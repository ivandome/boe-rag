import pytest
from unittest.mock import patch, MagicMock
from tasks.scraping import scrape_example_page
import requests

@patch('tasks.scraping.session.get')
def test_scrape_example_page_success(mock_get):
    mock_response = MagicMock()
    mock_response.text = "<html><head><title>Test Page</title></head><body><p>Hello World!</p></body></html>"
    mock_get.return_value = mock_response

    url = "http://example.com"
    result = scrape_example_page.fn(url)

    mock_get.assert_called_once_with(url, timeout=10)
    assert "Hello World!" in result
    assert "Test Page" in result # Title is also text

@patch('tasks.scraping.session.get')
def test_scrape_example_page_http_error(mock_get):
    mock_response = MagicMock()
    # It's good practice to ensure your mock raises an error if the code is expected to handle it.
    # However, scrape_example_page currently doesn't explicitly call raise_for_status().
    # If it did, this test would be more robust.
    # For now, we'll assume requests.get itself might raise or return a bad status.
    # Let's simulate a requests.exceptions.RequestException for a more general network issue.
    mock_get.side_effect = requests.exceptions.RequestException("Test Network Error")

    url = "http://example.com"
    with pytest.raises(requests.exceptions.RequestException, match="Test Network Error"):
        scrape_example_page.fn(url)

    mock_get.assert_called_once_with(url, timeout=10)
