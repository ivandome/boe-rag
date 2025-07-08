from prefect import task
from tasks import session
from bs4 import BeautifulSoup


@task
def scrape_example_page(url: str) -> str:
    response = session.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text()
