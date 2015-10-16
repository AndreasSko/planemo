""" Integration tests for shed_diff command.
"""

from os.path import join
from .test_utils import (
    CliShedTestCase,
)
from planemo import io
import tempfile
import sys
import os
from xml.etree import ElementTree
from planemo.xml.diff import diff
from .test_utils import TEST_REPOS_DIR

DIFF_LINES = [
    "diff -r _local_/related_file _custom_shed_/related_file",
    "< A related non-tool file (modified).",
    "> A related non-tool file.",
]


class ShedDiffTestCase(CliShedTestCase):

    def test_shed_diff(self):
        with self._isolate_repo("single_tool") as f:
            upload_command = ["shed_upload", "--force_repository_creation"]
            upload_command.extend(self._shed_args())
            self._check_exit_code(upload_command)
            io.write_file(
                join(f, "related_file"),
                "A related non-tool file (modified).\n",
            )
            self._check_diff(f, True)
            self._check_diff(f, False)

    def test_diff_doesnt_exist(self):
        with self._isolate_repo("multi_repos_nested"):
            diff_command = ["shed_diff"]
            diff_command.extend(self._shed_args(read_only=True))
            self._check_exit_code(diff_command, exit_code=2)

    def test_diff_recursive(self):
        with self._isolate_repo("multi_repos_nested") as f:
            upload_command = [
                "shed_upload", "-r", "--force_repository_creation"
            ]
            upload_command.extend(self._shed_args())
            self._check_exit_code(upload_command)

            diff_command = ["shed_diff", "-r"]
            diff_command.extend(self._shed_args(read_only=True))
            self._check_exit_code(diff_command, exit_code=0)

            io.write_file(
                join(f, "cat1", "related_file"),
                "A related non-tool file (modified).\n",
            )
            self._check_exit_code(diff_command, exit_code=1)

    def test_shed_diff_raw(self):
        with self._isolate_repo("suite_auto"):
            upload_command = [
                "shed_upload", "--force_repository_creation",
            ]
            upload_command.extend(self._shed_args())
            self._check_exit_code(upload_command)

            diff_command = [
                "shed_diff", "-o", "diff"
            ]
            diff_command.append("--raw")
            diff_command.extend(self._shed_args(read_only=True))
            self._check_exit_code(diff_command, exit_code=1)

            diff_command = [
                "shed_diff", "-o", "diff"
            ]
            diff_command.extend(self._shed_args(read_only=True))
            self._check_exit_code(diff_command, exit_code=0)

    def test_diff_xunit(self):
        with self._isolate_repo("multi_repos_nested") as f:
            upload_command = [
                "shed_upload", "-r", "--force_repository_creation"
            ]
            upload_command.extend(self._shed_args())
            self._check_exit_code(upload_command)

            xunit_report = tempfile.NamedTemporaryFile(delete=False)
            xunit_report.flush()
            xunit_report.close()
            diff_command = ["shed_diff", "-r", "--report_xunit", xunit_report.name]
            diff_command.extend(self._shed_args(read_only=True))
            known_good_xunit_report = os.path.join(TEST_REPOS_DIR,
                                                   'multi_repos_nested.xunit.xml')
            known_bad_xunit_report = os.path.join(TEST_REPOS_DIR,
                                                  'multi_repos_nested.xunit-bad.xml')
            self._check_exit_code(diff_command, exit_code=0)

            compare = open(xunit_report.name, 'r').read()
            if not diff(
                self._make_deterministic(ElementTree.parse(known_good_xunit_report).getroot()),
                self._make_deterministic(ElementTree.fromstring(compare)),
                reporter=sys.stdout.write
            ):
                self.assertTrue(True)
            else:
                sys.stdout.write(compare)
                self.assertTrue(False)

            io.write_file(
                join(f, "cat1", "related_file"),
                "A related non-tool file (modified).\n",
            )
            self._check_exit_code(diff_command, exit_code=1)

            compare = open(xunit_report.name, 'r').read()
            if not diff(
                self._make_deterministic(ElementTree.parse(known_bad_xunit_report).getroot()),
                self._make_deterministic(ElementTree.fromstring(compare)),
                reporter=sys.stdout.write
            ):
                self.assertTrue(True)
            else:
                sys.stdout.write(compare)
                self.assertTrue(False)

            os.unlink(xunit_report.name)

    def _check_diff(self, f, raw):
        diff_command = ["shed_diff", "-o", "diff"]
        if raw:
            diff_command.append("--raw")
        diff_command.extend(self._shed_args(read_only=True))
        self._check_exit_code(diff_command, exit_code=1)
        diff_path = join(f, "diff")
        with open(diff_path, "r") as diff_f:
            diff = diff_f.read()
        for diff_line in DIFF_LINES:
            assert diff_line in diff

    def _make_deterministic(self, node):
        for x in node.findall('testcase'):
            if 'time' in x.attrib:
                del x.attrib['time']

        return node
