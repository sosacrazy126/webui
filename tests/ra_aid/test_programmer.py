import pytest
import pathlib
import os

from ra_aid.tools.programmer import (
    get_aider_executable,
    parse_aider_flags,
    run_programming_task,
)

# Test cases for parse_aider_flags function
test_cases = [
    # Test case format: (input_string, expected_output, test_description)
    (
        "yes-always,dark-mode",
        ["--yes-always", "--dark-mode"],
        "basic comma separated flags without dashes",
    ),
    (
        "--yes-always,--dark-mode",
        ["--yes-always", "--dark-mode"],
        "comma separated flags with dashes",
    ),
    (
        "yes-always, dark-mode",
        ["--yes-always", "--dark-mode"],
        "comma separated flags with space",
    ),
    (
        "--yes-always, --dark-mode",
        ["--yes-always", "--dark-mode"],
        "comma separated flags with dashes and space",
    ),
    ("", [], "empty string"),
    (
        "  yes-always  ,  dark-mode  ",
        ["--yes-always", "--dark-mode"],
        "flags with extra whitespace",
    ),
    ("--yes-always", ["--yes-always"], "single flag with dashes"),
    ("yes-always", ["--yes-always"], "single flag without dashes"),
    # New test cases for flags with values
    (
        "--analytics-log filename.json",
        ["--analytics-log", "filename.json"],
        "flag with value",
    ),
    (
        "--analytics-log filename.json, --model gpt4",
        ["--analytics-log", "filename.json", "--model", "gpt4"],
        "multiple flags with values",
    ),
    (
        "--dark-mode, --analytics-log filename.json",
        ["--dark-mode", "--analytics-log", "filename.json"],
        "mix of simple flags and flags with values",
    ),
    (
        "  --dark-mode  ,  --model  gpt4  ",
        ["--dark-mode", "--model", "gpt4"],
        "flags with values and extra whitespace",
    ),
    (
        "--analytics-log    filename.json",
        ["--analytics-log", "filename.json"],
        "multiple spaces between flag and value",
    ),
    (
        "---dark-mode,----model gpt4",
        ["--dark-mode", "--model", "gpt4"],
        "stripping extra dashes",
    ),
]


@pytest.mark.parametrize("input_flags,expected,description", test_cases)
def test_parse_aider_flags(input_flags, expected, description):
    """Table-driven test for parse_aider_flags function."""
    result = parse_aider_flags(input_flags)
    assert result == expected, f"Failed test case: {description}"


def test_aider_config_flag(mocker):
    """Test that aider config flag is properly included in the command when specified."""
    mock_memory = {
        "config": {"aider_config": "/path/to/config.yml"},
        "related_files": {},
    }
    mocker.patch("ra_aid.tools.programmer._global_memory", mock_memory)
    
    # Mock the aider executable path to avoid filesystem check
    mocker.patch("ra_aid.tools.programmer.get_aider_executable", return_value="/mock/path/to/aider")
    
    # Mock the run_interactive_command to capture the command that would be run
    mock_run = mocker.patch(
        "ra_aid.tools.programmer.run_interactive_command", return_value=(b"", 0)
    )

    run_programming_task.invoke({"instructions": "test instruction"})

    # Verify the command includes the config flag
    called_args, _ = mock_run.call_args
    assert "--config" in called_args[0]
    assert "/path/to/config.yml" in called_args[0]


def test_path_normalization_and_deduplication(mocker, tmp_path):
    """Test path normalization and deduplication in run_programming_task."""
    # Create a temporary test file
    test_file = tmp_path / "test.py"
    test_file.write_text("")
    new_file = tmp_path / "new.py"

    # Mock dependencies
    mocker.patch("ra_aid.tools.programmer._global_memory", {"related_files": {}})
    mocker.patch(
        "ra_aid.tools.programmer.get_aider_executable", return_value="/path/to/aider"
    )
    mock_run = mocker.patch(
        "ra_aid.tools.programmer.run_interactive_command", return_value=(b"", 0)
    )

    # Test duplicate paths
    run_programming_task.invoke(
        {
            "instructions": "test instruction",
            "files": [str(test_file), str(test_file)],  # Same path twice
        }
    )

    # Get the command list passed to run_interactive_command
    cmd_args = mock_run.call_args[0][0]
    # Count occurrences of test_file path in command
    test_file_count = sum(1 for arg in cmd_args if arg == str(test_file))
    assert test_file_count == 1, "Expected exactly one instance of test_file path"

    # Test mixed paths
    run_programming_task.invoke(
        {
            "instructions": "test instruction",
            "files": [str(test_file), str(new_file)],  # Two different paths
        }
    )

    # Get the command list from the second call
    cmd_args = mock_run.call_args[0][0]
    # Verify both paths are present exactly once
    assert (
        sum(1 for arg in cmd_args if arg == str(test_file)) == 1
    ), "Expected one instance of test_file"
    assert (
        sum(1 for arg in cmd_args if arg == str(new_file)) == 1
    ), "Expected one instance of new_file"


def test_get_aider_executable(mocker):
    """Test that the aider executable is correctly located based on the Python executable's path."""
    # Mock the Path.exists method to return True
    mock_exists = mocker.patch("pathlib.Path.exists", return_value=True)
    
    # Mock os.access to return True
    mock_os = mocker.patch("ra_aid.tools.programmer.os")
    mock_os.access.return_value = True
    mock_os.X_OK = 1  # Mock execute permission constant
    
    # Mock sys.executable with a dummy path
    mock_sys = mocker.patch("ra_aid.tools.programmer.sys")
    mock_sys.executable = "/mock/python/bin/python"
    mock_sys.platform = "linux"  # Non-Windows platform
    
    # Call the function
    result = get_aider_executable()
    
    # Check that the result is as expected
    assert result == "/mock/python/bin/aider"
    mock_exists.assert_called_once()
    mock_os.access.assert_called_once()
    
    # Test Windows platform
    mock_sys.platform = "win32"
    mock_exists.reset_mock()
    mock_os.access.reset_mock()
    
    result = get_aider_executable()
    assert result == "/mock/python/bin/aider.exe"
    mock_exists.assert_called_once()
    mock_os.access.assert_called_once()
