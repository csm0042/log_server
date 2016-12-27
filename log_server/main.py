#!/usr/bin/python3
""" log_server.py: Log server process
"""

# Import Required Libraries (Standard, Third Party, Local) ****************************************
import datetime
import logging
import os
import sys
import time
import multiprocessing
from multiprocessing.connection import Listener
sys.path.insert(0, os.path.abspath('..'))
import logger_mp
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


# Incoming Message Handler Sub-Process ************************************************************
def connection_listener(host, port, password, msg_in_queue):
    """ separate process to handle incoming connections """
    address = (host, port)
    listener = Listener(address, authkey=password)

    while True:
        conn = listener.accept()
        msg = conn.recv()
        conn.close()
        msg_in_queue.put_nowait(msg)


# Main process class ******************************************************************************
class LogServer(object):
    """ Log server that listens on port 6000 for incoming messages from other processes """
    def __init__(self):
        # Set up local logging
        self.debug_logfile = (os.path.dirname(os.path.abspath(__file__)) + "/logs/debug.log")
        self.info_logfile = (os.path.dirname(os.path.abspath(__file__)) + "/logs/info.log")
        logger_mp.listener_configurer(self.debug_logfile, self.info_logfile)
        self.logger = logging.getLogger(__name__)
        self.master_logger = None
        # Define control tags
        self.close_pending = False
        self.in_msg_loop = True
        self.shutdown_time = None
        self.heartbeat = datetime.datetime.now()
        # Define various queues used for sorting and processing of messages
        self.msg_in_queue = multiprocessing.Queue(-1)
        self.log_queue = multiprocessing.Queue(-1)
        self.work_queue = multiprocessing.Queue(-1)
        self.msg_out_queue = multiprocessing.Queue(-1)
        self.msg = None
        self.msg_in = None
        self.log_record = None
        self.work_record = None
        # Define sub-processed which will listen for incoming messages
        self.msg_in_proc = multiprocessing.Process(
            target=connection_listener, args=("localhost", 6000, b"password", self.msg_in_queue))



    def process_in_buffer(self):
        """ This method cycles through the incoming communication buffer and sorts the messages out
        by type """
        while True:
            try:
                self.msg_in = self.msg_in_queue.get_nowait()
                if isinstance(self.msg_in, message.Message):
                    self.work_queue.put_nowait(self.msg_in)
                    self.msg_in = None
                elif isinstance(self.msg_in, logging.LogRecord):
                    self.log_queue.put_nowait(self.msg_in)
                    self.msg_in = None
                else:
                    self.msg_in = None
            except:
                break


    def process_log_buffer(self):
        """ Processes log messages received from other processes via whatever handlers are
        currenntly defined. """
        while True:
            try:
                self.log_record = self.log_queue.get_nowait()
                if isinstance(self.log_record, logging.LogRecord) is True:
                    self.master_logger = logging.getLogger(self.log_record.name)
                    self.master_logger.handle(self.log_record)
                    self.log_record = None
                else:
                    self.log_record = None
            except:
                break


    def process_work_buffer(self):
        """ Processes any non-alarm messages received from other processes """
        while True:
            try:
                self.work_record = None
                self.work_record = self.msg_in_queue.get_nowait()
                if self.work_record.dest == 6000:
                    # If message is a heartbeat, update heartbeat and reset
                    if self.work_record.type == "001":
                        self.heartbeat = datetime.datetime.now()
                    elif self.work_record.type == "999":
                        self.logger.info("Kill code received - Shutting down")
                        self.shutdown_time = datetime.datetime.now()
                        self.close_pending = True
                else:
                    self.msg_out_queue.put_nowait(self.work_record)
            except:
                break


    def run(self):
        self.logger.info("Log Server Started")
        self.msg_in_proc.start()
        while True:
            self.process_in_buffer()
            self.process_log_buffer()
            self.process_work_buffer()
            time.sleep(0.011)



if __name__ == "__main__":
    this_process = LogServer()
    this_process.run()






