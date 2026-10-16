import httpx
from bs4 import BeautifulSoup

from .wikipedia import FetchedDocument


class URLFetcher:
    def fetch(self, url: str) -> FetchedDocument | None:
        try:
            resp = httpx.get(url, follow_redirects=True, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            title = soup.title.string if soup.title else url
            content = soup.get_text(separator="\n", strip=True)
            return FetchedDocument(title=title, content=content[:50000], source="url", url=url)
        except Exception:  # noqa: BLE001 - best-effort fetch, caller handles None
            return None
