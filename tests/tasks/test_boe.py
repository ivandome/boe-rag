import pytest
from unittest.mock import patch, MagicMock
from tasks.boe import fetch_index_xml, extract_article_ids, get_article_metadata
import requests

@patch('tasks.boe.requests.get')
def test_fetch_index_xml_success(mock_get):
    mock_response = MagicMock()
    mock_response.text = "<xml>test data</xml>"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    year, month, day = "2023", "01", "01"
    # Test with unpadded month/day as well, assuming zfill in main code handles it
    result = fetch_index_xml.fn(year, "1", "1")

    mock_get.assert_called_once_with(f"https://www.boe.es/datosabiertos/api/boe/sumario/{year}{month}{day}")
    mock_response.raise_for_status.assert_called_once()
    assert result == "<xml>test data</xml>"

@patch('tasks.boe.requests.get')
def test_fetch_index_xml_success_with_capture(mock_get, capsys):
    mock_response = MagicMock()
    mock_response.text = "<xml>test data</xml>"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    fecha = "2023-01-01"
    result = fetch_index_xml.fn(fecha)
    print(f"Resultado de fetch_index_xml: {result}")

    captured = capsys.readouterr()
    assert "<xml>test data</xml>" in captured.out
    mock_get.assert_called_once_with(f"https://www.boe.es/diario_boe/xml.php?fecha={fecha}")
    mock_response.raise_for_status.assert_called_once()
    assert result == "<xml>test data</xml>"

@patch('tasks.boe.requests.get')
def test_fetch_index_xml_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(side_effect=requests.exceptions.HTTPError("Test HTTP Error"))
    mock_get.return_value = mock_response

    year, month, day = "2023", "01", "01"
    with pytest.raises(requests.exceptions.HTTPError, match="Test HTTP Error"):
        fetch_index_xml.fn(year, month, day) # Use padded values for consistency in test

    mock_get.assert_called_once_with(f"https://www.boe.es/datosabiertos/api/boe/sumario/{year}{month}{day}")
    mock_response.raise_for_status.assert_called_once()

def test_extract_article_ids(capsys):
    sample_xml_content = """
    <document>
        <item id="BOE-A-2023-12345"/>
        <item id="BOE-S-2023-00123"/>
        <item id="BOE-A-2023-67890"/>
        <item id="BOE-A-2023-12345"/>
    </document>
    """
    expected_ids = ["BOE-A-2023-12345", "BOE-A-2023-67890"]
    result = extract_article_ids.fn(sample_xml_content)
    print(f"Resultado de extract_article_ids: {result}")
    # Sorting because set does not guarantee order
    assert sorted(result) == sorted(expected_ids)
    captured = capsys.readouterr()
    assert "BOE-A-2023-12345" in captured.out
    assert "BOE-A-2023-67890" in captured.out


def test_extract_article_ids_no_matches(capsys):
    sample_xml_content = "<document><item id='OTHER-ID-123'/></document>"
    result = extract_article_ids.fn(sample_xml_content)
    print(f"Resultado de extract_article_ids_no_matches: {result}")
    assert result == []
    captured = capsys.readouterr()
    assert "[]" in captured.out

def test_get_article_metadata(capsys):
    boe_id = "BOE-A-2023-12345"
    fecha = "2023-01-01" # YYYY-MM-DD
    year, month, day = fecha.split('-')
    expected_metadata = {
        "id": boe_id,
        "fecha": fecha, # This is the original fecha string
        "url_xml": f"https://www.boe.es/diario_boe/xml.php?id={boe_id}",
        "url_pdf": f"https://www.boe.es/boe/dias/{year}/{month}/{day}/pdfs/{boe_id}.pdf" # Uses parsed components
    }
    result = get_article_metadata.fn(boe_id, fecha)
    print(f"Resultado de get_article_metadata: {result}")
    assert result == expected_metadata
    captured = capsys.readouterr()
    assert boe_id in captured.out
    assert fecha in captured.out
