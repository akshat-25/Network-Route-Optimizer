from datetime import datetime

from pydantic import BaseModel


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
