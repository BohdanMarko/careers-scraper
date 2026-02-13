"""Simple database initialization script."""

import sys
from pathlib import Path

# Add src to path so we can import careers_scraper
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from careers_scraper.db import Base, engine

def init_database():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    print("\nTables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

if __name__ == "__main__":
    init_database()
