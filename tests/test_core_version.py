# -*- coding: utf-8 -*-
import unittest

import revit_stubs

revit_stubs.install()

import core


def version(text):
    return tuple(int(part) for part in text.split("."))


class NewerVersionTests(unittest.TestCase):

    def setUp(self):
        self.fetches = 0
        core.Version = version
        core.get_local_version = lambda: "1.4.6"

    def remote(self, text):
        def fetch(timeout=None):
            self.fetches += 1
            return text
        core.get_git_version = fetch

    def test_a_newer_release_is_returned_after_one_fetch(self):
        self.remote("1.5.0")
        self.assertEqual((core.newer_version(), self.fetches), ("1.5.0", 1))

    def test_the_same_release_returns_none(self):
        self.remote("1.4.6")
        self.assertIsNone(core.newer_version())

    def test_no_network_returns_none(self):
        def offline(timeout=None):
            raise IOError("offline")
        core.get_git_version = offline
        self.assertIsNone(core.newer_version())


if __name__ == "__main__":
    unittest.main()
