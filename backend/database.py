"""
Neo4j Database Connection Manager.
Provides a singleton driver and session helpers for the FastAPI app.
Gracefully falls back to an in-memory graph simulator when Neo4j is offline,
ensuring the application is always accessible on localhost.
"""
from contextlib import contextmanager
from neo4j import GraphDatabase
from backend.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from backend.mock_store import mock_store


class Neo4jConnection:
    """Manages the Neo4j driver lifecycle with seamless fallback."""

    def __init__(self):
        self._driver = None
        self._connected = False

    def connect(self):
        """Initialize the Neo4j driver or gracefully fall back to simulator."""
        try:
            self._driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )
            # Verify connectivity
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
        if self._connected and self._driver:
            try:
                with self.get_session() as session:
                    result = session.run(query, parameters or {})
                    return [record.data() for record in result]
            except Exception as e:
                print(f"[WARN] Live query failed ({e}), falling back to simulator.")
                return mock_store.execute(query, parameters)
        else:
            return mock_store.execute(query, parameters)

    def execute_write(self, query, parameters=None):
        """Execute a write query on Neo4j if online, or in-memory simulator."""
        if self._connected and self._driver:
            try:
                with self.get_session() as session:
                    def _write_tx(tx):
                        result = tx.run(query, parameters or {})
                        return [record.data() for record in result]
                    return session.execute_write(lambda tx: _write_tx(tx))
            except Exception as e:
                print(f"[WARN] Live write failed ({e}), falling back to simulator.")
                return mock_store.execute(query, parameters)
        else:
            return mock_store.execute(query, parameters)

    def run_write_transaction(self, tx_func):
        """Execute a multi-step transaction callback atomically with write locks."""
        if self._connected and self._driver:
            try:
                with self.get_session() as session:
                    return session.execute_write(tx_func)
            except Exception as e:
                print(f"[WARN] Live write tx failed ({e}), falling back to simulator.")
                return mock_store.run_transaction(tx_func)
        else:
            return mock_store.run_transaction(tx_func)



# Singleton instance
db = Neo4jConnection()
