import logging
import os
import frontmatter
from slugify import slugify
from pipeline import parser, llm, store

log = logging.getLogger(__name__)

ARTICLES_DIR = os.path.join(os.path.dirname(__file__), "..", "articles")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", ".index")


def run_ingest(url: str, model: str = None, embed_model: str = None, force: bool = False) -> dict:
    os.makedirs(ARTICLES_DIR, exist_ok=True)

    log.info("Fetching and parsing %s", url)
    data = parser.fetch_and_parse(url)
    title = data.get("title") or url
    text = data.get("text") or ""
    author = data.get("author") or ""
    date = str(data.get("date") or "")
    article_url = data.get("url") or url
    log.debug("Parsed: title=%r author=%r date=%r len=%d", title, author, date, len(text))

    slug = slugify(title)[:80] or slugify(url)[:80]
    log.debug("Slug: %s", slug)

    collection = store.get_collection(DB_PATH)
    existing = collection.get(ids=[slug])
    if existing["ids"]:
        if not force:
            log.info("Already indexed, skipping: %s", slug)
            return {"skipped": True, "slug": slug, "title": title, "tags": []}
        log.info("Force re-indexing: %s", slug)
        collection.delete(ids=[slug])

    log.info("Formatting as markdown")
    formatted_text = llm.format_as_markdown(title, text, model=model)

    log.info("Generating tags")
    tags = llm.generate_tags(title, formatted_text, model=model)

    log.info("Generating summary")
    summary = llm.generate_summary(title, formatted_text, model=model)

    md_path = os.path.join(ARTICLES_DIR, f"{slug}.md")
    log.info("Writing %s", md_path)
    body = f"{summary}\n\n---\n\n{formatted_text}"
    post = frontmatter.Post(body, url=article_url, title=title, date=date, author=author, tags=tags)
    with open(md_path, "wb") as f:
        frontmatter.dump(post, f)

    log.info("Embedding document")
    embedding = llm.embed(f"{title}\n{formatted_text}", model=embed_model)

    log.info("Storing in index")
    metadata = {
        "slug": slug,
        "url": article_url,
        "title": title,
        "date": date,
        "author": author,
        "tags": ", ".join(tags),
    }
    store.add_document(collection, slug, embedding, metadata)
    log.info("Done: %s", slug)

    return {"skipped": False, "slug": slug, "title": title, "tags": tags, "summary": summary}
