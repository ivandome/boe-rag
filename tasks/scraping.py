from prefect import task
import requests
from bs4 import BeautifulSoup


@task
def scrape_example_page(url: str) -> str:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text()
