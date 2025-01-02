import logging
import os
from datetime import datetime
from config import proj_name

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure module-level logger
logger = logging.getLogger('app_logger')
logger.setLevel(logging.DEBUG)

# Create file handler which logs even debug messages
f_name = proj_name.replace(" ","_")
log_filename = f'logs/log_{f_name}.log'
if os.path.exists(log_filename):
    os.remove(log_filename)
fh = logging.FileHandler(log_filename)
fh.setLevel(logging.DEBUG)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

def get_logger():
    return logger