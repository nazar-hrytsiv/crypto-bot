import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('out.log')
formatter = logging.Formatter(fmt='%(levelname)s|%(asctime)s|%(filename)s %(funcName)s on line %(lineno)d|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)