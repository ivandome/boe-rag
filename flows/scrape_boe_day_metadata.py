from prefect import flow
from tasks.boe import (
    fetch_index_xml,
    extract_article_ids,
    get_article_metadata,
    fetch_article_xml,
    parse_article_xml,
)
from tasks.database import init_db, insert_article, article_exists


@flow
def scrape_boe_day_metadata(url_date_str: str = "2025/07/03"):
    print("Inicio del flow scrape_boe_day_metadata")
    print(f"Par\u00e1metros -> url_date_str: {url_date_str}")

    # Parse year, month, day from url_date_str (e.g., "2025/07/03")
    parts = url_date_str.split("/")
    if len(parts) != 3:
        raise ValueError("url_date_str must be in YYYY/MM/DD format")
    year, month, day = parts[0], parts[1], parts[2]

    # Ensure database is initialized
    init_db()

    index_boes = fetch_index_xml(year, month, day)
    if not index_boes:
        print("No existe \u00edndice para la fecha indicada.")
        return
    boe_ids = extract_article_ids(index_boes)
    print(f"Art\u00edculos encontrados: {len(boe_ids)}")

    # Reconstruct the date in YYYY-MM-DD format for get_article_metadata
    date_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    processed = 0
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
        insert_article(record, "\n".join(article_data.get("segments", [])))
        processed += 1

    print(
        "Fin del flow scrape_boe_day_metadata -> art\u00edculos almacenados: "
        f"{processed}"
    )
