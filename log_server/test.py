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
from multiprocessing.connection import Client
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
class TestSend(object):
    def __init__(self):
        self.msg_to_send = message.Message()

    def run(self):
        print("\n\nCreating message to send")
        self.msg_to_send = message.Message(source=6000, dest=6013, type="162", name="lrlt1", state=0, payload="192.168.86.25")
        self.target_address = ("localhost", 6013)
        self.conn = Client(self.target_address, authkey=b"password")
        print("Connection accepted, sending message")
        self.conn.send(self.msg_to_send.raw)
        print("Message sent, closing connection")
        #self.conn.close()
        print("Connection closed")


if __name__ == "__main__":
    test_xmit = TestSend()
    test_xmit.run()