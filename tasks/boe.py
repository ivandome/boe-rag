from prefect import task
import requests
import re
import xml.etree.ElementTree as ET
from tasks.processing import clean_boe_text, split_into_paragraphs

BOE_BASE = "https://www.boe.es"


def _parse_date_to_ymd(date_str: str) -> tuple[str, str, str]:
    """Parse a date string and return year, month and day.

    Accepts ``YYYY-MM-DD``, ``YYYY/MM/DD`` or ``YYYYMMDD``. Separators are
    removed and exactly eight digits are required.
    """

    digits = re.sub(r"\D", "", date_str)
    if len(digits) != 8:
        raise ValueError("The date must contain year, month and day (YYYYMMDD).")

    return digits[:4], digits[4:6], digits[6:8]


def _build_sumario_url(year: str, month: str, day: str) -> str:
    """Build the daily BOE index URL."""

    return (
        f"{BOE_BASE}/datosabiertos/api/boe/sumario/"
        f"{year}{month.zfill(2)}{day.zfill(2)}"
    )


@task
def fetch_boes_from_data(year: str, month: str, day: str) -> str:
    month_padded = month.zfill(2)
    day_padded = day.zfill(2)
    url = f"https://www.boe.es/boe/dias/{year}/{month_padded}/{day_padded}/"
    r = requests.get(url)
    r.raise_for_status()
    return r.text


@task
def fetch_index_xml(year: str, month: str, day: str) -> str:
    """Get the daily XML index given year, month and day."""

    url = _build_sumario_url(year, month, day)
    r = requests.get(url, headers={"Accept": "application/xml"})
    r.raise_for_status()
    if "xml" not in r.headers.get("Content-Type", ""):
        raise ValueError("Response is not XML")
    return r.text


@task
def fetch_index_xml_by_date(date_str: str) -> str:
    """Download the XML index for a given date."""

    year, month, day = _parse_date_to_ymd(date_str)
    return fetch_index_xml.fn(year, month, day)


@task
def extract_article_ids(index_xml: str) -> list[str]:
    """Return unique article IDs from the daily index XML."""

    root = ET.fromstring(index_xml)
    ids: set[str] = set()
    for elem in root.iter():
        id_attr = elem.attrib.get("id")
        if id_attr and id_attr.startswith("BOE-A-"):
            ids.add(id_attr)

    return list(ids)


@task
def get_article_metadata(boe_id: str, date_str: str) -> dict:
    # date_str is expected in YYYY-MM-DD format
    # For url_pdf, we need to parse it into YYYY, MM, DD
    # e.g., date_str = "2025-07-03" -> year="2025", month="07", day="03"
    try:
        year, month, day = date_str.split("-")
    except ValueError:
        # Handle cases where date_str might not be in the expected format, though previous steps should ensure this.
        # Alternatively, raise an error or log. For now, try to proceed if possible or adjust.
        # This part might need more robust error handling or assumptions based on strict input.
        # Assuming date_str is always "YYYY-MM-DD" as prepared by scrape_boe_day_metadata
        raise ValueError(
            f"Date format is incorrect in get_article_metadata: {date_str}. Expected YYYY-MM-DD."
        )

    url_xml = f"https://www.boe.es/diario_boe/xml.php?id={boe_id}"
    url_pdf = f"https://www.boe.es/boe/dias/{year}/{month.zfill(2)}/{day.zfill(2)}/pdfs/{boe_id}.pdf"
    return {
        "id": boe_id,
        "date": date_str,  # Keep original date for metadata record
        "url_xml": url_xml,
        "url_pdf": url_pdf,
    }


@task
def fetch_article_xml(boe_id: str) -> str:
    """Download the XML for a specific article."""
    url = f"https://www.boe.es/diario_boe/xml.php?id={boe_id}"
    r = requests.get(url)
    r.raise_for_status()
    return r.text


@task
def parse_article_xml(xml_text: str) -> dict:
    """Extract main fields and processed segments from an article XML."""
    root = ET.fromstring(xml_text)
    title = root.findtext(".//titulo")
    department = root.findtext(".//departamento")
    rank = root.findtext(".//rango")
    raw_text = root.findtext(".//texto") or ""
    cleaned = clean_boe_text(raw_text)
    segments = split_into_paragraphs(cleaned)
    return {
        "title": title,
        "department": department,
        "rank": rank,
        "segments": segments,
    }


@task
def fetch_article_text(url_xml: str) -> tuple[dict, list[str]]:
    """Download an article XML and return metadata and cleaned segments."""
    r = requests.get(url_xml)
    r.raise_for_status()
    xml_text = r.text
    article_data = parse_article_xml.fn(xml_text)
    metadata = {
        "title": article_data.get("title"),
        "department": article_data.get("department"),
        "rank": article_data.get("rank"),
    }
    return metadata, article_data.get("segments")
