from prefect import flow
from tasks.scraping import scrape_example_page
from tasks.storage import storage_text


@flow
def scrape_and_store(url: str, filename: str):
    text = scrape_example_page(url)
    storage_text(text, filename)
