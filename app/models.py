from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, UniqueConstraint

from app.database import Base


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
    path = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
