import asyncio
import httpx
import json
from typing import Optional
from app.logger import logger
from app.exceptions import ToolError
from app.tool.base import BaseTool, CLIResult

_RAG_DESCRIPTION = """Perform Retrieval Augmented Generation (RAG) operations.
You should use this tool when encountering large files.
Function:
Search: Uses a resource identity (mapped to paper_id) and a query string (mapped to question) to search via the QA endpoint.
"""


class RAG(BaseTool):
    name: str = "rag"
    description: str = _RAG_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "identity": {
                "type": "string",
                "description": "The resource identity to search (will be sent as paper_id).",
            },
            "query": {
                "type": "string",
                "description": "The query string to search within the resource (will be sent as question).",
            },
        },
        "required": ["identity", "query"],
    }

    BASE_URL: str = "http://140.113.24.140:8112"

    async def search(self, identity: str, query: str) -> CLIResult:
        """
        Call the FastAPI /qa endpoint with a POST request.
        Maps 'identity' to 'paper_id' and 'query' to 'question'.
        """
        payload = {"paper_id": identity, "question": query}
        logger.info(f"Sending payload: {payload} to {self.BASE_URL}/qa")
        timeout = httpx.Timeout(
            60.0
        )  # sets a 60-second timeout for connect, read, etc.
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(f"{self.BASE_URL}/qa", json=payload)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                status = exc.response.status_code if exc.response else "No status"
                content = exc.response.text if exc.response else "No content"
                logger.error(f"HTTP error occurred (status {status}): {content}")
                raise ToolError(f"Error performing QA search: HTTP {status}") from exc
            result = response.json()
        # Convert the result dictionary to a JSON string to avoid __str__ errors.
        result_str = json.dumps(result)
        return CLIResult(output=result_str)

    async def execute(
        self,
        identity: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs,
    ) -> CLIResult:
        """
        Execute the RAG tool.
        Perform a search using 'identity' (as paper_id) and 'query' (as question).
        """
        logger.info(f"Executing RAG tool with identity: {identity}, query: {query}")
        if identity is not None and query is not None:
            return await self.search(identity, query)
        else:
            error_msg = "Invalid parameters. Provide both identity and query."
            logger.error(error_msg)
            raise ToolError(error_msg)


# Example usage:
if __name__ == "__main__":
    rag_tool = RAG()
    try:
        search_result = asyncio.run(
            rag_tool.execute(
                identity="1503.03585v8",
                query="What is the core method_v2 of this paper?",
            )
        )
        logger.info(f"Search Results: {search_result.output}")
        print("Search Results:", search_result.output)
    except Exception as e:
        logger.error(f"An error occurred during execution: {e}")
