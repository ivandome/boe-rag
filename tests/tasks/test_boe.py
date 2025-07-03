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

    fecha = "2023-01-01"
    result = fetch_index_xml.fn(fecha)

    mock_get.assert_called_once_with(f"https://www.boe.es/diario_boe/xml.php?fecha={fecha}")
    mock_response.raise_for_status.assert_called_once()
    assert result == "<xml>test data</xml>"

@patch('tasks.boe.requests.get')
def test_fetch_index_xml_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(side_effect=requests.exceptions.HTTPError("Test HTTP Error"))
    mock_get.return_value = mock_response

    fecha = "2023-01-01"
    with pytest.raises(requests.exceptions.HTTPError, match="Test HTTP Error"):
        fetch_index_xml.fn(fecha)

    mock_get.assert_called_once_with(f"https://www.boe.es/diario_boe/xml.php?fecha={fecha}")
    mock_response.raise_for_status.assert_called_once()

def test_extract_article_ids():
    sample_xml_content = """
    <document>
        <item id="BOE-A-2023-12345"/>
        <item id="BOE-S-2023-00123"/>
        <item id="BOE-A-2023-67890"/>
        <item id="BOE-A-2023-12345"/>
    </document>
    """
    expected_ids = ["BOE-A-2023-12345", "BOE-A-2023-67890"]
    # Sorting because set does not guarantee order
    assert sorted(extract_article_ids.fn(sample_xml_content)) == sorted(expected_ids)

def test_extract_article_ids_no_matches():
    sample_xml_content = "<document><item id='OTHER-ID-123'/></document>"
    assert extract_article_ids.fn(sample_xml_content) == []

def test_get_article_metadata():
    boe_id = "BOE-A-2023-12345"
    fecha = "2023-01-01"
    expected_metadata = {
        "id": boe_id,
        "fecha": fecha,
        "url_xml": f"https://www.boe.es/diario_boe/xml.php?id={boe_id}",
        "url_pdf": f"https://www.boe.es/boe/dias/{fecha}/pdfs/{boe_id}.pdf"
    }
    assert get_article_metadata.fn(boe_id, fecha) == expected_metadata
