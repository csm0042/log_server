#!/usr/bin/python3
""" log_server_test.py:   
""" 

# Import Required Libraries (Standard, Third Party, Local) ****************************************
import logging
import unittest
import sys
import log_server


# Define test class *******************************************************************************
class TestLogServer(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.log_server = log_server.LogServer()

    def test_run(self):
        """ Put log server into run mode and test if it blocks or not """
        self.log_server.run()
