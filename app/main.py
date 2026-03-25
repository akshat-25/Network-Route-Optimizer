from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.database import Base, engine
from app.routers import edges, nodes, routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Network Route Optimizer")

app.include_router(nodes.router)
app.include_router(edges.router)
app.include_router(routes.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
