"""
Pytest configuration and shared fixtures.
Uses a separate test approach: tests that require Neo4j are marked
and will be skipped if the database is not available.
"""
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "requires_neo4j: test requires a running Neo4j instance")


@pytest.fixture(scope="session")
def neo4j_available():
    """Check if Neo4j is available for testing."""
    try:
        from backend.config import get_driver
        driver = get_driver()
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def neo4j_driver():
    """Provide a Neo4j driver for tests. Skip if unavailable."""
    try:
        from backend.config import get_driver
        driver = get_driver()
        driver.verify_connectivity()
        yield driver
        driver.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {e}")


@pytest.fixture(scope="session")
def test_client():
    """Provide a FastAPI test client."""
    from fastapi.testclient import TestClient
    try:
        from backend.main import app
        from backend.database import db
        db.connect()
        client = TestClient(app)
        yield client
        db.close()
    except Exception as e:
        pytest.skip(f"Cannot create test client: {e}")
