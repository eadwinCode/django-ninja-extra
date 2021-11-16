from functools import wraps
from unittest.mock import patch


def mock_signal_call(signal: str, called: bool = True):
    def _wrap(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            with patch(f"ninja_extra.signals.{signal}.send") as mock_:
                func(*args, **kwargs)
                assert mock_.called == called

        return _wrapper

    return _wrap
