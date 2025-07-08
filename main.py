from flows.scrape_and_store import scrape_and_store
from flows.scrape_boe_day_metadata import scrape_boe_day_metadata
import argparse

DEFAULT_DATE = "2025/06/28"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BOE scraping flows")
    parser.add_argument(
        "--date",
        default=DEFAULT_DATE,
        help="Date in YYYY/MM/DD format for scrape_boe_day_metadata",
    )
    args = parser.parse_args()

    # Test run for scrape and store all articles
    # scrape_and_store(
    #     url="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2025-13297",
    #     filename="boe_13297.txt"
    # )

    # Test run for scape and process a day articles
    scrape_boe_day_metadata(args.date)


if __name__ == "__main__":
    main()
