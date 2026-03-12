"""Async MongoDB connection via Motor."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Establish MongoDB connection."""
    global _client, _database
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _database = _client[settings.DATABASE_NAME]
    # Verify connection
    await _client.admin.command("ping")
    print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_db() -> None:
    """Close MongoDB connection."""
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None
        print("🔌 MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _database


def get_questions_collection():
    """Get the questions collection."""
    return get_database()["questions"]


def get_sessions_collection():
    """Get the user_sessions collection."""
    return get_database()["user_sessions"]
