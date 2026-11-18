import io
from dataclasses import dataclass

from pypdf import PdfReader


class PolicyTextExtractionError(Exception):
    pass


@dataclass(frozen=True)
class ExtractedPolicyPage:
    page_number: int
    content: str


class PolicyTextExtractionService:
    def extract(self, content: bytes) -> list[ExtractedPolicyPage]:
        try:
            reader = PdfReader(io.BytesIO(content), strict=False)

            if reader.is_encrypted:
                raise PolicyTextExtractionError("Encrypted policy PDFs are not supported")

            pages: list[ExtractedPolicyPage] = []

            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text()

                if not text:
                    continue

                normalized_text = "\n".join(
                    line.strip() for line in text.splitlines() if line.strip()
                )

                if normalized_text:
                    pages.append(
                        ExtractedPolicyPage(
                            page_number=page_number,
                            content=normalized_text,
                        )
                    )

            if not pages:
                raise PolicyTextExtractionError("No extractable text found in policy PDF")

            return pages

        except PolicyTextExtractionError:
            raise
        except Exception as error:
            raise PolicyTextExtractionError("Unable to extract policy PDF text") from error
