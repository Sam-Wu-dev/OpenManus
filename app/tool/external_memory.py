import uuid
import aiosqlite
from typing import Literal, Optional, Union, List

from app.tool.base import BaseTool

DB_PATH = "/home/shaosen/LLM/OpenManus/db/memory_store.db"


class ExternalMemory(BaseTool):
    name: str = "external_memory"
    description: str = """Store or retrieve long content using one or more memory_id values.

Actions:
- 'store': Save long content and return a memory_id.
- 'retrieve': Fetch previously stored content using one or more memory_id values.
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
                "oneOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string"}},
                ],
                "description": "Memory ID or list of memory IDs to retrieve. Required for 'retrieve' action.",
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
        memory_id: Optional[Union[str, List[str]]] = None,
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
                    new_id = str(uuid.uuid4())
                    await db.execute(
                        "INSERT INTO memory (id, content) VALUES (?, ?)",
                        (new_id, content),
                    )
                    await db.commit()
                    return f"🔐 Content stored. memory_id: {new_id}"

                elif action == "retrieve":
                    # Normalize to list
                    if isinstance(memory_id, str):
                        memory_id_list = [memory_id]
                    elif isinstance(memory_id, list):
                        memory_id_list = memory_id
                    else:
                        return "❗ Invalid memory_id format."

                    placeholders = ",".join("?" for _ in memory_id_list)
                    async with db.execute(
                        f"SELECT id, content FROM memory WHERE id IN ({placeholders})",
                        memory_id_list,
                    ) as cursor:
                        rows = await cursor.fetchall()

                    if not rows:
                        return "❌ No content found for the provided memory_id(s)."

                    results = "\n\n".join(
                        f"🧠 {mid}:\n{content}" for mid, content in rows
                    )
                    return results

                else:
                    return "❓ Invalid action."

        except Exception as e:
            return f"⚠️ ExternalMemory error: {str(e)}"
