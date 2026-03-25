# Network Route Optimizer
 
A FastAPI application that models a network of servers as a weighted graph and computes the shortest (lowest-latency) route between any two nodes using Dijkstra's algorithm. All queries are logged and can be retrieved through a history endpoint.

## Requirements

- **Python** 3.10+
- pip

## Project Structure

```
python_exercise/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app creation, router wiring, DB init
│   ├── database.py          # SQLAlchemy engine, session factory, Base class
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── graph.py             # Dijkstra's shortest-path algorithm
│   └── routers/
│       ├── __init__.py
│       ├── nodes.py         # /nodes endpoints
│       ├── edges.py         # /edges endpoints
│       └── routes.py        # /routes/shortest & /routes/history endpoints
├── requirements.txt
└── README.md
```

| Module | Responsibility |
|--------|----------------|
| `app/main.py` | Creates the FastAPI instance, includes all routers, initializes the database tables on startup. |
| `app/database.py` | Configures the SQLAlchemy engine (SQLite), session factory, declarative `Base`, and the `get_db` dependency. |
| `app/models.py` | Defines ORM models: `NodeDB`, `EdgeDB`, `RouteHistoryDB`. |
| `app/schemas.py` | Defines Pydantic models for request validation and response serialization. |
| `app/graph.py` | Builds an adjacency list from edges and runs Dijkstra's algorithm. |
| `app/routers/nodes.py` | Handles `POST /nodes`, `GET /nodes`, `DELETE /nodes/{id}`. |
| `app/routers/edges.py` | Handles `POST /edges`, `GET /edges`, `DELETE /edges/{id}`. |
| `app/routers/routes.py` | Handles `POST /routes/shortest`, `GET /routes/history`. |

## Setup & Run

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Start the server** (run from the `Network Route Optimizer/` directory)

```bash
uvicorn app.main:app --reload
```

3. **Open in browser**

Navigate to http://127.0.0.1:8000 — it automatically redirects to the Swagger UI at `/docs`.

> The SQLite database file (`network.db`) is created automatically on first startup in the working directory.

## API Endpoints

### Nodes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/nodes` | Create a new node |
| `GET` | `/nodes` | List all nodes |
| `DELETE` | `/nodes/{id}` | Delete a node and its connected edges |

#### POST /nodes

```json
// Request
{ "name": "ServerA" }

// Response (201)
{ "id": 1, "name": "ServerA" }
```

**Errors:** `400` — name missing or duplicate.

---

### Edges

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/edges` | Create a new edge between two nodes |
| `GET` | `/edges` | List all edges |
| `DELETE` | `/edges/{id}` | Delete an edge |

#### POST /edges

```json
// Request
{ "source": "ServerA", "destination": "ServerB", "latency": 12.5 }

// Response (201)
{ "id": 1, "source": "ServerA", "destination": "ServerB", "latency": 12.5 }
```

**Errors:** `400` — source/destination missing, latency <= 0, duplicate edge, or nodes not found.

---

### Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/routes/shortest` | Compute shortest path between two nodes |
| `GET` | `/routes/history` | Retrieve past route queries |

#### POST /routes/shortest

```json
// Request
{ "source": "ServerA", "destination": "ServerD" }

// Response (200)
{ "total_latency": 23.4, "path": ["ServerA", "ServerB", "ServerD"] }
```

**Errors:** `400` — invalid or non-existent nodes. `404` — no path exists.

#### GET /routes/history

Optional query parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | string | Filter by source node |
| `destination` | string | Filter by destination node |
| `limit` | int | Max number of records to return |
| `date_from` | datetime | Filter results from this timestamp |
| `date_to` | datetime | Filter results up to this timestamp |

```json
// Response (200)
[
  {
    "id": 1,
    "source": "ServerA",
    "destination": "ServerD",
    "total_latency": 23.4,
    "path": ["ServerA", "ServerB", "ServerD"],
    "created_at": "2026-02-20T14:32:00Z"
  }
]
```

## Algorithm

The shortest path is computed using **Dijkstra's algorithm** with a min-heap priority queue. The graph is treated as **bidirectional** — an edge between A and B allows traversal in both directions with the same latency.

## Database

SQLite is used via SQLAlchemy ORM. The database file `network.db` is auto-created on startup. Three tables are maintained:

- **nodes** — stores network node names (unique)
- **edges** — stores weighted connections between nodes (unique per source-destination pair)
- **route_history** — logs every shortest-path query with its result and timestamp
