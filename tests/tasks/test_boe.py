import pytest
from unittest.mock import patch, MagicMock
from tasks.boe import (
    fetch_index_xml,
    fetch_index_xml_by_date,
    extract_article_ids,
    get_article_metadata,
    fetch_article_text,
)
from tasks.processing import clean_boe_text, split_into_paragraphs
import requests


@patch("tasks.boe.session.get")
def test_fetch_index_xml_success(mock_get):
    mock_response = MagicMock()
    mock_response.text = "<xml>test data</xml>"
    mock_response.headers = {"Content-Type": "application/xml"}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    year, month, day = "2023", "01", "01"
    result = fetch_index_xml.fn(year, month, day)

    mock_get.assert_called_once_with(
        f"https://www.boe.es/datosabiertos/api/boe/sumario/{year}{month}{day}",
        headers={"Accept": "application/xml"},
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once()
    assert result == "<xml>test data</xml>"


@patch("tasks.boe.session.get")
def test_fetch_index_xml_success_with_capture(mock_get, capsys):
    mock_response = MagicMock()
    mock_response.text = "<xml>test data</xml>"
    mock_response.headers = {"Content-Type": "text/xml"}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    year, month, day = "2023", "01", "01"
    result = fetch_index_xml.fn(year, month, day)
    print(f"Resultado de fetch_index_xml: {result}")

    captured = capsys.readouterr()
    assert "<xml>test data</xml>" in captured.out
    mock_get.assert_called_once_with(
        f"https://www.boe.es/datosabiertos/api/boe/sumario/{year}{month}{day}",
        headers={"Accept": "application/xml"},
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once()
    assert result == "<xml>test data</xml>"


@patch("tasks.boe.session.get")
def test_fetch_index_xml_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/xml"}
    mock_response.raise_for_status = MagicMock(
        side_effect=requests.exceptions.HTTPError("Test HTTP Error")
    )
    mock_get.return_value = mock_response

    year, month, day = "2023", "01", "01"
    with pytest.raises(requests.exceptions.HTTPError, match="Test HTTP Error"):
        fetch_index_xml.fn(
            year, month, day
        )  # Use padded values for consistency in test

    mock_get.assert_called_once_with(
        f"https://www.boe.es/datosabiertos/api/boe/sumario/{year}{month}{day}",
        headers={"Accept": "application/xml"},
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once()


@patch("tasks.boe.session.get")
def test_fetch_index_xml_invalid_content_type(mock_get):
    mock_response = MagicMock()
    mock_response.text = "<html>Not XML</html>"
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Response is not XML"):
        fetch_index_xml.fn("2023", "01", "01")

    mock_get.assert_called_once()


def test_extract_article_ids(capsys):
    sample_xml_content = """
    <document>
        <item id="BOE-A-2023-12345"/>
        <item id="BOE-E-2023-00123"/>
        <item attr="BOE-C-2023-67890"/>
        <other attr="BOE-A-2024-11111"/>
        <item id="BOE-A-2023-12345"/>
        <text>BOE-A-9999-99999</text>
    </document>
    """
    expected_ids = [
        "BOE-A-2023-12345",
        "BOE-E-2023-00123",
        "BOE-C-2023-67890",
        "BOE-A-2024-11111",
        "BOE-A-9999-99999",
    ]
    result = extract_article_ids.fn(sample_xml_content)
    print(f"Resultado de extract_article_ids: {result}")
    # Sorting because set does not guarantee order
    assert sorted(result) == sorted(expected_ids)
    captured = capsys.readouterr()
    assert "BOE-A-2023-12345" in captured.out
    assert "BOE-C-2023-67890" in captured.out


def test_extract_article_ids_no_matches(capsys):
    sample_xml_content = """
    <document>
        <text>OTHER-2025-00001</text>
        <other attr='OTHER-2025-00002'/>
    </document>
    """
    result = extract_article_ids.fn(sample_xml_content)
    print(f"Resultado de extract_article_ids_no_matches: {result}")
    assert result == []
    captured = capsys.readouterr()
    assert "[]" in captured.out


def test_get_article_metadata(capsys):
    boe_id = "BOE-A-2023-12345"
    date_str = "2023-01-01"  # YYYY-MM-DD
    year, month, day = date_str.split("-")
    expected_metadata = {
        "id": boe_id,
        "date": date_str,  # Original date string
        "url_xml": f"https://www.boe.es/diario_boe/xml.php?id={boe_id}",
        "url_pdf": f"https://www.boe.es/boe/dias/{year}/{month}/{day}/pdfs/{boe_id}.pdf",  # Uses parsed components
    }
    result = get_article_metadata.fn(boe_id, date_str)
    print(f"Resultado de get_article_metadata: {result}")
    assert result == expected_metadata
    captured = capsys.readouterr()
    assert boe_id in captured.out
    assert date_str in captured.out


@patch("tasks.boe.fetch_index_xml.fn")
def test_fetch_index_xml_by_date_success(mock_fetch):
    mock_fetch.return_value = "<xml>test data</xml>"

    date_str = "2025-06-28"
    result = fetch_index_xml_by_date.fn(date_str)

    mock_fetch.assert_called_once_with("2025", "06", "28")
    assert result == "<xml>test data</xml>"


def test_fetch_index_xml_by_date_invalid():
    with pytest.raises(ValueError):
        fetch_index_xml_by_date.fn("202506")


@patch("tasks.boe.session.get")
def test_fetch_article_text_success(mock_get):
    sample_xml = """
    <documento>
        <titulo>Titulo de prueba</titulo>
        <departamento>Departamento X</departamento>
        <rango>Orden</rango>
        <texto>Cuerpo del texto</texto>
    </documento>
    """
    mock_response = MagicMock()
    mock_response.text = sample_xml
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    url = "http://example.com/test.xml"
    metadata, segments = fetch_article_text.fn(url)

    mock_get.assert_called_once_with(url, timeout=10)
    mock_response.raise_for_status.assert_called_once()
    assert metadata == {
        "title": "Titulo de prueba",
        "department": "Departamento X",
        "rank": "Orden",
    }
    assert segments == ["Cuerpo del texto"]


@patch("tasks.boe.session.get")
def test_fetch_article_text_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=requests.exceptions.HTTPError("Network Error")
    )
    mock_get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError, match="Network Error"):
        fetch_article_text.fn("http://example.com/test.xml")

    mock_get.assert_called_once_with("http://example.com/test.xml", timeout=10)
    mock_response.raise_for_status.assert_called_once()


def test_clean_boe_text():
    raw = "  Hola\nMundo\t"
    assert clean_boe_text(raw) == "Hola\nMundo"


def test_split_into_paragraphs():
    text = "Uno\n\nDos\nTres\n"
    assert split_into_paragraphs(text) == ["Uno", "Dos", "Tres"]


def test_parse_article_xml_segments():
    xml = """
    <documento>
        <titulo>Titulo</titulo>
        <departamento>Depto</departamento>
        <rango>Orden</rango>
        <texto>Linea 1\n\nLinea 2</texto>
    </documento>
    """
    from tasks.boe import parse_article_xml

    result = parse_article_xml.fn(xml)
    assert result["segments"] == ["Linea 1", "Linea 2"]
