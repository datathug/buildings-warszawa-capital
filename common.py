import logging

LOG_FILE = 'geocoder.log'
MAX_RETRIES = 3
MAX_REQUESTS_PER_MINUTE = 200

# logging configuration - write to file and console
LOGGER_FORMAT = "%(levelname)s:  %(message)s"
logger = logging.getLogger('')
logging.basicConfig(filename=LOG_FILE, filemode='a',
                    level=logging.INFO, format=LOGGER_FORMAT)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logging.Formatter(LOGGER_FORMAT))
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)