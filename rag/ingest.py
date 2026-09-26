from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class Section:
    document_id: str
    title: str
    section: str
    text: str
    source_path: str
    estimated_pages: float


class _PolicyHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.document_id = ""
        self.estimated_pages = 1.0
        self.title = ""
        self.current_heading = "Overview"
        self.in_title = False
        self.in_heading = False
        self.in_text = False
        self.buffer: list[str] = []
        self.sections: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag == "meta" and attrs_dict.get("name") == "document-id":
            self.document_id = attrs_dict.get("content", "")
        if tag == "meta" and attrs_dict.get("name") == "estimated-pages":
            try:
                self.estimated_pages = float(attrs_dict.get("content", "1"))
            except ValueError:
                self.estimated_pages = 1.0
        if tag == "title":
            self.in_title = True
            self.buffer = []
        elif tag in {"h1", "h2", "h3"}:
            self._flush_text()
            self.in_heading = True
            self.buffer = []
        elif tag in {"p", "li"}:
            self.in_text = True
            self.buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self.in_title:
            self.title = " ".join(self.buffer).strip()
            self.in_title = False
            self.buffer = []
        elif tag in {"h1", "h2", "h3"} and self.in_heading:
            heading = " ".join(self.buffer).strip()
            if tag == "h1" and heading:
                self.title = heading
            elif heading:
                self.current_heading = heading
            self.in_heading = False
            self.buffer = []
        elif tag in {"p", "li"} and self.in_text:
            text = " ".join(self.buffer).strip()
            if text:
                self.sections.append((self.current_heading, text))
            self.in_text = False
            self.buffer = []

    def handle_data(self, data: str) -> None:
        if self.in_title or self.in_heading or self.in_text:
            clean = re.sub(r"\s+", " ", data).strip()
            if clean:
                self.buffer.append(clean)

    def _flush_text(self) -> None:
        if self.in_text:
            text = " ".join(self.buffer).strip()
            if text:
                self.sections.append((self.current_heading, text))
            self.in_text = False
            self.buffer = []


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip('"')
    return values, text[end + 5 :]


def load_markdown(path: Path, root: Path) -> list[Section]:
    metadata, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    document_id = metadata.get("document_id", path.stem.upper())
    title = metadata.get("title", path.stem.replace("-", " ").title())
    estimated_pages = float(metadata.get("estimated_pages", "1"))
    current = "Overview"
    parts: dict[str, list[str]] = {current: []}
    for raw_line in body.splitlines():
        line = raw_line.strip()
        match = re.match(r"^#{1,3}\s+(.+)$", line)
        if match:
            heading = match.group(1).strip()
            if line.startswith("# "):
                title = heading
                continue
            current = heading
            parts.setdefault(current, [])
        elif line:
            parts.setdefault(current, []).append(line)
    return [
        Section(
            document_id=document_id,
            title=title,
            section=section,
            text=re.sub(r"\s+", " ", " ".join(lines)).strip(),
            source_path=str(path.relative_to(root)),
            estimated_pages=estimated_pages,
        )
        for section, lines in parts.items()
        if lines
    ]


def load_html(path: Path, root: Path) -> list[Section]:
    parser = _PolicyHTMLParser()
    parser.feed(path.read_text(encoding="utf-8"))
    grouped: dict[str, list[str]] = {}
    for section, text in parser.sections:
        grouped.setdefault(section, []).append(text)
    return [
        Section(
            document_id=parser.document_id or path.stem.upper(),
            title=parser.title or path.stem.replace("-", " ").title(),
            section=section,
            text=re.sub(r"\s+", " ", " ".join(lines)).strip(),
            source_path=str(path.relative_to(root)),
            estimated_pages=parser.estimated_pages,
        )
        for section, lines in grouped.items()
        if lines
    ]


def load_policy_sections(policy_dir: Path) -> list[Section]:
    root = policy_dir.parent
    sections: list[Section] = []
    for path in sorted(policy_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".md", ".markdown"}:
            sections.extend(load_markdown(path, root))
        elif path.suffix.lower() in {".html", ".htm"}:
            sections.extend(load_html(path, root))
    return sections


def chunk_sections(
    sections: Iterable[Section], *, chunk_words: int = 180, overlap_words: int = 30
) -> list[dict[str, object]]:
    if chunk_words <= overlap_words:
        raise ValueError("chunk_words must be greater than overlap_words")
    chunks: list[dict[str, object]] = []
    for section in sections:
        words = section.text.split()
        if not words:
            continue
        start = 0
        ordinal = 1
        while start < len(words):
            end = min(start + chunk_words, len(words))
            content = " ".join(words[start:end])
            chunks.append(
                {
                    "chunk_id": f"{section.document_id}:{slug(section.section)}:{ordinal}",
                    "document_id": section.document_id,
                    "title": section.title,
                    "section": section.section,
                    "source_path": section.source_path,
                    "content": content,
                    "estimated_pages": section.estimated_pages,
                    "word_count": len(words[start:end]),
                }
            )
            if end == len(words):
                break
            start = end - overlap_words
            ordinal += 1
    return chunks


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "section"
