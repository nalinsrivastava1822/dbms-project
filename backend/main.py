"""
FastAPI Main Application — Hotel Management System with Neo4j.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from backend.database import db
from backend.routers import dashboard, hotels, rooms, guests, reservations, staff, recommendations, graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Neo4j connection lifecycle."""
    try:
        db.connect()
        yield
    finally:
        db.close()


app = FastAPI(
    title="Hotel Management System",
    description="A graph-based Hotel Management System using Neo4j — DBMS DA3 Project",
    version="1.0.0",
    lifespan=lifespan,
)

# Register API routers
app.include_router(dashboard.router)
app.include_router(hotels.router)
app.include_router(rooms.router)
app.include_router(guests.router)
app.include_router(reservations.router)
app.include_router(staff.router)
app.include_router(recommendations.router)
app.include_router(graph.router)

# Serve static frontend files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/api/health")
def health_check():
    """Health check endpoint to verify API and DB connectivity."""
    try:
        result = db.execute_read("RETURN 1 AS ok")
        return {
            "status": "healthy",
            "database": "connected",
            "mode": "live_neo4j" if db.is_connected else "in_memory_simulator",
        }
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
