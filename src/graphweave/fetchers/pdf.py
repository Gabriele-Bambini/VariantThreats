from pathlib import Path

import fitz  # pymupdf

from .wikipedia import FetchedDocument


class PDFFetcher:
    def fetch(self, path: str | Path) -> FetchedDocument | None:
        path = Path(path)
        if not path.exists():
            return None
        try:
            doc = fitz.open(str(path))
            text = "\n".join(page.get_text() for page in doc)
            return FetchedDocument(
                title=path.stem,
                content=text[:80000],
                source="pdf",
                url=str(path.absolute()),
            )
        except Exception:  # noqa: BLE001 - best-effort fetch, caller handles None
            return None
