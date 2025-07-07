import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def test_create_or_update_index(tmp_path):
    fake_model = MagicMock()
    fake_model.get_sentence_embedding_dimension.return_value = 3
    fake_model.encode.return_value = [[0.1, 0.2, 0.3]]

    fake_sentence_module = SimpleNamespace(SentenceTransformer=MagicMock(return_value=fake_model))
    fake_index = MagicMock()
    fake_faiss = SimpleNamespace(
        IndexFlatL2=MagicMock(return_value=fake_index),
        write_index=MagicMock(),
        read_index=MagicMock(side_effect=FileNotFoundError),
    )
    fake_numpy = SimpleNamespace(array=lambda x, dtype=None: x)

    with patch.dict('sys.modules', {
        'faiss': fake_faiss,
        'sentence_transformers': fake_sentence_module,
        'numpy': fake_numpy,
    }):
        from tasks.indexing import create_or_update_index

        record = {'id': '1', 'title': 'Title', 'text': 'Some text'}
        index_path = tmp_path / 'index.faiss'
        meta_path = tmp_path / 'meta.jsonl'

        create_or_update_index.fn([record], str(index_path), str(meta_path))

        fake_faiss.write_index.assert_called_once_with(fake_index, str(index_path))
        assert meta_path.exists()
        data = [json.loads(line) for line in meta_path.read_text().splitlines()]
        assert data[0]['id'] == '1'
