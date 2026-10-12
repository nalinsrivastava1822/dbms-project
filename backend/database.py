"""
Neo4j Database Connection Manager.
Provides a singleton driver and session helpers for the FastAPI app.
Gracefully falls back to an in-memory graph simulator when Neo4j is offline,
ensuring the application is always accessible on localhost.
Instrumented with QueryTracer to power the live Backend Query Inspector terminal.
"""
from contextlib import contextmanager
import time
from neo4j import GraphDatabase

from backend.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from backend.mock_store import mock_store
from backend.query_tracer import QueryTracer


class TracedTx:
    """Wrapper around a Neo4j or Mock transaction to trace individual statement executions."""

    def __init__(self, raw_tx, db_mode: str):
        self._raw_tx = raw_tx
        self._db_mode = db_mode

    def run(self, query, parameters=None):
        t0 = time.perf_counter()
        params = parameters or {}
        try:
            result = self._raw_tx.run(query, params)
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            QueryTracer.record_execution(
                query=query,
                parameters=params,
                database_mode=self._db_mode,
                duration_ms=duration_ms,
                status="SUCCESS",
                records_count=1,
            )
            return result
        except Exception as e:
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            QueryTracer.record_execution(
                query=query,
                parameters=params,
                database_mode=self._db_mode,
                duration_ms=duration_ms,
                status="FAILURE",
                error=str(e),
            )
            raise

    def __getattr__(self, name):
        return getattr(self._raw_tx, name)


class Neo4jConnection:
    """Manages the Neo4j driver lifecycle with seamless fallback and live tracing."""

    def __init__(self):
        self._driver = None
        self._connected = False

    def connect(self):
        """Initialize the Neo4j driver or gracefully fall back to simulator."""
        try:
            self._driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )
            self._driver.verify_connectivity()
            self._connected = True
            print(f"[OK] Connected to live Neo4j database at {NEO4J_URI}")
        except Exception as e:
            self._connected = False
            self._driver = None
            print(
                f"[INFO] Neo4j instance at {NEO4J_URI} is currently offline ({e}).\n"
                f"       Active Mode: In-Memory Graph Simulator (All features & queries operational)."
            )

    def close(self):
        """Close the Neo4j driver."""
        if self._driver:
            try:
                self._driver.close()
                print("Neo4j connection closed.")
            except Exception:
                pass
            finally:
                self._driver = None
                self._connected = False

    @property
    def driver(self):
        return self._driver

    @property
    def is_connected(self) -> bool:
        return self._connected

    @contextmanager
    def get_session(self):
        """Provide a Neo4j session as a context manager."""
        if not self._connected or not self._driver:
            raise RuntimeError("Neo4j driver is not connected")
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def execute_read(self, query, parameters=None):
        """Execute a read query on Neo4j if online, or in-memory simulator."""
        params = parameters or {}
        t0 = time.perf_counter()

        if self._connected and self._driver:
            try:
                with self.get_session() as session:
                    result = session.run(query, params)
                    data = [record.data() for record in result]
                    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                    QueryTracer.record_execution(
                        query=query,
                        parameters=params,
                        database_mode="Neo4j (Live)",
                        duration_ms=duration_ms,
                        status="SUCCESS",
                        records_count=len(data),
                    )
                    return data
            except Exception as e:
                duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                QueryTracer.record_execution(
                    query=query,
                    parameters=params,
                    database_mode="Neo4j (Live)",
                    duration_ms=duration_ms,
                    status="FAILURE",
                    error=str(e),
                )
                print(f"[WARN] Live query failed ({e}), falling back to simulator.")

        # Simulator fallback
        t0 = time.perf_counter()
        try:
            data = mock_store.execute(query, params)
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            QueryTracer.record_execution(
                query=query,
                parameters=params,
                database_mode="Neo4j (In-Memory Simulator)",
                duration_ms=duration_ms,
                status="SUCCESS",
                records_count=len(data) if isinstance(data, list) else 1,
            )
            return data
        except Exception as e:
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            QueryTracer.record_execution(
                query=query,
                parameters=params,
                database_mode="Neo4j (In-Memory Simulator)",
                duration_ms=duration_ms,
                status="FAILURE",
                error=str(e),
            )
            raise

    def execute_write(self, query, parameters=None):
        """Execute a write query on Neo4j if online, or in-memory simulator."""
        params = parameters or {}
        t0 = time.perf_counter()

        if self._connected and self._driver:
            try:
                with self.get_session() as session:
                    def _write_tx(tx):
                        result = tx.run(query, params)
                        return [record.data() for record in result]
                    data = session.execute_write(_write_tx)
                    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                    QueryTracer.record_execution(
                        query=query,
                        parameters=params,
                        database_mode="Neo4j (Live)",
                        duration_ms=duration_ms,
                        status="SUCCESS",
                        records_count=len(data) if isinstance(data, list) else 1,
                    )
                    return data
            except Exception as e:
                duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                QueryTracer.record_execution(
                    query=query,
                    parameters=params,
                    database_mode="Neo4j (Live)",
                    duration_ms=duration_ms,
                    status="FAILURE",
                    error=str(e),
                )
                print(f"[WARN] Live write failed ({e}), falling back to simulator.")

        # Simulator fallback
        t0 = time.perf_counter()
        try:
            data = mock_store.execute(query, params)
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            QueryTracer.record_execution(
                query=query,
                parameters=params,
                database_mode="Neo4j (In-Memory Simulator)",
                duration_ms=duration_ms,
                status="SUCCESS",
                records_count=len(data) if isinstance(data, list) else 1,
            )
            return data
        except Exception as e:
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            QueryTracer.record_execution(
                query=query,
                parameters=params,
                database_mode="Neo4j (In-Memory Simulator)",
                duration_ms=duration_ms,
                status="FAILURE",
                error=str(e),
            )
            raise

    def run_write_transaction(self, tx_func):
        """Execute a multi-step transaction callback atomically with write locks."""
        if self._connected and self._driver:
            try:
                with self.get_session() as session:
                    return session.execute_write(lambda tx: tx_func(TracedTx(tx, "Neo4j (Live)")))
            except Exception as e:
                print(f"[WARN] Live write tx failed ({e}), falling back to simulator.")

        return mock_store.run_transaction(lambda tx: tx_func(TracedTx(tx, "Neo4j (In-Memory Simulator)")))


# Singleton instance
db = Neo4jConnection()
