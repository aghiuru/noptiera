import logging
import trafilatura

log = logging.getLogger(__name__)


def fetch_and_parse(url: str) -> dict:
    log.debug("Downloading %s", url)
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError(f"Failed to download URL: {url}")

    log.debug("Extracting content")
    doc = trafilatura.bare_extraction(downloaded, with_metadata=True)
    if not doc:
        raise ValueError(f"Failed to extract content from: {url}")

    result = {
        "title": doc.title,
        "text": doc.text,
        "author": doc.author,
        "date": doc.date,
        "url": doc.url or url,
    }
    return result
