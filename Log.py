import logging

class Logger():
    def __init__(self):
        logging.basicConfig(
            format='[ %(levelname)s ] :: %(message)s '
        )
        self.logger = logging.getLogger('general')

        self.logger.setLevel('WARNING')

    def setlevel(self, level):
        self.logger.setLevel(level)

    def log(self, level, message):
        if level.upper() == 'CRITICAL':
            lvl = 50
        if level.upper() == 'ERROR':
            lvl = 40
        if level.upper() == 'WARNING':
            lvl = 30
        if level.upper() == 'INFO':
            lvl = 20
        if level.upper() == 'DEBUG':
            lvl = 10
        self.logger.log(lvl, message)