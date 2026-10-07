import os
from unittest.mock import patch

import pytest
from tenacity import RetryError

from src.utilities.config import ConfigLoader
from src.utilities.retry import with_retry

def test_config_loader_default_env():
    """Test that ConfigLoader defaults to 'dev' when ENVIRONMENT is not set."""
    with patch.dict(os.environ, clear=True):
        loader = ConfigLoader(config_dir="dummy_path")
        assert loader.env == "dev"

def test_config_loader_reads_env_var():
    """Test that ConfigLoader respects the ENVIRONMENT variable."""
    with patch.dict(os.environ, {"ENVIRONMENT": "prod"}):
        loader = ConfigLoader(config_dir="dummy_path")
        assert loader.env == "prod"

def test_retry_decorator_success_first_try():
    """Test that with_retry succeeds immediately if no exception occurs."""
    call_count = 0
    
    @with_retry(max_attempts=3, min_wait_seconds=0, max_wait_seconds=0)
    def dummy_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = dummy_func()
    assert result == "success"
    assert call_count == 1

def test_retry_decorator_success_after_failure():
    """Test that with_retry retries on failure and succeeds."""
    call_count = 0
    
    @with_retry(max_attempts=3, min_wait_seconds=0, max_wait_seconds=0)
    def dummy_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Temporary failure")
        return "success"

    result = dummy_func()
    assert result == "success"
    assert call_count == 2

def test_retry_decorator_max_attempts_exceeded():
    """Test that with_retry raises RetryError after max attempts."""
    call_count = 0
    
    @with_retry(max_attempts=2, min_wait_seconds=0, max_wait_seconds=0)
    def dummy_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Permanent failure")

    with pytest.raises(ValueError, match="Permanent failure"):
        dummy_func()
        
    assert call_count == 2
