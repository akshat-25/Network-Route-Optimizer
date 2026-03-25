from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.graph import build_adjacency_list, dijkstra
from app.models import NodeDB, RouteHistoryDB
from app.schemas import RouteHistoryResponse, ShortestRouteRequest, ShortestRouteResponse

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.post("/shortest", response_model=ShortestRouteResponse)
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


@router.get("/history", response_model=list[RouteHistoryResponse])
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

    return [
        RouteHistoryResponse(
            id=row.id,
            source=row.source,
            destination=row.destination,
            total_latency=row.total_latency,
            path=row.path.split(","),
            created_at=row.created_at,
        )
        for row in rows
    ]
