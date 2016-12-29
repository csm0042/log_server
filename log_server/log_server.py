#!/usr/bin/python3
""" log_server.py: Log server process
"""

# Import Required Libraries (Standard, Third Party, Local) ****************************************
import datetime
import logging
import logging.handlers
import file_logger
import message
import multiprocessing
from multiprocessing.connection import Listener
import os
import sys
import time



# Authorship Info *********************************************************************************
__author__ = "Christopher Maue"
__copyright__ = "Copyright 2016, The Maue-Home Project"
__credits__ = ["Christopher Maue"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Christopher Maue"
__email__ = "csmaue@gmail.com"
__status__ = "Development"


# Main process class ******************************************************************************
class LogServer(object):
    """ Log server that listens on port 6000 for incoming messages from other processes """
    def __init__(self, logger=None):
        # Set up local logging
        self.logger = logger or logging.getLogger(__name__)
        self.heartbeat = datetime.datetime.now()
        self.shutdown_time = None
        self.main_loop = True
        self.setup_listener_connection("localhost", 6000, b"password")
        self.conn = None
        

    def setup_listener_connection(self, host, port, password):
        """ Set up a listener object """
        self.listener = Listener((host, port), authkey=password)


    def process_log_record(self, record):
        self.master_logger = logging.getLogger(record.name)
        self.master_logger.handle(record)


    def process_message(self, msg):
        if msg.dest == 6000:
            # If message is a heartbeat, update heartbeat and reset
            if msg.type == "001":
                self.heartbeat = datetime.datetime.now()
                print("Resetting heartbeat")
            elif msg.type == "999":
                self.logger.info("Kill code received - Shutting down")
                self.shutdown_time = datetime.datetime.now()
                self.main_loop = False


    def run(self):
        """ Runs a connection listener and processes any messages that are received """
        while self.main_loop is True:
            self.conn = self.listener.accept()
            self.msg = self.conn.recv()
            self.conn.close()
            if isinstance(self.msg, logging.LogRecord):
                self.process_log_record(self.msg)
            elif isinstance(self.msg, message.Message):
                self.process_message(self.msg)


if __name__ == "__main__":
    listener = LogServer()
    listener.run()