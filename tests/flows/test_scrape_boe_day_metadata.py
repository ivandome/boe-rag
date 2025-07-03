import pytest
from unittest.mock import patch
from flows.scrape_boe_day_metadata import scrape_boe_day_metadata

from unittest.mock import call # Import call for checking multiple calls
from prefect.testing.utilities import prefect_test_harness

@patch('flows.scrape_boe_day_metadata.append_metadata')
@patch('flows.scrape_boe_day_metadata.get_article_metadata')
@patch('flows.scrape_boe_day_metadata.extract_article_ids')
@patch('flows.scrape_boe_day_metadata.fetch_index_xml')
def test_scrape_boe_day_metadata_flow(
    mock_fetch_index_xml,
    mock_extract_article_ids,
    mock_get_article_metadata,
    mock_append_metadata
):
    test_url_date_str = "2023/01/01"
    expected_year, expected_month, expected_day = "2023", "01", "01"
    expected_fecha_yyyymmdd = "2023-01-01"


    # Configure mocks
    mock_fetch_index_xml.return_value = "<xml>dummy index</xml>"
    mock_extract_article_ids.return_value = ["ID-1", "ID-2"]

    # Mock metadata returned for each ID
    mock_get_article_metadata.side_effect = [
        {"id": "ID-1", "data": "meta1"},
        {"id": "ID-2", "data": "meta2"}
    ]

    # Call the flow's function directly
    scrape_boe_day_metadata.fn(url_date_str=test_url_date_str)

    # Assertions
    mock_fetch_index_xml.assert_called_once_with(expected_year, expected_month, expected_day)
    mock_extract_article_ids.assert_called_once_with("<xml>dummy index</xml>")

    # Check calls to get_article_metadata
    expected_get_metadata_calls = [
        call("ID-1", expected_fecha_yyyymmdd),
        call("ID-2", expected_fecha_yyyymmdd)
    ]
    mock_get_article_metadata.assert_has_calls(expected_get_metadata_calls, any_order=False)
    assert mock_get_article_metadata.call_count == 2

    # Check calls to append_metadata
    expected_append_calls = [
        call({"id": "ID-1", "data": "meta1"}),
        call({"id": "ID-2", "data": "meta2"})
    ]
    mock_append_metadata.assert_has_calls(expected_append_calls, any_order=False)
    assert mock_append_metadata.call_count == 2

@patch('flows.scrape_boe_day_metadata.append_metadata')
@patch('flows.scrape_boe_day_metadata.get_article_metadata')
@patch('flows.scrape_boe_day_metadata.extract_article_ids')
@patch('flows.scrape_boe_day_metadata.fetch_index_xml')
def test_scrape_boe_day_metadata_flow_no_ids(
    mock_fetch_index_xml,
    mock_extract_article_ids,
    mock_get_article_metadata,
    mock_append_metadata
):
    test_url_date_str = "2023/01/02"
    expected_year, expected_month, expected_day = "2023", "01", "02"
    # expected_fecha_yyyymmdd is not used here as get_article_metadata should not be called

    mock_fetch_index_xml.return_value = "<xml>empty index</xml>"
    mock_extract_article_ids.return_value = [] # No IDs found

    scrape_boe_day_metadata.fn(url_date_str=test_url_date_str)

    mock_fetch_index_xml.assert_called_once_with(expected_year, expected_month, expected_day)
    mock_extract_article_ids.assert_called_once_with("<xml>empty index</xml>")

    # Ensure these were NOT called if no IDs
    mock_get_article_metadata.assert_not_called()
    mock_append_metadata.assert_not_called()
