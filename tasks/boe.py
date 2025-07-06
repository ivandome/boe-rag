from prefect import task
import requests
import re

BOE_BASE = "https://www.boe.es"


def _parse_date_to_ymd(fecha: str) -> tuple[str, str, str]:
    """Parsea una cadena de fecha y devuelve año, mes y día.

    Acepta ``YYYY-MM-DD``, ``YYYY/MM/DD`` o ``YYYYMMDD``. Se eliminan
    separadores y se valida que queden exactamente ocho dígitos.
    """

    digits = re.sub(r"\D", "", fecha)
    if len(digits) != 8:
        raise ValueError("La fecha debe contener año, mes y día (YYYYMMDD).")

    return digits[:4], digits[4:6], digits[6:8]


def _build_sumario_url(year: str, month: str, day: str) -> str:
    """Construye la URL del índice diario del BOE."""

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
    """Obtiene el índice XML diario dado año, mes y día."""

    url = _build_sumario_url(year, month, day)
    r = requests.get(url, headers={"Accept": "application/xml"})
    r.raise_for_status()
    if "xml" not in r.headers.get("Content-Type", ""):
        raise ValueError("La respuesta no es XML")
    return r.text


@task
def fetch_index_xml_by_date(fecha: str) -> str:
    """Descarga el índice XML para una fecha dada."""

    year, month, day = _parse_date_to_ymd(fecha)
    return fetch_index_xml.fn(year, month, day)


@task
def extract_article_ids(index_xml: str) -> list[str]:
    # Extraer BOE-A-XXXX-YYYY usando regex
    ids = re.findall(r"BOE-A-\d{4}-\d{5}", index_xml)
    return list(set(ids))  # evitar duplicados


@task
def get_article_metadata(boe_id: str, fecha: str) -> dict:
    # fecha is expected in YYYY-MM-DD format
    # For url_pdf, we need to parse fecha into YYYY, MM, DD
    # e.g., fecha = "2025-07-03" -> year="2025", month="07", day="03"
    try:
        year, month, day = fecha.split("-")
    except ValueError:
        # Handle cases where fecha might not be in the expected format, though previous steps should ensure this.
        # Alternatively, raise an error or log. For now, try to proceed if possible or adjust.
        # This part might need more robust error handling or assumptions based on strict input.
        # Assuming fecha is always "YYYY-MM-DD" as prepared by scrape_boe_day_metadata
        raise ValueError(
            f"Fecha format is incorrect in get_article_metadata: {fecha}. Expected YYYY-MM-DD."
        )

    url_xml = f"https://www.boe.es/diario_boe/xml.php?id={boe_id}"  # This remains unchanged as per current understanding
    url_pdf = f"https://www.boe.es/boe/dias/{year}/{month.zfill(2)}/{day.zfill(2)}/pdfs/{boe_id}.pdf"
    return {
        "id": boe_id,
        "fecha": fecha,  # Keep original fecha for metadata record
        "url_xml": url_xml,
        "url_pdf": url_pdf,
    }
