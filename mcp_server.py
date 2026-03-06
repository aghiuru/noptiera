from dotenv import load_dotenv
load_dotenv()

from fastmcp import FastMCP
from pipeline.ingest import run_ingest
from pipeline.search import run_search

mcp = FastMCP("noptiera")

@mcp.tool()
def ingest(url: str, force: bool = False) -> str:
    """Download, parse, tag and index an article from a URL."""
    result = run_ingest(url, force=force)
    if result["skipped"]:
        return f"Already indexed: {result['title']}"
    tags = ", ".join(result["tags"])
    summary = result.get("summary", "")
    return f"Ingested: {result['title']}\n\nSummary: {summary}\n\nTags: {tags}"

@mcp.tool()
def search(query: str, top_k: int = 5) -> str:
    """Search indexed articles by topic or question."""
    results = run_search(query, top_k=top_k)
    if not results:
        return "No results found."
    lines = []
    for i, r in enumerate(results, 1):
        m = r["metadata"]
        lines.append(f"{i}. {m.get('title')} — {m.get('url')}")
    return "\n".join(lines)

if __name__ == "__main__":
    mcp.run()  # stdio transport
