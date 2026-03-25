from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Float, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# SQLAlchemy setup

engine = create_engine("sqlite:///network.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


class NodeDB(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)


class EdgeDB(Base):
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    latency = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "destination", name="uq_edge_src_dst"),
    )


class RouteHistoryDB(Base):
    __tablename__ = "route_history"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    total_latency = Column(Float, nullable=False)
    path = Column(String, nullable=False)  # stored as comma-separated names
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(bind=engine)

# Pydantic schemas

class NodeCreate(BaseModel):
    name: str


class NodeResponse(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class EdgeCreate(BaseModel):
    source: str
    destination: str
    latency: float


class EdgeResponse(BaseModel):
    id: int
    source: str
    destination: str
    latency: float
    model_config = {"from_attributes": True}


class ShortestRouteRequest(BaseModel):
    source: str
    destination: str


class ShortestRouteResponse(BaseModel):
    total_latency: float
    path: list[str]


class RouteHistoryResponse(BaseModel):
    id: int
    source: str
    destination: str
    total_latency: float
    path: list[str]
    created_at: datetime
    model_config = {"from_attributes": True}
