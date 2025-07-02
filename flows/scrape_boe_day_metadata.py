from prefect import flow
from tasks.storage import append_metadata
from tasks.boe import fetch_index_xml, extract_article_ids, get_article_metadata


@flow
def scrape_boe_day_metadata(fecha: str = "2025-06-28"):
    index_xml = fetch_index_xml(fecha)
    boe_ids = extract_article_ids(index_xml)
    for boe_id in boe_ids:
        metadata = get_article_metadata(boe_id, fecha)
        append_metadata(metadata)
