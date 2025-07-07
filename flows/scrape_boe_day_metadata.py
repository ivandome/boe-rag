from prefect import flow
from tasks.storage import append_metadata
from tasks.boe import (
    fetch_index_xml,
    extract_article_ids,
    get_article_metadata,
    fetch_article_xml,
    parse_article_xml,
)
from tasks.database import insert_article, article_exists


@flow
def scrape_boe_day_metadata(url_date_str: str = "2025/07/03"):
    # Parse year, month, day from url_date_str (e.g., "2025/07/03")
    parts = url_date_str.split("/")
    if len(parts) != 3:
        raise ValueError("url_date_str must be in YYYY/MM/DD format")
    year, month, day = parts[0], parts[1], parts[2]

    index_boes = fetch_index_xml(year, month, day)
    boe_ids = extract_article_ids(index_boes)

    # Reconstruct the date in YYYY-MM-DD format for get_article_metadata
    date_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    for boe_id in boe_ids:
        # Skip if already stored
        if article_exists(boe_id):
            continue

        metadata = get_article_metadata(boe_id, date_iso)
        xml_text = fetch_article_xml(boe_id)
        article_data = parse_article_xml(xml_text)
        record = {
            **metadata,
            "title": article_data.get("title"),
            "department": article_data.get("department"),
            "rank": article_data.get("rank"),
        }
        insert_article(record, article_data.get("text"))
        append_metadata(metadata)
