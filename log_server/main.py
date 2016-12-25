import datetime
import logging
import time
from multiprocessing.connection import Listener
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


    def setup_receiver(self, address=None, port=None):
        self.receiver_address = (address, port) or ("localhost", 6001)
        self.receiver = Listener(self.address, authkey=b"secret password")
        self.receiver_conn = self.receiver.accept()


    def setup_transmitter(self, address=None, port=None):
        self.transmitter_address = (address, port) or ("localhost", 6000)
        self.transmitter_conn = Client(self.transmitter_address, authkey=b"secret password")


    def run(self):
        self.logger.info("Log Server Started")
        while self.in_msg_loop is True:





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


