"""
Unit tests for Windows Credential Manager integration.
Uses mock keyring backend to ensure zero impact on real credentials during tests.
"""

from unittest.mock import patch
import pytest
from app.security import credentials


@pytest.fixture
def mock_keyring():
    """In-memory dictionary simulating Windows Credential Manager."""
    vault = {}

    def get_pwd(service, username):
        return vault.get((service, username))

    def set_pwd(service, username, password):
        vault[(service, username)] = password

    def del_pwd(service, username):
        if (service, username) in vault:
            del vault[(service, username)]
        else:
            import keyring
            raise keyring.errors.PasswordDeleteError("Not found")

    with patch("keyring.get_password", side_effect=get_pwd), \
         patch("keyring.set_password", side_effect=set_pwd), \
         patch("keyring.delete_password", side_effect=del_pwd):
        yield vault


def test_save_and_retrieve_credentials(mock_keyring):
    assert not credentials.has_credentials()

    success = credentials.save_credentials("test_user", "SecurePass@123")
    assert success is True
    assert credentials.has_credentials() is True

    creds = credentials.get_saved_credentials()
    assert creds is not None
    assert creds[0] == "test_user"
    assert creds[1] == "SecurePass@123"


def test_reject_empty_credentials(mock_keyring):
    assert credentials.save_credentials("", "password") is False
    assert credentials.save_credentials("user", "") is False
    assert not credentials.has_credentials()


def test_delete_credentials(mock_keyring):
    credentials.save_credentials("test_user", "Secret")
    assert credentials.has_credentials() is True

    deleted = credentials.delete_credentials()
    assert deleted is True
    assert not credentials.has_credentials()
    assert credentials.get_saved_credentials() is None
