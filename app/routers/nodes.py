from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EdgeDB, NodeDB
from app.schemas import NodeCreate, NodeResponse

router = APIRouter(prefix="/nodes", tags=["Nodes"])


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("", response_model=list[NodeResponse])
def list_nodes(db: Session = Depends(get_db)):
    return db.query(NodeDB).all()


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(NodeDB).filter(NodeDB.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    db.query(EdgeDB).filter(
        (EdgeDB.source == node.name) | (EdgeDB.destination == node.name)
    ).delete(synchronize_session="fetch")

    db.delete(node)
    db.commit()
