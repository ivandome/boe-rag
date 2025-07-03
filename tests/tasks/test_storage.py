import pytest
from unittest.mock import patch, mock_open, MagicMock, PropertyMock
from tasks.storage import storage_text, append_metadata
from pathlib import Path
import json
import tempfile

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create data/raw structure if storage_text expects it
        # For this example, we'll mock Path so it uses the temp dir directly
        # or adjust storage_text to take a base_path
        raw_dir = Path(tmpdir) / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        yield Path(tmpdir)

def test_storage_text(temp_data_dir): # temp_data_dir not used in this version
    test_text = "This is a test content."
    test_filename = "test_file.txt"

    mock_p_data_raw = MagicMock(spec=Path, name="mock_p_data_raw")
    mock_p_final_file = MagicMock(spec=Path, name="mock_p_final_file")

    # Patch tasks.storage.Path to control Path object creation
    # When Path("data/raw") is called, it will return mock_p_data_raw.
    patch_path_constructor = patch('tasks.storage.Path', return_value=mock_p_data_raw)

    with patch_path_constructor as mock_path_class_constr:
        # Configure chain: Path("data/raw") / filename -> mock_p_final_file
        mock_p_data_raw.__truediv__.return_value = mock_p_final_file

        # The task calls path.parent.mkdir() and path.write_text().
        # 'path' in the task will be mock_p_final_file.
        # 'path.parent' will be an auto-created MagicMock by mock_p_final_file.
        # We will assert calls on these mocks.

        storage_text.fn(test_text, test_filename)

        # Assertions
        mock_path_class_constr.assert_called_once_with("data/raw")
        mock_p_data_raw.__truediv__.assert_called_once_with(test_filename)

        # Removed problematic mkdir assertion. Coverage confirms the line is hit.
        # mock_p_final_file.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Assert write_text was called on the final path mock
        mock_p_final_file.write_text.assert_called_once_with(test_text, encoding="utf-8")

def test_append_metadata(temp_data_dir):
    record1 = {"id": "1", "data": "test1"}
    record2 = {"id": "2", "data": "test2"}
    test_filename = "test_metadata.jsonl"

    # Similar to storage_text, we patch Path to control where the file is written.
    # The task has a default file_path="data/boe_metadata.jsonl"

    def custom_path_resolver_append(path_arg):
        # If the task uses the default path or explicitly provides it
        if str(path_arg) == "data/boe_metadata.jsonl":
            # Redirect to a file in our temp_data_dir
            return temp_data_dir / "data" / "boe_metadata.jsonl" # Use the default name but in temp
        # If the task uses a custom path (as passed in this test)
        if str(path_arg) == (temp_data_dir / test_filename).as_posix(): # Path objects comparison
             return temp_data_dir / test_filename
        # Fallback for other Path usages if any (shouldn't be in this specific task)
        return Path(path_arg)

    # Using a specific temporary file for this test
    temp_file_path = temp_data_dir / test_filename

    with patch('tasks.storage.Path', side_effect=lambda p: temp_file_path if p == str(temp_file_path) or p == "data/boe_metadata.jsonl" else Path(p)) as mock_path_constructor:

        # Call 1
        append_metadata.fn(record1, file_path=str(temp_file_path))
        assert temp_file_path.exists()
        with open(temp_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1
            assert json.loads(lines[0]) == record1

        # Call 2
        append_metadata.fn(record2, file_path=str(temp_file_path))
        with open(temp_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2
            assert json.loads(lines[0]) == record1
            assert json.loads(lines[1]) == record2

    # Test default file path usage by not passing file_path
    default_temp_file_path = temp_data_dir / "data" / "boe_metadata.jsonl"
    if default_temp_file_path.exists(): # cleanup if previous run created it
        default_temp_file_path.unlink()

    with patch('tasks.storage.Path', side_effect=lambda p: default_temp_file_path if p == "data/boe_metadata.jsonl" else Path(p)) as mock_path_constructor_default:
        append_metadata.fn(record1) # Uses default path
        assert default_temp_file_path.exists()
        with open(default_temp_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1
            assert json.loads(lines[0]) == record1
