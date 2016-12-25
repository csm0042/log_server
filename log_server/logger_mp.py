import logging


def listener_configurer(debug_logfile, info_logfile):
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



def worker_configurer(queue):
    handler = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
