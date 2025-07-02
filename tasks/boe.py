from prefect import task
import requests
import re

BOE_BASE = "https://www.boe.es"


@task
def fetch_index_xml(fecha: str) -> str:
    url = f"{BOE_BASE}/diario_boe/xml.php?fecha={fecha}"
    r = requests.get(url)
    r.raise_for_status()
    return r.text


@task
def extract_article_ids(index_xml: str) -> list[str]:
    # Extraer BOE-A-XXXX-YYYY usando regex
    ids = re.findall(r'BOE-A-\d{4}-\d{5}', index_xml)
    return list(set(ids))  # evitar duplicados


@task
def get_article_metadata(boe_id: str, fecha: str) -> dict:
    url_xml = f"https://www.boe.es/diario_boe/xml.php?id={boe_id}"
    url_pdf = f"https://www.boe.es/boe/dias/{fecha}/pdfs/{boe_id}.pdf"
    return {
        "id": boe_id,
        "fecha": fecha,
        "url_xml": url_xml,
        "url_pdf": url_pdf
    }
