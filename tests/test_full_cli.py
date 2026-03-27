import pytest
from unittest.mock import patch, MagicMock
import argparse
import sys
import garmin_tools
from datetime import date

# ==============================================================================
# CLI Testing Fixtures
# ==============================================================================

@pytest.fixture
def mock_all_clients():
    """Mock all clients and handlers to prevent real network calls."""
    # We patch them in the core.commands and core.utils where garmin_tools imports them from,
    # OR better, patch them in garmin_tools directly if they were imported via 'from ... import ...'
    with patch('client.activity_client.ActivityClient'), \
         patch('client.workout_client.WorkoutClient'), \
         patch('client.health_client.HealthClient'), \
         patch('client.sleep_client.SleepClient'), \
         patch('client.body_battery_client.BodyBatteryClient'), \
         patch('client.vo2max_client.Vo2MaxClient'), \
         patch('client.max_hr_client.MaxHrClient'), \
         patch('client.race_event_client.RaceEventClient'), \
         patch('client.weight_client.WeightClient'), \
         patch('client.hrv_client.HrvClient'), \
         patch('garmin_tools.resolve_user_auth', return_value=("user", "pass"), create=True), \
         patch('garmin_tools.configure_runtime_logger'):
        yield

# ==============================================================================
# Global Options Tests
# ==============================================================================

def test_global_options(mock_all_clients):
    """測試全域選項: --verbosity, --progress, --over-write, --env-file, --session"""
    mock_activity_handler = MagicMock()
    with patch('garmin_tools.COMMAND_HANDLERS', {'activity': mock_activity_handler}):
        # Add an extra argument to avoid the "smart help" (which triggers if subcommand is the last arg)
        test_args = [
            "garmin_tools.py", "-vv", "--progress", "--over-write", 
            "--env-file", "custom.env", "-ss", "./custom_session",
            "activity", "-c", "5"
        ]
        with patch('sys.argv', test_args):
            garmin_tools.main()
            args = mock_activity_handler.call_args[0][0]
            assert args.verbosity == 2
            assert args.progress is True
            assert args.over_write is True
            assert args.env_file == "custom.env"
            assert args.session == "./custom_session"

# ==============================================================================
# Subcommand & Option Tests
# ==============================================================================

def test_activity_all_options(mock_all_clients):
    """測試 activity 子命令的所有選項"""
    with patch('garmin_tools.execute_activity_export') as mock_handler:
        # Re-patch COMMAND_HANDLERS to use our mock_handler
        with patch('garmin_tools.COMMAND_HANDLERS', {'activity': mock_handler}):
            test_args = [
                "garmin_tools.py", "activity", 
                "-c", "all", "-sd", "2023-01-01", "-ed", "2023-01-31", 
                "-f", "tcx", "--directory", "./downloads", "-ot", "--desc", "20"
            ]
            with patch('sys.argv', test_args):
                garmin_tools.main()
                assert mock_handler.called
                args = mock_handler.call_args[0][0]
                assert args.count == "all"
                assert args.start_date == "2023-01-01"
                assert args.end_date == "2023-01-31"
                assert args.format == "tcx"
                assert args.directory == "./downloads"
                assert args.originaltime is True
                assert args.desc == "20"

def test_workout_all_subcommands(mock_all_clients):
    """測試 workout 所有子指令 (list, get, upload, delete)"""
    with patch('garmin_tools.manage_workout_workflow') as mock_handler:
        with patch('garmin_tools.COMMAND_HANDLERS', {'workout': mock_handler}):
            # list
            with patch('sys.argv', ["garmin_tools.py", "workout", "list"]):
                garmin_tools.main()
                assert mock_handler.call_args[0][0].workout_command == "list"
            # get
            with patch('sys.argv', ["garmin_tools.py", "workout", "get", "999", "-o", "test.yaml"]):
                garmin_tools.main()
                args = mock_handler.call_args[0][0]
                assert args.workout_command == "get"
                assert args.id == "999"
                assert args.output == "test.yaml"
            # upload
            with patch('sys.argv', ["garmin_tools.py", "workout", "upload", "src.yaml"]):
                garmin_tools.main()
                args = mock_handler.call_args[0][0]
                assert args.workout_command == "upload"
                assert args.file == "src.yaml"
            # delete
            with patch('sys.argv', ["garmin_tools.py", "workout", "delete", "888"]):
                garmin_tools.main()
                args = mock_handler.call_args[0][0]
                assert args.workout_command == "delete"
                assert args.id == "888"

def test_health_metrics_dispatch(mock_all_clients):
    """測試所有健康/生理數據子命令的分發 (透過 health 父命令)"""
    metrics = [
        "health", "sleep", "body-battery", "vo2max", 
        "hrv", "weight", "max-hr", "stress"
    ]
    
    with patch('garmin_tools.process_health_command') as mock_handler:
        with patch('garmin_tools.COMMAND_HANDLERS', {'health': mock_handler}):
            for metric in metrics:
                test_args = ["garmin_tools.py", "health", metric, "--summary"]
                with patch('sys.argv', test_args):
                    garmin_tools.main()
                    assert mock_handler.called
                    args = mock_handler.call_args[0][0]
                    assert args.command == "health"
                    assert args.health_command == metric
                    assert args.summary is True

def test_hrv_detailed_flag(mock_all_clients):
    """測試 hrv 的 --detailed 選項"""
    with patch('garmin_tools.process_health_command') as mock_handler:
        with patch('garmin_tools.COMMAND_HANDLERS', {'health': mock_handler}):
            with patch('sys.argv', ["garmin_tools.py", "health", "hrv", "--detailed"]):
                garmin_tools.main()
                assert mock_handler.call_args[0][0].detailed is True

def test_weight_upload_value(mock_all_clients):
    """測試 weight 的 --upload 選項"""
    with patch('garmin_tools.process_health_command') as mock_handler:
        with patch('garmin_tools.COMMAND_HANDLERS', {'health': mock_handler}):
            with patch('sys.argv', ["garmin_tools.py", "health", "weight", "--upload", "80.0"]):
                garmin_tools.main()
                assert mock_handler.call_args[0][0].upload == 80.0

def test_max_hr_limit_value(mock_all_clients):
    """測試 max-hr 的 --limit 選項"""
    with patch('garmin_tools.process_health_command') as mock_handler:
        with patch('garmin_tools.COMMAND_HANDLERS', {'health': mock_handler}):
            with patch('sys.argv', ["garmin_tools.py", "health", "max-hr", "-l", "3"]):
                garmin_tools.main()
                assert mock_handler.call_args[0][0].limit == 3
