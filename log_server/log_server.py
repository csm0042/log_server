#!/usr/bin/python3
""" log_server.py: Log server process
"""

# Import Required Libraries (Standard, Third Party, Local) ****************************************
import datetime
import logging
import logging.handlers
import os
import sys
import time
import multiprocessing
from multiprocessing.connection import Listener
sys.path.insert(0, os.path.abspath('..'))
import message


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
    def __init__(self):
        # Set up local logging
        self.debug_logfile = (os.path.dirname(os.path.abspath(__file__)) + "/logs/debug.log")
        self.info_logfile = (os.path.dirname(os.path.abspath(__file__)) + "/logs/info.log")
        self.setup_log_handlers(self.debug_logfile, self.info_logfile)
        self.logger = logging.getLogger(__name__)
        self.master_logger = None
        self.heartbeat = datetime.datetime.now()
        self.shutdown_time = None
        self.main_loop = True
        self.setup_listener_connection("localhost", 6000, b"password")
        self.conn = None


    def setup_log_handlers(self, debug_logfile, info_logfile):
        root = logging.getLogger()
        root.handlers = []
        # Create desired handlers
        debug_handler = logging.handlers.TimedRotatingFileHandler(debug_logfile, when="h", interval=1, backupCount=24, encoding=None, delay=False, utc=False, atTime=None)
        info_handler = logging.handlers.TimedRotatingFileHandler(info_logfile, when="h", interval=1, backupCount=24, encoding=None, delay=False, utc=False, atTime=None)
        console_handler = logging.StreamHandler()
        # Create individual formats for each handler
        debug_formatter = logging.Formatter('%(processName)-16s,  %(asctime)-24s,  %(levelname)-8s, %(message)s')
        info_formatter = logging.Formatter('%(processName)-16s,  %(asctime)-24s,  %(levelname)-8s, %(message)s')    
        console_formatter = logging.Formatter('%(processName)-16s,  %(asctime)-24s,  %(levelname)-8s, %(message)s')
        # Set formatting options for each handler
        debug_handler.setFormatter(debug_formatter)
        info_handler.setFormatter(info_formatter)
        console_handler.setFormatter(console_formatter)
        # Set logging levels for each handler
        debug_handler.setLevel(logging.DEBUG)
        info_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)
        # Add handlers to root logger
        root.addHandler(debug_handler)
        root.addHandler(info_handler)
        root.addHandler(console_handler)
        

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