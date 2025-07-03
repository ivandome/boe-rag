import pytest
from unittest.mock import patch
from flows.scrape_and_store import scrape_and_store

from prefect.testing.utilities import prefect_test_harness

@patch('flows.scrape_and_store.scrape_example_page')
@patch('flows.scrape_and_store.storage_text')
def test_scrape_and_store_flow(mock_storage_text, mock_scrape_example_page):
    # Configure mocks
    mock_scrape_example_page.return_value = "Test content"

    test_url = "http://example.com"
    test_filename = "test.txt"

    # Using Prefect's test harness for flow execution if needed,
    # or directly calling the flow function for simpler cases.
    # For this flow, direct call is fine as it's simple.
    # If it were a deployment or had more complex Prefect features, harness would be better.

    scrape_and_store.fn(url=test_url, filename=test_filename) # .fn to call the original function

    # Assert that the mocked tasks were called correctly
    mock_scrape_example_page.assert_called_once_with(test_url)
    mock_storage_text.assert_called_once_with("Test content", test_filename)

# Example of using prefect_test_harness if the flow had subflows or needed state checks
# @patch('flows.scrape_and_store.scrape_example_page')
# @patch('flows.scrape_and_store.storage_text')
# def test_scrape_and_store_flow_with_harness(mock_storage_text, mock_scrape_example_page):
#     mock_scrape_example_page.return_value = "Test content from harness"
#     test_url = "http://harness-example.com"
#     test_filename = "harness_test.txt"

#     with prefect_test_harness():
#         # Run the flow, e.g. as a deployment or by direct invocation
#         # This allows Prefect to manage states and results if you need to inspect them.
#         result = scrape_and_store.serve(
#             name="test-deployment",
#             parameters={"url": test_url, "filename": test_filename}
#         )
#         # Or simpler:
#         # scrape_and_store(url=test_url, filename=test_filename)
#         # For this flow, the direct .fn call as above is sufficient.

#     mock_scrape_example_page.assert_called_once_with(test_url)
#     mock_storage_text.assert_called_once_with("Test content from harness", test_filename)
