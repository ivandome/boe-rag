from unittest.mock import patch
from flows.index_articles import index_articles


@patch("flows.index_articles.init_db")
@patch("flows.index_articles.fetch_all_articles")
@patch("flows.index_articles.create_or_update_index")
def test_index_articles_flow(mock_create_or_update_index, mock_fetch_all_articles, mock_init_db):
    sample_records = [{"id": "1", "title": "t", "text": "x"}]
    mock_fetch_all_articles.return_value = sample_records

    index_articles.fn(db_path="test.db")

    mock_init_db.assert_called_once_with("test.db")
    mock_fetch_all_articles.assert_called_once_with("test.db")
    mock_create_or_update_index.assert_called_once_with(sample_records)
