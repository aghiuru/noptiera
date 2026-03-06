import logging
import click
from dotenv import load_dotenv
load_dotenv()
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler

console = Console()


def _setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_path=False)],
    )


@click.group()
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging.")
@click.pass_context
def cli(ctx, verbose: bool):
    """Noptiera - personal knowledge pipeline."""
    _setup_logging(verbose)


@cli.command()
@click.argument("url")
def fetch(url: str):
    """Download and extract article content, with detailed logging."""
    import logging
    from pipeline.parser import fetch_and_parse

    log = logging.getLogger(__name__)
    log.info("Fetching %s", url)
    try:
        data = fetch_and_parse(url)
    except Exception as e:
        log.error("Failed: %s", e)
        raise SystemExit(1)

    log.info("Title:  %s", data.get("title"))
    log.info("Author: %s", data.get("author"))
    log.info("Date:   %s", data.get("date"))
    log.info("URL:    %s", data.get("url"))
    text = data.get("text") or ""
    log.info("Length: %d chars, %d words", len(text), len(text.split()))
    console.print(Panel(
        text[:1000] + ("…" if len(text) > 1000 else ""),
        title="[green]Extracted text (preview)[/green]",
    ))


@cli.command()
@click.argument("url")
@click.option("--model", default=None, help="LM Studio model for tag generation")
@click.option("--embed-model", default=None, help="LM Studio model for embeddings")
@click.option("--force", is_flag=True, default=False, help="Re-index even if already indexed.")
def ingest(url: str, model: str, embed_model: str, force: bool):
    """Download, parse, tag and index an article from URL."""
    from pipeline.ingest import run_ingest

    console.print(f"[bold blue]Ingesting:[/bold blue] {url}")
    try:
        result = run_ingest(url, model=model, embed_model=embed_model, force=force)
        if result["skipped"]:
            console.print(f"[yellow]Skipped[/yellow] (already indexed): {result['slug']}")
        else:
            console.print(Panel(
                f"[bold]{result['title']}[/bold]\n\n"
                f"{result.get('summary', '')}\n\n"
                f"Tags: {', '.join(result['tags'])}\n"
                f"Saved: articles/{result['slug']}.md",
                title="[green]Ingested[/green]",
            ))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command()
@click.argument("query")
@click.option("--top-k", default=5, show_default=True, help="Number of results")
@click.option("--embed-model", default=None, help="Ollama model for embeddings")
def search(query: str, top_k: int, embed_model: str):
    """Semantic search over indexed articles."""
    from pipeline.search import run_search
    from rich.table import Table

    try:
        results = run_search(query, top_k=top_k, embed_model=embed_model)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(title=f"Search: {query}", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="bold")
    table.add_column("Tags")
    table.add_column("URL", style="dim")

    for i, r in enumerate(results, 1):
        meta = r["metadata"]
        table.add_row(
            str(i),
            meta.get("title", ""),
            meta.get("tags", ""),
            meta.get("url", ""),
        )

    console.print(table)


@cli.command("list")
def list_articles():
    """List all indexed articles."""
    from pipeline.store import get_collection
    from rich.table import Table
    import os

    db_path = os.path.join(os.path.dirname(__file__), ".index")
    collection = get_collection(db_path)
    results = collection.get(include=["metadatas"])

    if not results["ids"]:
        console.print("[yellow]No articles indexed yet.[/yellow]")
        return

    table = Table(title="Indexed Articles", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="bold")
    table.add_column("Date")
    table.add_column("Tags")

    for i, (doc_id, meta) in enumerate(zip(results["ids"], results["metadatas"]), 1):
        table.add_row(
            str(i),
            meta.get("title", doc_id),
            meta.get("date", ""),
            meta.get("tags", ""),
        )

    console.print(table)


if __name__ == "__main__":
    cli()
