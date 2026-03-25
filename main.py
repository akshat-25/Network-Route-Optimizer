from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

from graph import build_adjacency_list, dijkstra
from models import (
    EdgeCreate,
    EdgeDB,
    EdgeResponse,
    NodeCreate,
    NodeDB,
    NodeResponse,
    RouteHistoryDB,
    RouteHistoryResponse,
    SessionLocal,
    ShortestRouteRequest,
    ShortestRouteResponse,
)

app = FastAPI(title="Network Route Optimizer")

@app.get("/")
def root():
    return {
        "service": "Network Route Optimizer",
        "docs": "/docs",
        "endpoints": ["/nodes" ,"/edges", "/routes/shortest", "/routes/history"]
    }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Nodes

@app.post("/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
def add_node(body: NodeCreate, db: Session = Depends(get_db)):
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=400, detail="Node name is required")

    if db.query(NodeDB).filter(NodeDB.name == body.name).first():
        raise HTTPException(status_code=400, detail=f"Node '{body.name}' already exists")

    node = NodeDB(name=body.name.strip())
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


@app.get("/nodes", response_model=list[NodeResponse])
def list_nodes(db: Session = Depends(get_db)):
    return db.query(NodeDB).all()


@app.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(NodeDB).filter(NodeDB.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    db.query(EdgeDB).filter(
        (EdgeDB.source == node.name) | (EdgeDB.destination == node.name)
    ).delete(synchronize_session="fetch")

    db.delete(node)
    db.commit()


# Edges

@app.post("/edges", response_model=EdgeResponse, status_code=status.HTTP_201_CREATED)
def add_edge(body: EdgeCreate, db: Session = Depends(get_db)):
    if not body.source or not body.source.strip():
        raise HTTPException(status_code=400, detail="Source node is required")
    if not body.destination or not body.destination.strip():
        raise HTTPException(status_code=400, detail="Destination node is required")
    if body.latency <= 0:
        raise HTTPException(status_code=400, detail="Latency must be greater than 0")

    src = body.source.strip()
    dst = body.destination.strip()

    if not db.query(NodeDB).filter(NodeDB.name == src).first():
        raise HTTPException(status_code=400, detail=f"Source node '{src}' not found")
    if not db.query(NodeDB).filter(NodeDB.name == dst).first():
        raise HTTPException(status_code=400, detail=f"Destination node '{dst}' not found")

    existing = (
        db.query(EdgeDB)
        .filter(EdgeDB.source == src, EdgeDB.destination == dst)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Edge from '{src}' to '{dst}' already exists",
        )

    edge = EdgeDB(source=src, destination=dst, latency=body.latency)
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return edge


@app.get("/edges", response_model=list[EdgeResponse])
def list_edges(db: Session = Depends(get_db)):
    return db.query(EdgeDB).all()


@app.delete("/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_edge(edge_id: int, db: Session = Depends(get_db)):
    edge = db.query(EdgeDB).filter(EdgeDB.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    db.delete(edge)
    db.commit()


# Routes

@app.post("/routes/shortest", response_model=ShortestRouteResponse)
def shortest_route(body: ShortestRouteRequest, db: Session = Depends(get_db)):
    src = body.source.strip()
    dst = body.destination.strip()

    if not src or not dst:
        raise HTTPException(status_code=400, detail="Source and destination are required")

    if not db.query(NodeDB).filter(NodeDB.name == src).first():
        raise HTTPException(status_code=400, detail=f"Node '{src}' does not exist")
    if not db.query(NodeDB).filter(NodeDB.name == dst).first():
        raise HTTPException(status_code=400, detail=f"Node '{dst}' does not exist")

    adj = build_adjacency_list(db)
    result = dijkstra(adj, src, dst)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No path exists between {src} and {dst}",
        )

    total_latency, path = result

    history = RouteHistoryDB(
        source=src,
        destination=dst,
        total_latency=total_latency,
        path=",".join(path),
        created_at=datetime.now(timezone.utc),
    )
    db.add(history)
    db.commit()

    return ShortestRouteResponse(total_latency=total_latency, path=path)


@app.get("/routes/history", response_model=list[RouteHistoryResponse])
def route_history(
    source: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(RouteHistoryDB)

    if source:
        q = q.filter(RouteHistoryDB.source == source)
    if destination:
        q = q.filter(RouteHistoryDB.destination == destination)
    if date_from:
        q = q.filter(RouteHistoryDB.created_at >= date_from)
    if date_to:
        q = q.filter(RouteHistoryDB.created_at <= date_to)

    q = q.order_by(RouteHistoryDB.created_at.desc())

    if limit:
        q = q.limit(limit)

    rows = q.all()

    results = []
    for row in rows:
        results.append(
            RouteHistoryResponse(
                id=row.id,
                source=row.source,
                destination=row.destination,
                total_latency=row.total_latency,
                path=row.path.split(","),
                created_at=row.created_at,
            )
        )
    return results