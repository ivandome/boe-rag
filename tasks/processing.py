import re


def clean_boe_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph breaks."""
    if not text:
        return ""
    # Normalize line endings
    text = text.replace("\r", "\n")
    # Collapse spaces and tabs but keep newlines
    cleaned = re.sub(r"[ \t]+", " ", text)
    # Collapse multiple newlines
    cleaned = re.sub(r"\n+", "\n", cleaned)
    return cleaned.strip()


def split_into_paragraphs(text: str) -> list[str]:
    """Split cleaned BOE article text into paragraphs."""
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    return paragraphs
