"""
FastAPI Main Application — Hotel Management System with Neo4j.
Includes real-time QueryTracer middleware and inspector endpoints.
"""
from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from backend.database import db
from backend.query_tracer import (
    QueryTracer,
    request_trace_var,
    request_endpoint_var,
    request_action_var,
    infer_action_name,
)
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

# Enable CORS for localhost access across ports and local hosts, exposing query inspector headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Backend-Trace", "X-Backend-Queries-Count"],
)


@app.middleware("http")
async def query_trace_middleware(request: Request, call_next):
    """Capture actual Cypher executions per HTTP request and attach trace header."""
    trace_list = []
    token_trace = request_trace_var.set(trace_list)
    token_endpoint = request_endpoint_var.set(f"{request.method} {request.url.path}")
    token_action = request_action_var.set(infer_action_name(request.method, request.url.path))

    try:
        response = await call_next(request)
    finally:
        request_trace_var.reset(token_trace)
        request_endpoint_var.reset(token_endpoint)
        request_action_var.reset(token_action)

    if trace_list:
        try:
            response.headers["X-Backend-Trace"] = QueryTracer.encode_traces(trace_list)
            response.headers["X-Backend-Queries-Count"] = str(len(trace_list))
        except Exception as e:
            print(f"[WARN] Failed to encode trace header: {e}")

    return response


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# Backend Query Inspector endpoints
@app.get("/api/query-inspector/history", tags=["Query Inspector"])
def get_query_inspector_history(limit: int = 100):
    """Retrieve recent Cypher query execution traces."""
    return QueryTracer.get_history(limit=limit)


@app.post("/api/query-inspector/clear", tags=["Query Inspector"])
def clear_query_inspector_history():
    """Clear recorded query execution traces."""
    QueryTracer.clear_history()
    return {"status": "cleared", "message": "Query history cleared"}


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

    @app.api_route("/", methods=["GET", "HEAD"])
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.api_route("/login", methods=["GET", "HEAD"])
    async def serve_login():
        """Serve the login page."""
        return FileResponse(os.path.join(frontend_dir, "login.html"))


@app.api_route("/api/health", methods=["GET", "HEAD"])
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
