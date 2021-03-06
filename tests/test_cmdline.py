"""Cmdline tests."""
from pyicloud import cmdline
from . import PyiCloudServiceMock, AUTHENTICATED_USER, REQUIRES_2SA_USER, DEVICES

import os
import sys
import pickle
import pytest
from unittest import TestCase

if sys.version_info >= (3, 3):
    from unittest.mock import patch  # pylint: disable=no-name-in-module,import-error
else:
    from mock import patch


class TestCmdline(TestCase):
    """Cmdline test cases."""

    main = None

    def setUp(self):
        cmdline.PyiCloudService = PyiCloudServiceMock
        self.main = cmdline.main

    def test_no_arg(self):
        """Test no args."""
        with pytest.raises(SystemExit, match="2"):
            self.main()

        with pytest.raises(SystemExit, match="2"):
            self.main(None)

        with pytest.raises(SystemExit, match="2"):
            self.main([])

    def test_help(self):
        """Test the help command."""
        with pytest.raises(SystemExit, match="0"):
            self.main(["--help"])

    def test_username(self):
        """Test the username command."""
        # No username supplied
        with pytest.raises(SystemExit, match="2"):
            self.main(["--username"])

    @patch("getpass.getpass")
    def test_username_password_invalid(self, mock_getpass):
        """Test username and password commands."""
        # No password supplied
        mock_getpass.return_value = None
        with pytest.raises(SystemExit, match="2"):
            self.main(["--username", "invalid_user"])

        # Bad username or password
        mock_getpass.return_value = "invalid_pass"
        with pytest.raises(
            RuntimeError, match="Bad username or password for invalid_user"
        ):
            self.main(["--username", "invalid_user"])

        # We should not use getpass for this one, but we reset the password at login fail
        with pytest.raises(
            RuntimeError, match="Bad username or password for invalid_user"
        ):
            self.main(["--username", "invalid_user", "--password", "invalid_pass"])

    @patch("pyicloud.cmdline.input")
    def test_username_password_requires_2sa(self, mock_input):
        """Test username and password commands."""
        # Valid connection for the first time
        mock_input.return_value = "0"
        with pytest.raises(SystemExit, match="0"):
            # fmt: off
            self.main([
                '--username', REQUIRES_2SA_USER,
                '--password', 'valid_pass',
                '--non-interactive',
            ])
            # fmt: on

    def test_device_outputfile(self):
        """Test the outputfile command."""
        with pytest.raises(SystemExit, match="0"):
            # fmt: off
            self.main([
                '--username', AUTHENTICATED_USER,
                '--password', 'valid_pass',
                '--non-interactive',
                '--outputfile'
            ])
            # fmt: on

        for key in DEVICES:
            file_name = DEVICES[key].content["name"].strip().lower() + ".fmip_snapshot"

            pickle_file = open(file_name, "rb")
            assert pickle_file

            contents = []
            with pickle_file as opened_file:
                while True:
                    try:
                        contents.append(pickle.load(opened_file))
                    except EOFError:
                        break
            assert contents == [DEVICES[key].content]

            pickle_file.close()
            os.remove(file_name)
