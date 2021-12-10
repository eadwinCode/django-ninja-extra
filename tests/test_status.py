from ninja_extra.status import (
    is_client_error,
    is_informational,
    is_redirect,
    is_server_error,
    is_success,
)


class TestStatus:
    def test_status_categories(self):
        assert is_informational(99) is False
        assert is_informational(100) is True
        assert is_informational(199) is True
        assert is_informational(200) is False

        assert is_success(199) is False
        assert is_success(200) is True
        assert is_success(299) is True
        assert is_success(300) is False

        assert is_redirect(299) is False
        assert is_redirect(300) is True
        assert is_redirect(399) is True
        assert is_redirect(400) is False

        assert is_client_error(399) is False
        assert is_client_error(400) is True
        assert is_client_error(499) is True
        assert is_client_error(500) is False

        assert is_server_error(499) is False
        assert is_server_error(500) is True
        assert is_server_error(599) is True
        assert is_server_error(600) is False
