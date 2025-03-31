import asyncio
import httpx
from typing import Optional

# Assuming these come from your project.
from app.exceptions import ToolError
from app.tool.base import BaseTool, CLIResult

_RAG_DESCRIPTION = """Perform Retrieval Augmented Generation (RAG) operations.
You should use this tool when the encounter large file.
Functions:
1. list_resources: Returns a list of available resource identifiers.
2. search: Uses a resource identity and query string to search for relevant data.
"""


class RAG(BaseTool):
    name: str = "rag"
    description: str = _RAG_DESCRIPTION
    # Define a simple JSON schema for the tool's parameters if needed.
    parameters: dict = {
        "type": "object",
        "properties": {
            "list_resources": {
                "type": "boolean",
                "description": "Set to true to list available resource identifiers.",
            },
            "identity": {
                "type": "string",
                "description": "The resource identity to search.",
            },
            "query": {
                "type": "string",
                "description": "The query string to search within the resource.",
            },
        },
        "oneOf": [
            {"required": ["list_resources"]},
            {"required": ["identity", "query"]},
        ],
    }

    # Base URL for the local FastAPI backend.
    BASE_URL: str = "http://140.113.24.140:8112"

    async def list_resources(self) -> CLIResult:
        """
        Call the FastAPI endpoint to list resource identifiers.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.BASE_URL}/resources")
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise ToolError(f"Error listing resources: {exc}") from exc
            resources = response.json()
        return CLIResult(output=resources)

    async def search(self, identity: str, query: str) -> CLIResult:
        """
        Call the FastAPI endpoint to search a resource.
        """
        params = {"identity": identity, "query": query}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.BASE_URL}/search", params=params)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise ToolError(f"Error searching resource: {exc}") from exc
            result = response.json()
        return CLIResult(output=result)

    async def execute(
        self,
        list_resources: Optional[bool] = None,
        identity: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs,
    ) -> CLIResult:
        """
        Execute the RAG tool.
        - If 'list_resources' is True, list all resources.
        - Otherwise, perform a search using 'identity' and 'query'.
        """
        if list_resources:
            return await self.list_resources()
        elif identity is not None and query is not None:
            return await self.search(identity, query)
        else:
            raise ToolError(
                "Invalid parameters. Provide either list_resources=True or both identity and query."
            )


# Example usage:
if __name__ == "__main__":
    rag_tool = RAG()
    # Example: list resources
    result = asyncio.run(rag_tool.execute(list_resources=True))
    print("Resources:", result.output)

    # Example: search within a resource.
    search_result = asyncio.run(rag_tool.execute(identity="resource1", query="cat"))
    print("Search Results:", search_result.output)
