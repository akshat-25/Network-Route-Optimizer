from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EdgeDB, NodeDB
from app.schemas import EdgeCreate, EdgeResponse

router = APIRouter(prefix="/edges", tags=["Edges"])


@router.post("", response_model=EdgeResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("", response_model=list[EdgeResponse])
def list_edges(db: Session = Depends(get_db)):
    return db.query(EdgeDB).all()


@router.delete("/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_edge(edge_id: int, db: Session = Depends(get_db)):
    edge = db.query(EdgeDB).filter(EdgeDB.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    db.delete(edge)
    db.commit()
