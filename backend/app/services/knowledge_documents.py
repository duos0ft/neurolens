"""Parsing and chunking of organization knowledge documents.

Documents are Markdown files with a small front-matter block, for example::

    ---
    slug: annual-leave
    title: Annual Leave Policy
    version: 2.1
    owner: People Operations
    effective_date: 2026-01-01
    status: verified
    verified_by: Priya Raman, Head of People Operations
    verified_on: 2026-09-15
    ---

Only documents with ``status: verified`` can ground policy answers.
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import date

FRONT_MATTER_DELIMITER = "---"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

VERIFICATION_STATUSES = frozenset({"draft", "verified", "retired"})
REQUIRED_FIELDS = ("slug", "title", "version", "status")

DEFAULT_MAX_CHUNK_CHARS = 1000


class KnowledgeDocumentError(ValueError):
    """Raised when a knowledge document is malformed."""


@dataclass(frozen=True)
class ParsedKnowledgeDocument:
    slug: str
    title: str
    source_version: str
    owner: str | None
    effective_date: date | None
    verification_status: str
    verified_by: str | None
    verified_on: date | None
    body: str
    source_path: str
    content_sha256: str

    @property
    def is_verified(self) -> bool:
        return self.verification_status == "verified"


@dataclass(frozen=True)
class DocumentChunk:
    index: int
    section: str | None
    content: str


def _normalize_text(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    return "\n".join(line.rstrip() for line in text.split("\n")).strip() + "\n"


def _parse_date(field: str, value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise KnowledgeDocumentError(f"{field} must be an ISO date (YYYY-MM-DD)") from error


def parse_knowledge_document(raw: str, source_path: str) -> ParsedKnowledgeDocument:
    text = _normalize_text(raw)
    lines = text.split("\n")

    if not lines or lines[0].strip() != FRONT_MATTER_DELIMITER:
        raise KnowledgeDocumentError(f"{source_path}: missing front matter")

    try:
        closing = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == FRONT_MATTER_DELIMITER
        )
    except StopIteration as error:
        raise KnowledgeDocumentError(f"{source_path}: unterminated front matter") from error

    metadata: dict[str, str] = {}

    for line in lines[1:closing]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        key, separator, value = line.partition(":")

        if not separator:
            raise KnowledgeDocumentError(f"{source_path}: invalid front matter line {line!r}")

        key = key.strip().lower()

        if key in metadata:
            raise KnowledgeDocumentError(f"{source_path}: duplicate front matter key {key!r}")

        metadata[key] = value.strip().strip('"').strip("'")

    for field in REQUIRED_FIELDS:
        if not metadata.get(field):
            raise KnowledgeDocumentError(f"{source_path}: missing required field {field!r}")

    slug = metadata["slug"]

    if not SLUG_PATTERN.match(slug):
        raise KnowledgeDocumentError(f"{source_path}: invalid slug {slug!r}")

    status = metadata["status"].lower()

    if status not in VERIFICATION_STATUSES:
        raise KnowledgeDocumentError(f"{source_path}: invalid status {status!r}")

    verified_by = metadata.get("verified_by") or None
    verified_on = (
        _parse_date("verified_on", metadata["verified_on"]) if metadata.get("verified_on") else None
    )

    if status == "verified" and (verified_by is None or verified_on is None):
        raise KnowledgeDocumentError(
            f"{source_path}: verified documents require verified_by and verified_on"
        )

    body = "\n".join(lines[closing + 1 :]).strip()

    if not body:
        raise KnowledgeDocumentError(f"{source_path}: document body is empty")

    return ParsedKnowledgeDocument(
        slug=slug,
        title=metadata["title"],
        source_version=metadata["version"],
        owner=metadata.get("owner") or None,
        effective_date=(
            _parse_date("effective_date", metadata["effective_date"])
            if metadata.get("effective_date")
            else None
        ),
        verification_status=status,
        verified_by=verified_by,
        verified_on=verified_on,
        body=body,
        source_path=source_path,
        # The hash covers metadata as well as the body, so a change to the
        # verification status or effective date also creates a new revision.
        content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    current = ""

    for sentence in SENTENCE_BOUNDARY.split(paragraph):
        candidate = f"{current} {sentence}".strip() if current else sentence

        if current and len(candidate) > max_chars:
            pieces.append(current)
            current = sentence
        else:
            current = candidate

    if current:
        pieces.append(current)

    return pieces


def _pack_paragraphs(paragraphs: list[str], max_chars: int) -> list[str]:
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        parts = (
            _split_long_paragraph(paragraph, max_chars)
            if len(paragraph) > max_chars
            else [paragraph]
        )

        for part in parts:
            candidate = f"{current}\n\n{part}" if current else part

            if current and len(candidate) > max_chars:
                chunks.append(current)
                current = part
            else:
                current = candidate

    if current:
        chunks.append(current)

    return chunks


def chunk_knowledge_document(
    document: ParsedKnowledgeDocument,
    max_chars: int = DEFAULT_MAX_CHUNK_CHARS,
) -> list[DocumentChunk]:
    """Split a document into section-aware passages.

    Chunks never cross a heading boundary, so every passage can be cited with
    a single section name.
    """

    sections: list[tuple[str | None, list[str]]] = []
    heading_path: list[tuple[int, str]] = []
    current_lines: list[str] = []

    def section_name() -> str | None:
        # The level-1 heading is the document title and is cited separately.
        names = [name for level, name in heading_path if level > 1]

        return " > ".join(names) or None

    def flush() -> None:
        if any(line.strip() for line in current_lines):
            sections.append((section_name(), list(current_lines)))

        current_lines.clear()

    for line in document.body.split("\n"):
        match = HEADING_PATTERN.match(line)

        if match:
            flush()
            level = len(match.group(1))
            heading_path[:] = [entry for entry in heading_path if entry[0] < level]
            heading_path.append((level, match.group(2).strip()))
            continue

        current_lines.append(line)

    flush()

    chunks: list[DocumentChunk] = []

    for section, lines in sections:
        paragraphs = [
            " ".join(part.split()) if not _is_list_block(part) else part.strip()
            for part in "\n".join(lines).split("\n\n")
            if part.strip()
        ]

        for content in _pack_paragraphs(paragraphs, max_chars):
            chunks.append(
                DocumentChunk(
                    index=len(chunks),
                    section=section,
                    content=content,
                )
            )

    if not chunks:
        raise KnowledgeDocumentError(f"{document.source_path}: no content to index")

    return chunks


def _is_list_block(block: str) -> bool:
    return any(
        line.lstrip().startswith(("- ", "* ")) or re.match(r"^\s*\d+\.\s", line)
        for line in block.split("\n")
    )


def embedding_text(document_title: str, chunk: DocumentChunk) -> str:
    """Text sent to the embedding model for one chunk."""

    heading = f"{document_title} — {chunk.section}" if chunk.section else document_title

    return f"{heading}\n\n{chunk.content}"
