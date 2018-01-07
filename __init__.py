import logging
from time import strftime
logging.getLogger(__name__).addHandler(logging.FileHandler('Log/' + strftime("%Y-%m-%d %H.%M.%S") + '.log'))
