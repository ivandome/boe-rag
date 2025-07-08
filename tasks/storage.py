import json
from prefect import task
from pathlib import Path


@task
def storage_text(text: str, filename: str):
    path = Path("data/raw") / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Ruta de archivo utilizada: {path}")
    print("Texto almacenado correctamente.")


@task
def append_metadata(record: dict, file_path: str = "data/boe_metadata.jsonl"):
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Ruta de archivo utilizada: {path}")
    print("Registro de metadata guardado correctamente.")
