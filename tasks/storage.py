import json
from prefect import task
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@task
def storage_text(text: str, filename: str):
    path = Path("data/raw") / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    logger.info("Ruta de archivo utilizada: %s", path)
    logger.info("Texto almacenado correctamente.")


@task
def append_metadata(record: dict, file_path: str = "data/boe_metadata.jsonl"):
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info("Ruta de archivo utilizada: %s", path)
    logger.info("Registro de metadata guardado correctamente.")
