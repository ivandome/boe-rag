from prefect import task
from typing import Iterable
from pathlib import Path
import json

from tasks.processing import split_into_paragraphs


@task
def create_or_update_index(
    records: Iterable[dict],
    index_path: str = "data/index.faiss",
    meta_path: str = "data/index_meta.jsonl",
):
    """Compute embeddings for each fragment and store them in a local index."""

    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np

    model = SentenceTransformer("all-MiniLM-L6-v2")
    dim = model.get_sentence_embedding_dimension()

    index_file = Path(index_path)
    meta_file = Path(meta_path)

    if index_file.exists():
        index = faiss.read_index(str(index_file))
        metas = (
            [json.loads(line) for line in meta_file.read_text(encoding="utf-8").splitlines()]
            if meta_file.exists()
            else []
        )
    else:
        index_file.parent.mkdir(parents=True, exist_ok=True)
        index = faiss.IndexFlatL2(dim)
        metas = []

    for record in records:
        segments = split_into_paragraphs(record.get("text", ""))
        if not segments:
            continue
        embeddings = model.encode(segments)
        index.add(np.array(embeddings, dtype="float32"))
        metas.extend({"id": record.get("id"), "title": record.get("title")} for _ in segments)

    faiss.write_index(index, str(index_file))
    meta_file.write_text(
        "\n".join(json.dumps(m, ensure_ascii=False) for m in metas),
        encoding="utf-8",
    )
