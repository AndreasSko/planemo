import os
import glob

from .test_utils import CliTestCase
from .test_utils import TEST_TOOLS_DIR


class LintTestCase(CliTestCase):

    def test_ok_tools(self):
        ok_tools = glob.glob("%s/ok_*" % TEST_TOOLS_DIR)
        for ok_tool in ok_tools:
            lint_cmd = ["lint", ok_tool]
            self._check_exit_code(lint_cmd)

    def test_fail_tools(self):
        fail_tools = glob.glob("%s/fail_*" % TEST_TOOLS_DIR)
        for fail_tool in fail_tools:
            lint_cmd = ["lint", fail_tool]
            self._check_exit_code(lint_cmd, exit_code=1)

    def test_skips(self):
        fail_citation = os.path.join(TEST_TOOLS_DIR, "fail_citation.xml")
        lint_cmd = ["lint", fail_citation]
        self._check_exit_code(lint_cmd, exit_code=1)

        lint_cmd = ["lint", "--skip", "citations", fail_citation]
        self._check_exit_code(lint_cmd, exit_code=0)

        # Check string splitting and stuff.
        lint_cmd = ["lint", "--skip", "xml_order, citations", fail_citation]
        self._check_exit_code(lint_cmd, exit_code=0)
