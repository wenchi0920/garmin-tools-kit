import os
import argparse
from unittest.mock import patch
import pytest
import sys

# Ensure we can import garmin_tools
sys.path.append(".")
from core.utils import resolve_user_auth, load_env_file

def test_load_env_file(tmp_path):
    env_file = tmp_path / ".env.test"
    env_file.write_text("GARMIN_USERNAME=test@user.com\nGARMIN_PASSWORD=secret_pass")
    
    data = load_env_file(str(env_file))
    assert data["GARMIN_USERNAME"] == "test@user.com"
    assert data["GARMIN_PASSWORD"] == "secret_pass"

def test_resolve_user_auth_from_args():
    args = argparse.Namespace(
        username="cli_user",
        password="cli_password",
        env_file=None
    )
    # Mock os.path.exists to return False for .env to avoid loading real secrets
    with patch('os.path.exists', return_value=False):
        with patch('os.environ', {}):
            user, pwd = resolve_user_auth(args)
            assert user == "cli_user"
            assert pwd == "cli_password"

def test_resolve_user_auth_from_env():
    args = argparse.Namespace(
        username=None,
        password=None,
        env_file=None
    )
    # Mock os.path.exists to return False for .env
    with patch('os.path.exists', return_value=False):
        with patch.dict('os.environ', {"GARMIN_USERNAME": "env_user", "GARMIN_PASSWORD": "env_password"}):
            user, pwd = resolve_user_auth(args)
            assert user == "env_user"
            assert pwd == "env_password"
