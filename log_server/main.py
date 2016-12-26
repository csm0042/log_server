import datetime
import logging
import queue
import os
import time
from multiprocessing.connection import Listener, Client
from .logger_mp import listener_configurer, worker_configurer
from .message import Message





class LogServer(object):
    def __init__(self):
        # Set up local logging
        self.debug_logfile = (os.path.dirname(os.path.abspath(__file__)) + "/logs/debug.log")
        self.info_logfile = (os.path.dirname(os.path.abspath(__file__)) + "/logs/info.log")
        listener_configurer(self.debug_logfile, self.info_logfile)
        self.logger = logging.getLogger(__name__)

        self.close_pending = False
        self.in_msg_loop = True

        self.msg_in_queue = queue.Queue(-1)
        self.log_queue = queue.Queue(-1)
        self.work_queue = queue.Queue(-1)
        self.msg_out_queue = queue.Queue(-1)
        self.msg_recv = None
        self.msg_in = None

        self.address = str()
        self.receiver_address = str()
        self.transmitter_address = str()
        self.setup_receiver()
        self.setup_transmitter()



    def setup_receiver(self, address=None, port=None):
        self.receiver_address = (address, port) or ("localhost", 6001)
        self.receiver = Listener(self.receiver_address, authkey=b"secret password")
        self.receiver_conn = self.receiver.accept()


    def setup_transmitter(self, address=None, port=None):
        self.transmitter_address = (address, port) or ("localhost", 6000)
        self.transmitter_conn = Client(self.transmitter_address, authkey=b"secret password")


    def receive_and_buffer(self):
        """ This method checks the receiver connection for incoming messages and establishes the
        connection and receives the incoming message if one is availabe to receive.  Messages are
        deposited into the incoming message buffer for later processing """
        while True:
            try:
                if self.receiver_conn.poll() is True:
                    self.msg_recv = self.receiver_conn.recv()
                    if self.msg_recv is not None:
                        self.msg_in_queue.put_nowait(self.msg_recv)
                    self.msg_recv = None
                else:
                    break
            except:
                break


    def process_in_buffer(self):
        """ This method cycles through the incoming communication buffer and sorts the messages out
        by type """
        while True:
            try:
                self.msg_in = self.msg_in_queue.get_nowait()
                if isinstance(self.msg_in, Message):
                    self.work_queue.put_nowait(self.msg_in)
                    self.msg_in = None
                elif isinstance(self.msg_in, logging.LogRecord):
                    self.log_queue.put_nowait(self.msg_in)
                    self.msg_in = None
            except:
                break


    def process_log_buffer(self):
        """ Processes log messages received from other processes via whatever handlers are
        currenntly defined. """
        pass


    def process_work_buffer(self):
        """ Processes any non-alarm messages received from other processes """
        pass


    def send_outgoing(self):
        """ Transmits outgoing messages to other processes as necessary """
        pass



    def run(self):
        self.logger.info("Log Server Started")
        while self.in_msg_loop is True:
            self.receive_and_buffer()
            self.process_in_buffer()
            self.process_log_buffer()
            self.process_work_buffer()
            self.send_outgoing()



if __name__ == "__main__":
    this_process = LogServer()
    this_process.run()






# Log Handler Process ******************************************************************************
def listener_process(in_queue, out_queue, log_queue, debug_logfile, info_logfile):
    listener_configurer(debug_logfile, info_logfile)
    logger = logging.getLogger(__name__)

    close_pending = False
    msg_in = Message()
    log_record = None
    last_log_record = None
    last_hb = datetime.datetime.now()
    shutdown_time = None
    in_msg_loop = bool()

    # Main process loop
    logger.info("Main loop started")
    in_msg_loop = True
    while in_msg_loop is True:
        # Check incoming process message queue and pull next message from the stack if present
        try:
            msg_in = Message(raw=in_queue.get_nowait())
        except:
            pass
        
        if len(msg_in.raw) > 4:
            logger.debug("Processing message [%s] from incoming message queue", msg_in.raw)
            # Check if message is destined for this process based on pseudo-process-id
            if msg_in.dest == "01":
                # If message is a heartbeat, update heartbeat snapshot
                if msg_in.type == "001":
                    last_hb = datetime.datetime.now()
                    logger.debug("")
                # If message is a kill-code, set the close_pending flag so the process can close out gracefully 
                elif msg_in.type == "999":
                    logger.info("Kill code received - Shutting down")
                    shutdown_time = datetime.datetime.now()
                    close_pending = True
            else:
                # If message isn't destined for this process, drop it into the queue for the main process so it can re-forward it to the proper recipient.
                out_queue.put_nowait(msg_in.raw)
                logger.debug("Redirecting message [%s] back to main", msg_in.raw)  
            pass
            msg_in = Message()


        # Check incoming process message queue and pull next message from the stack if present
        try:
            log_record = log_queue.get_nowait()
        except:
            pass     

        # Get log handler, then pass it the log message from the queue
        if isinstance(log_record, logging.LogRecord) is True:
            master_logger = logging.getLogger(log_record.name)
            master_logger.handle(log_record)
            log_record = None
        

        # Only close down process once incoming message queue is empty
        if close_pending is True:
            if shutdown_time is not None:
                if datetime.datetime.now() > shutdown_time + datetime.timedelta(seconds=5):
                    if in_queue.empty() is True:
                        in_msg_loop = False
        elif datetime.datetime.now() > last_hb + datetime.timedelta(seconds=30):
            in_msg_loop = False
        
        # Delay before re-running loop
        time.sleep(0.013)
    pass
    logger.info("Shutdown complete")


