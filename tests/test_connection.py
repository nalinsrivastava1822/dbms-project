"""
Test database connectivity.
"""
import pytest


@pytest.mark.requires_neo4j
class TestConnection:
    def test_driver_connects(self, neo4j_driver):
        """Verify Neo4j driver can connect."""
        assert neo4j_driver is not None

    def test_basic_query(self, neo4j_driver):
        """Verify basic Cypher query execution."""
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1 AS value")
            record = result.single()
            assert record["value"] == 1

    def test_health_endpoint(self, test_client):
        """Verify /api/health returns connected status."""
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
