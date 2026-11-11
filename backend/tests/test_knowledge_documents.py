import pytest

from app.services.knowledge_documents import (
    KnowledgeDocumentError,
    chunk_knowledge_document,
    embedding_text,
    parse_knowledge_document,
)
from tests.helpers.knowledge import KNOWLEDGE_DIR

VALID_DOCUMENT = """---
slug: annual-leave
title: Annual Leave Policy
version: 2.1
owner: People Operations
effective_date: 2026-01-01
status: verified
verified_by: Priya Raman
verified_on: 2025-12-10
---

# Annual Leave Policy

Intro paragraph.

## Entitlement

Full-time employees receive 25 days of paid annual leave.

### Part-time staff

Part-time employees receive leave pro rata.

## Carrying over leave

- Up to five days may be carried over.
- Carried-over leave expires on 31 March.
"""


def test_parses_front_matter_and_provenance() -> None:
    document = parse_knowledge_document(VALID_DOCUMENT, "annual-leave.md")

    assert document.slug == "annual-leave"
    assert document.title == "Annual Leave Policy"
    assert document.source_version == "2.1"
    assert document.owner == "People Operations"
    assert document.effective_date.isoformat() == "2026-01-01"
    assert document.is_verified
    assert document.verified_by == "Priya Raman"
    assert document.source_path == "annual-leave.md"
    assert len(document.content_sha256) == 64


def test_hash_ignores_line_endings_but_tracks_metadata() -> None:
    original = parse_knowledge_document(VALID_DOCUMENT, "a.md")
    windows = parse_knowledge_document(VALID_DOCUMENT.replace("\n", "\r\n"), "a.md")
    retired = parse_knowledge_document(
        VALID_DOCUMENT.replace("status: verified", "status: retired"), "a.md"
    )

    assert original.content_sha256 == windows.content_sha256
    assert original.content_sha256 != retired.content_sha256


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ("# No front matter\n\nBody", "missing front matter"),
        ("---\nslug: a\n\nBody", "unterminated front matter"),
        (VALID_DOCUMENT.replace("title: Annual Leave Policy\n", ""), "'title'"),
        (VALID_DOCUMENT.replace("slug: annual-leave", "slug: Annual Leave"), "invalid slug"),
        (VALID_DOCUMENT.replace("status: verified", "status: approved"), "invalid status"),
        (VALID_DOCUMENT.replace("verified_by: Priya Raman\n", ""), "require verified_by"),
        (VALID_DOCUMENT.replace("2026-01-01", "1 Jan 2026"), "ISO date"),
        (VALID_DOCUMENT.split("# Annual")[0], "body is empty"),
        (VALID_DOCUMENT.replace("owner:", "slug:", 1), "duplicate"),
    ],
)
def test_rejects_malformed_documents(document: str, message: str) -> None:
    with pytest.raises(KnowledgeDocumentError, match=message):
        parse_knowledge_document(document, "bad.md")


def test_draft_documents_do_not_need_verifier() -> None:
    draft = VALID_DOCUMENT.replace("status: verified", "status: draft")
    draft = draft.replace("verified_by: Priya Raman\n", "").replace("verified_on: 2025-12-10\n", "")

    document = parse_knowledge_document(draft, "draft.md")

    assert not document.is_verified


def test_chunks_follow_section_headings() -> None:
    document = parse_knowledge_document(VALID_DOCUMENT, "annual-leave.md")

    chunks = chunk_knowledge_document(document)

    assert [chunk.section for chunk in chunks] == [
        None,
        "Entitlement",
        "Entitlement > Part-time staff",
        "Carrying over leave",
    ]
    assert [chunk.index for chunk in chunks] == [0, 1, 2, 3]
    assert chunks[1].content == "Full-time employees receive 25 days of paid annual leave."
    # List formatting is preserved so bullet items stay readable.
    assert chunks[3].content.startswith("- Up to five days")
    assert "\n- Carried-over" in chunks[3].content


def test_long_sections_are_split_within_the_section() -> None:
    sentences = " ".join(f"Rule number {index} applies to everyone." for index in range(80))
    document = parse_knowledge_document(
        VALID_DOCUMENT.split("# Annual")[0] + f"# Title\n\n## Rules\n\n{sentences}\n",
        "long.md",
    )

    chunks = chunk_knowledge_document(document, max_chars=400)

    assert len(chunks) > 1
    assert all(chunk.section == "Rules" for chunk in chunks)
    assert all(len(chunk.content) <= 400 for chunk in chunks)
    assert " ".join(chunk.content for chunk in chunks) == sentences


def test_embedding_text_includes_title_and_section() -> None:
    document = parse_knowledge_document(VALID_DOCUMENT, "annual-leave.md")
    chunk = chunk_knowledge_document(document)[1]

    assert embedding_text(document.title, chunk).startswith("Annual Leave Policy — Entitlement")


def test_repository_knowledge_documents_are_valid() -> None:
    paths = sorted(KNOWLEDGE_DIR.glob("*.md"))
    documents = [
        parse_knowledge_document(path.read_text(encoding="utf-8"), path.name) for path in paths
    ]

    assert len({document.slug for document in documents}) == len(documents)

    verified = {document.slug for document in documents if document.is_verified}

    assert verified == {
        "annual-leave",
        "remote-work",
        "communication-guidelines",
        "data-handling",
        "employee-support",
    }

    for document in documents:
        assert chunk_knowledge_document(document)
