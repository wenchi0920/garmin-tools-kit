#!/usr/bin/env python3
"""
Purpose: Garmin Tool Kit 深層模擬整合測試 (Mock Integrated Test) - v2
Author: Gemini CLI
"""
import unittest
from unittest.mock import MagicMock, patch
import argparse
import os
import sys
import json
from datetime import date

# 匯入要測試的模組
import garmin_tools
import core.commands as commands

class TestGarminToolsIntegrated(unittest.TestCase):

    def setUp(self):
        # 建立基本的 args
        self.base_args = argparse.Namespace(
            verbosity=0,
            username="test@example.com",
            password="password",
            env_file=None,
            session=".garth",
            over_write=True,
            progress=False,
            gui=False,
            date=date.today().isoformat(),
            start_date=None,
            end_date=None,
            summary=False,
            output=None
        )

    def run_handler_test(self, handler_func, args, mock_client_cls):
        """通用測試邏輯"""
        mock_client = mock_client_cls.return_value
        with patch('builtins.open', unittest.mock.mock_open()):
            with patch('os.path.exists', return_value=False):
                handler_func(args)
        return mock_client

    @patch('core.commands.ActivityClient')
    def test_activity(self, mock_cls):
        args = self.base_args
        args.command = "activity"
        args.count = "1"
        args.format = "original"
        args.directory = "data/activity"
        args.originaltime = False
        args.desc = None
        
        mock_client = mock_cls.return_value
        mock_client.list_activities.return_value = [{"activityId": "123", "startTimeLocal": "2026-03-12 10:00", "startTimeGMT": "2026-03-12 02:00"}]
        
        commands.execute_activity_export(args)
        mock_client.list_activities.assert_called_once()
        print("SUCCESS: Activity verified.")

    @patch('client.health_client.HealthClient')
    def test_health(self, mock_cls):
        args = self.base_args
        args.command = "health"
        mock_client = mock_cls.return_value
        mock_data = MagicMock()
        mock_data.model_dump.return_value = {"calendarDate": "2026-03-12", "totalSteps": 1000}
        mock_client.get_daily_summary.return_value = mock_data
        
        self.run_handler_test(commands.fetch_daily_health_metrics, args, mock_cls)
        print("SUCCESS: Health verified.")

    @patch('client.sleep_client.SleepClient')
    def test_sleep(self, mock_cls):
        args = self.base_args
        args.command = "sleep"
        mock_client = mock_cls.return_value
        mock_data = MagicMock()
        mock_data.model_dump.return_value = {"dailySleepDTO": {"calendarDate": "2026-03-12"}}
        mock_client.get_sleep_data.return_value = mock_data
        
        self.run_handler_test(commands.fetch_sleep_analytics, args, mock_cls)
        print("SUCCESS: Sleep verified.")

    @patch('client.body_battery_client.BodyBatteryClient')
    def test_body_battery(self, mock_cls):
        args = self.base_args
        args.command = "body-battery"
        mock_client = mock_cls.return_value
        mock_data = MagicMock()
        mock_data.model_dump.return_value = {"calendarDate": "2026-03-12", "charged": 50}
        mock_client.get_body_battery_report.return_value = mock_data
        
        self.run_handler_test(commands.analyze_body_battery, args, mock_cls)
        print("SUCCESS: Body Battery verified.")

    @patch('client.vo2max_client.Vo2MaxClient')
    def test_vo2max(self, mock_cls):
        args = self.base_args
        args.command = "vo2max"
        mock_client = mock_cls.return_value
        mock_client.get_vo2max_history.return_value = []
        mock_client.get_training_status.return_value = None
        
        self.run_handler_test(commands.evaluate_vo2max_trends, args, mock_cls)
        print("SUCCESS: VO2 Max verified.")


    @patch('client.client.Client.login', return_value=True)
    @patch('client.race_event_client.RaceEventClient')
    def test_race_event(self, mock_cls, mock_client_login):
        args = self.base_args
        args.command = "race-event"
        mock_client = mock_cls.return_value
        mock_client.list_events.return_value = [{"id": 1, "eventName": "Test Race", "date": "2026-03-27"}]


        
        self.run_handler_test(commands.fetch_race_calendar, args, mock_cls)
        print("SUCCESS: Race Event verified.")

    @patch('client.max_hr_client.MaxHrClient')
    def test_max_hr(self, mock_cls):
        args = self.base_args
        args.command = "max-hr"
        args.limit = 5
        mock_client = mock_cls.return_value
        mock_client.get_daily_hr_metrics.return_value = None
        mock_client.get_recent_activity_max_hr.return_value = []
        
        self.run_handler_test(commands.report_heart_rate_indicators, args, mock_cls)
        print("SUCCESS: Max-HR verified.")

    @patch('core.commands.WorkoutClient')
    def test_workout_list(self, mock_cls):
        args = self.base_args
        args.command = "workout"
        args.workout_command = "list"
        mock_client = mock_cls.return_value
        mock_client.list_workouts.return_value = []
        
        commands.manage_workout_workflow(args)
        mock_client.list_workouts.assert_called_once()
        print("SUCCESS: Workout List verified.")

if __name__ == '__main__':
    unittest.main()
