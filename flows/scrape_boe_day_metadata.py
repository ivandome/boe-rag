from prefect import flow
from tasks.storage import append_metadata
from tasks.boe import fetch_boes_from_data, extract_article_ids, get_article_metadata


@flow
def scrape_boe_day_metadata(url_date_str: str = "2025/07/03"):
    # Parse year, month, day from url_date_str (e.g., "2025/07/03")
    parts = url_date_str.split("/")
    if len(parts) != 3:
        raise ValueError("url_date_str must be in YYYY/MM/DD format")
    year, month, day = parts[0], parts[1], parts[2]

    index_boes = fetch_boes_from_data(year, month, day)
    boe_ids = extract_article_ids(index_boes)

    # Reconstruct fecha in YYYY-MM-DD format for get_article_metadata
    # and potentially for other uses if the PDF URL format still needs it.
    fecha_yyyymmdd = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    for boe_id in boe_ids:
        # Pass the original year, month, day for consistency if needed,
        # or the reconstructed fecha_yyyymmdd.
        # Based on current get_article_metadata, it expects fecha in YYYY-MM-DD for PDF URLs.
        metadata = get_article_metadata(boe_id, fecha_yyyymmdd)
        append_metadata(metadata)
