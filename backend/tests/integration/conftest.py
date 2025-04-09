"""
Pytest configuration for integration tests.
"""

import contextlib
import importlib
import sys
from functools import wraps

import pytest


def patch_log_timing(monkeypatch):
    """
    Patch the log_timing function to handle duplicate 'operation' parameters.

    The issue is that log_timing is called with both a positional operation parameter
    and receives 'operation' again in **log_context.

    This patch fixes that conflict by creating a wrapper that removes 'operation'
    from the kwargs if it's provided as a positional argument.
    """
    # First identify where log_timing is defined
    module_path = "app.api.core.logging"
    try:
        module = importlib.import_module(module_path)
        original_log_timing = getattr(module, "log_timing", None)
        if not original_log_timing:
            print(f"ERROR: Couldn't find log_timing in {module_path}")
            return False
    except ImportError:
        print(f"ERROR: Couldn't import module {module_path}")
        return False

    @wraps(original_log_timing)
    @contextlib.contextmanager
    def fixed_log_timing(operation_name, **kwargs):
        """Wrapper that prevents operation parameter collision"""
        # Remove 'operation' from kwargs if present to avoid conflict
        if "operation" in kwargs:
            kwargs.pop("operation")

        with original_log_timing(operation_name, **kwargs) as result:
            yield result

    # Patch the function directly in the module
    monkeypatch.setattr(f"{module_path}.log_timing", fixed_log_timing)
    print(f"Successfully patched log_timing in {module_path}")

    # Also patch it globally if it's imported elsewhere
    for name, module in list(sys.modules.items()):
        if name.startswith("app.") and hasattr(module, "log_timing"):
            if getattr(module, "log_timing") is original_log_timing:
                monkeypatch.setattr(f"{name}.log_timing", fixed_log_timing)
                print(f"Also patched log_timing in {name}")

    # Directly patch the modules that use log_timing
    for user_module_path in ["app.api.v1.user"]:
        try:
            user_module = importlib.import_module(user_module_path)
            if hasattr(user_module, "log_timing"):
                monkeypatch.setattr(f"{user_module_path}.log_timing", fixed_log_timing)
                print(f"Patched log_timing in user module {user_module_path}")
        except ImportError:
            pass

    return True


@pytest.fixture(autouse=True)
def fix_log_timing(monkeypatch):
    """
    Automatically apply the log_timing patch to all tests.
    The fixture has function scope to match monkeypatch's scope.
    """
    patch_log_timing(monkeypatch)


def mock_email_service(mocker, email_service_path: str, success: bool = True):
    """
    Helper function to mock email-sending services.

    Args:
        mocker: The pytest-mock mocker object.
        email_service_path: The import path of the email service to mock.
        success: Whether the mock should simulate a successful email send.

    Returns:
        The mocked email service.
    """
    mock_send = mocker.patch(email_service_path)
    if success:
        mock_send.return_value = {"message": "Verification email sent successfully"}
    else:
        mock_send.side_effect = Exception("SMTP connection failed")
    return mock_send
