import heapq
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import EdgeDB


def build_adjacency_list(db: Session) -> dict[str, list[tuple[str, float]]]:
    """Build an adjacency list from all edges in the database."""
    adj: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for edge in db.query(EdgeDB).all():
        adj[edge.source].append((edge.destination, edge.latency))
        adj[edge.destination].append((edge.source, edge.latency))
    return adj


def dijkstra(
    adj: dict[str, list[tuple[str, float]]],
    source: str,
    destination: str,
) -> tuple[float, list[str]] | None:
    """
    Return (total_latency, path) for the shortest path, or None if unreachable.
    Uses Dijkstra's algorithm with a min-heap.
    """
    dist: dict[str, float] = {source: 0.0}
    prev: dict[str, str | None] = {source: None}
    heap: list[tuple[float, str]] = [(0.0, source)]

    while heap:
        cost, node = heapq.heappop(heap)
        if node == destination:
            path: list[str] = []
            cur: str | None = destination
            while cur is not None:
                path.append(cur)
                cur = prev[cur]
            path.reverse()
            return round(cost, 10), path

        if cost > dist.get(node, float("inf")):
            continue

        for neighbor, latency in adj.get(node, []):
            new_cost = cost + latency
            if new_cost < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_cost
                prev[neighbor] = node
                heapq.heappush(heap, (new_cost, neighbor))

    return None
