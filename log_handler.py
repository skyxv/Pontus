import os
import logging
from logging.handlers import RotatingFileHandler

log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thanatos.log')
logging.basicConfig(filename=log_dir,
                    format='%(asctime)s - %(name)s-%(filename)s[line:%(lineno)d] - %(levelname)s - %(message)s')


def get_logger():
    logger = logging.getLogger('thanatos_logger')
    handler = RotatingFileHandler(log_dir, maxBytes=20000000, backupCount=2)
    logger.addHandler(handler)
    return logger
