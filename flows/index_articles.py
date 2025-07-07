from prefect import flow

from tasks.database import init_db, fetch_all_articles
from tasks.indexing import create_or_update_index


@flow
def index_articles(db_path: str = "data/boe.db"):
    init_db(db_path)
    records = fetch_all_articles(db_path)
    create_or_update_index(records)
