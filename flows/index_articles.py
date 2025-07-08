from prefect import flow

from tasks.database import init_db, fetch_all_articles
from tasks.indexing import create_or_update_index


@flow
def index_articles(db_path: str = "data/boe.db"):
    print("Inicio del flow index_articles")
    print(f"Par\u00e1metros -> db_path: {db_path}")

    init_db(db_path)
    records = fetch_all_articles(db_path)
    print(f"Art\u00edculos recuperados: {len(records)}")
    create_or_update_index(records)
    print(
        "Fin del flow index_articles -> art\u00edculos indexados: "
        f"{len(records)}"
    )
