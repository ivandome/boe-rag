from prefect import flow
from tasks.scraping import scrape_example_page
from tasks.storage import storage_text


@flow
def scrape_and_store(url: str, filename: str):
    print("Inicio del flow scrape_and_store")
    print(f"Par\u00e1metros -> url: {url}, filename: {filename}")

    text = scrape_example_page(url)
    storage_text(text, filename)

    print(
        "Fin del flow scrape_and_store -> art\u00edculos procesados: 1, "
        f"caracteres guardados: {len(text)}"
    )
