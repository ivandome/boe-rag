from prefect import task
from tasks import session
import re
import xml.etree.ElementTree as ET
from tasks.processing import clean_boe_text, split_into_paragraphs

BOE_BASE = "https://www.boe.es"


def _parse_date_to_ymd(date_str: str) -> tuple[str, str, str]:
    """Parse a date string and return year, month and day.

    Accepts ``YYYY-MM-DD``, ``YYYY/MM/DD`` or ``YYYYMMDD``. Separators are
    removed and exactly eight digits are required.
    """

    print(f"_parse_date_to_ymd -> date_str: {date_str}")
    digits = re.sub(r"\D", "", date_str)
    if len(digits) != 8:
        raise ValueError("The date must contain year, month and day (YYYYMMDD).")

    year, month, day = digits[:4], digits[4:6], digits[6:8]
    print(f"_parse_date_to_ymd -> parsed: {year}-{month}-{day}")
    return year, month, day


def _build_sumario_url(year: str, month: str, day: str) -> str:
    """Build the daily BOE index URL."""

    url = (
        f"{BOE_BASE}/datosabiertos/api/boe/sumario/"
        f"{year}{month.zfill(2)}{day.zfill(2)}"
    )
    print(f"_build_sumario_url -> year:{year} month:{month} day:{day} url:{url}")
    return url


@task
def fetch_boes_from_data(year: str, month: str, day: str) -> str:
    print(f"fetch_boes_from_data -> params: year={year} month={month} day={day}")
    month_padded = month.zfill(2)
    day_padded = day.zfill(2)
    url = f"https://www.boe.es/boe/dias/{year}/{month_padded}/{day_padded}/"
    print(f"fetch_boes_from_data -> url: {url}")
    r = session.get(url, timeout=10)
    r.raise_for_status()
    print("fetch_boes_from_data -> response size:", len(r.text))
    return r.text


@task(retries=2, retry_delay_seconds=5)
def fetch_index_xml(year: str, month: str, day: str) -> str:
    """Get the daily XML index given year, month and day."""
    print(f"fetch_index_xml -> params: year={year} month={month} day={day}")
    url = _build_sumario_url(year, month, day)
    print(f"fetch_index_xml -> url: {url}")
    r = session.get(url, headers={"Accept": "application/xml"}, timeout=10)
    if r.status_code == 404:
        print("fetch_index_xml -> index not found (404)")
        return ""
    r.raise_for_status()
    if "xml" not in r.headers.get("Content-Type", ""):
        raise ValueError("Response is not XML")
    print("fetch_index_xml -> response size:", len(r.text))
    return r.text


@task
def fetch_index_xml_by_date(date_str: str) -> str:
    """Download the XML index for a given date."""
    print(f"fetch_index_xml_by_date -> date_str: {date_str}")
    year, month, day = _parse_date_to_ymd(date_str)
    return fetch_index_xml.fn(year, month, day)


@task
def extract_article_ids(index_xml: str) -> list[str]:
    """Return unique article IDs from the daily index XML."""

    root = ET.fromstring(index_xml)
    ids: set[str] = set()
    pattern = re.compile(r"BOE-[A-Z]-\d{4}-\d{5}")

    for elem in root.iter():
        # Look for IDs in any attribute value
        for value in elem.attrib.values():
            ids.update(pattern.findall(value))

        # Also check element text content
        if elem.text:
            ids.update(pattern.findall(elem.text))

    id_list = list(ids)
    print(f"extract_article_ids -> found {len(id_list)} ids")
    return id_list


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

    print(f"get_article_metadata -> boe_id:{boe_id} date_str:{date_str}")
    url_xml = f"https://www.boe.es/diario_boe/xml.php?id={boe_id}"
    url_pdf = f"https://www.boe.es/boe/dias/{year}/{month.zfill(2)}/{day.zfill(2)}/pdfs/{boe_id}.pdf"
    metadata = {
        "id": boe_id,
        "date": date_str,  # Keep original date for metadata record
        "url_xml": url_xml,
        "url_pdf": url_pdf,
    }
    print(f"get_article_metadata -> metadata: {metadata}")
    return metadata


@task(retries=2, retry_delay_seconds=5)
def fetch_article_xml(boe_id: str) -> str:
    """Download the XML for a specific article."""
    print(f"fetch_article_xml -> boe_id: {boe_id}")
    url = f"https://www.boe.es/diario_boe/xml.php?id={boe_id}"
    print(f"fetch_article_xml -> url: {url}")
    r = session.get(url, timeout=10)
    r.raise_for_status()
    print("fetch_article_xml -> response size:", len(r.text))
    return r.text


def _parse_additional_fields(root: ET.Element) -> dict:
    """Extract metadata and analysis sections from an article XML tree."""
    data: dict = {}
    meta = root.find(".//metadatos")
    if meta is not None:
        data["identificador"] = meta.findtext("identificador")
        data["fecha_disposicion"] = meta.findtext("fecha_disposicion")
        data["diario"] = meta.findtext("diario")
        data["fecha_publicacion"] = meta.findtext("fecha_publicacion")
        data["pagina_inicial"] = meta.findtext("pagina_inicial")
        data["pagina_final"] = meta.findtext("pagina_final")

    analysis = root.find(".//analisis")
    if analysis is not None:
        materias = [m.text for m in analysis.findall(".//materias/materia") if m.text]
        notas = [n.text for n in analysis.findall(".//notas/nota") if n.text]
        referencias = [
            r.text for r in analysis.findall(".//referencias/referencia") if r.text
        ]
        alertas = [a.text for a in analysis.findall(".//alertas/alerta") if a.text]

        data["materias"] = materias
        data["notas"] = notas
        data["referencias"] = referencias
        data["alertas"] = alertas

    return data


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
    data = {
        "title": title,
        "department": department,
        "rank": rank,
        "segments": segments,
    }
    data.update(_parse_additional_fields(root))
    print(
        f"parse_article_xml -> title:{title} department:{department} rank:{rank} segments:{len(segments)}"
    )
    return data


@task
def fetch_article_text(url_xml: str) -> tuple[dict, list[str]]:
    """Download an article XML and return metadata and cleaned segments."""
    print(f"fetch_article_text -> url: {url_xml}")
    r = session.get(url_xml, timeout=10)
    r.raise_for_status()
    xml_text = r.text
    print("fetch_article_text -> downloaded", len(xml_text), "chars")
    article_data = parse_article_xml.fn(xml_text)
    metadata = {
        "title": article_data.get("title"),
        "department": article_data.get("department"),
        "rank": article_data.get("rank"),
    }
    print(f"fetch_article_text -> metadata: {metadata}")
    return metadata, article_data.get("segments")
