"""
Database Reset Script — Deletes ALL data from the Neo4j database.
Requires explicit user confirmation before proceeding.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.config import get_driver


def reset_database(driver):
    """Delete all nodes and relationships."""
    with driver.session() as session:
        # Count existing data
        result = session.run("MATCH (n) RETURN COUNT(n) AS count")
        count = result.single()["count"]

        if count == 0:
            print("Database is already empty.")
            return

        print(f"\nFound {count} nodes in the database.")

        # Require explicit confirmation
        confirm = input(
            "\n⚠️  WARNING: This will DELETE ALL DATA in the database.\n"
            "Type 'RESET' (all caps) to confirm: "
        )

        if confirm != "RESET":
            print("Reset cancelled.")
            return

        session.run("MATCH (n) DETACH DELETE n")
        print("\n[OK] All nodes and relationships deleted.")

        # Verify
        result = session.run("MATCH (n) RETURN COUNT(n) AS count")
        remaining = result.single()["count"]
        print(f"Remaining nodes: {remaining}")


if __name__ == "__main__":
    print("=" * 50)
    print("Hotel Management System — Database Reset")
    print("=" * 50)

    driver = get_driver()
    try:
        driver.verify_connectivity()
        print("[OK] Connected to Neo4j.")
        reset_database(driver)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    finally:
        driver.close()
