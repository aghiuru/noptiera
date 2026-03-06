import asyncio
import json
import logging

from fastmcp import Client
from mcp_server import mcp
from pipeline import llm

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a personal knowledge assistant. "
    "When the user wants to save or index an article, call the `ingest` tool. "
    "When the user wants to find or search articles, call the `search` tool. "
    "Always use a tool — do not answer from memory."
)


async def _run_agent_async(user_message: str) -> str:
    async with Client(mcp) as client:
        # Fetch tool schemas live from the MCP server
        mcp_tools = await client.list_tools()
        tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema,
                },
            }
            for t in mcp_tools
        ]

        # Ask LLM to pick a tool
        lm_client = llm._get_client()
        response = lm_client.chat.completions.create(
            model=llm.DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            tools=tools,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        if not msg.tool_calls:
            return msg.content or "I didn't understand that. Try: 'ingest <url>' or 'search <topic>'."

        tool_call = msg.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        log.info("MCP tool call: %s(%s)", name, args)

        result = await client.call_tool(name, args)
        # result is a CallToolResult; .content is a list of content blocks
        return "\n".join(r.text for r in result.content if hasattr(r, "text"))


def run_agent(user_message: str) -> str:
    return asyncio.run(_run_agent_async(user_message))
