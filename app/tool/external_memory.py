import uuid
import aiosqlite
from typing import Literal, Optional

from app.tool.base import BaseTool

DB_PATH = "/home/shaosen/LLM/OpenManus/db/memory_store.db"


class ExternalMemory(BaseTool):
    name: str = "external_memory"
    description: str = """Store or retrieve long content using a memory_id.

Actions:
- 'store': Save long content and return a memory_id.
- 'retrieve': Fetch previously stored content using a memory_id.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["store", "retrieve"],
                "description": "The action to perform: store or retrieve memory.",
            },
            "content": {
                "type": "string",
                "description": "Content to store. Required for 'store' action.",
            },
            "memory_id": {
                "type": "string",
                "description": "Memory ID to retrieve. Required for 'retrieve' action.",
            },
        },
        "required": ["action"],
        "dependencies": {
            "store": ["content"],
            "retrieve": ["memory_id"],
        },
    }

    async def execute(
        self,
        action: Literal["store", "retrieve"],
        content: Optional[str] = None,
        memory_id: Optional[str] = None,
    ) -> str:
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    """CREATE TABLE IF NOT EXISTS memory (
                        id TEXT PRIMARY KEY,
                        content TEXT
                    )"""
                )

                if action == "store":
                    memory_id = str(uuid.uuid4())
                    await db.execute(
                        "INSERT INTO memory (id, content) VALUES (?, ?)",
                        (memory_id, content),
                    )
                    await db.commit()
                    return f"🔐 Content stored. memory_id: {memory_id}"

                elif action == "retrieve":
                    async with db.execute(
                        "SELECT content FROM memory WHERE id = ?", (memory_id,)
                    ) as cursor:
                        row = await cursor.fetchone()
                        if row is None:
                            return f"❌ No content found for memory_id: {memory_id}"
                        return f"🧠 Retrieved content for {memory_id}:\n{row[0]}"

                else:
                    return "❓ Invalid action."

        except Exception as e:
            return f"⚠️ ExternalMemory error: {str(e)}"
