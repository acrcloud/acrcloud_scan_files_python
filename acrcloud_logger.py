#!/usr/bin/env python
#-*- coding:utf-8 -*

import os
import sys
import time
import logging
import traceback
from logging.handlers import TimedRotatingFileHandler
'''
traceback records log
try:
    pass
except Exception, e:
    logger.error('Failed to open file', exc_info=True)
'''

import logging

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

COLORS = {
    'WARNING'  : YELLOW,
    'INFO'     : GREEN,
    'DEBUG'    : BLUE,
    'CRITICAL' : YELLOW,
    'ERROR'    : RED,
    'RED'      : RED,
    'GREEN'    : GREEN,
    'YELLOW'   : YELLOW,
    'BLUE'     : BLUE,
    'MAGENTA'  : MAGENTA,
    'CYAN'     : CYAN,
    'WHITE'    : WHITE,
}

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ  = "\033[1m"

class ColoredFormatter(logging.Formatter):

    def __init__(self, *args, **kwargs):
        # can't do super(...) here because Formatter is an old school class
        logging.Formatter.__init__(self, *args, **kwargs)

    def format(self, record):
        levelname = record.levelname
        color     = COLOR_SEQ % (30 + COLORS[levelname])
        message   = logging.Formatter.format(self, record)
        message   = message.replace("$RESET", RESET_SEQ)\
                           .replace("$BOLD",  BOLD_SEQ)\
                           .replace("$COLOR", color)
        for k,v in COLORS.items():
            message = message.replace("$" + k,    COLOR_SEQ % (v+30))\
                             .replace("$BG" + k,  COLOR_SEQ % (v+40))\
                             .replace("$BG-" + k, COLOR_SEQ % (v+40))
        return message + RESET_SEQ


class AcrcloudLogger:

    def __init__(self, logname, loglevel = logging.INFO):
        self.logger = logging.getLogger(logname)
        self.logger.setLevel(loglevel)
        self.default_fmt = '%(asctime)s - %(name)s - %(levelname)8s - %(message)s'
        self.default_colorfmt = "$MAGENTA%(asctime)s$RESET - $COLOR%(name)-12s$RESET - $COLOR%(levelname)-6s$RESET - %(message)s"
        self.default_dir = './radioLog'

    def addFilehandler(self, logfile, logdir = None, fmt = '', loglevel = logging.INFO, when='D', interval=10, backupCount=1):
        try:
            filename = logfile
            if logdir is None:
                logdir = self.default_dir
            if not os.path.exists(logdir):
                os.makedirs(logdir)
            logfilepath = os.path.join(logdir, filename)
            #fhandler = logging.FileHandler(logfilepath)
            fhandler = TimedRotatingFileHandler(logfilepath, when, interval, backupCount)
            fhandler.setLevel(loglevel)
            formatter = logging.Formatter(fmt if fmt else self.default_fmt)
            fhandler.setFormatter(formatter)
            self.logger.addHandler(fhandler)
            return True
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            return False

    def addStreamHandler(self, fmt='', loglevel = logging.INFO):
        try:
            color_fmt = fmt if fmt else self.default_colorfmt
            shandler = logging.StreamHandler()
            shandler.setLevel(loglevel)
            color_formatter = ColoredFormatter(color_fmt)
            #f = logging.Formatter(self.default_fmt)
            shandler.setFormatter(color_formatter)
            self.logger.addHandler(shandler)
            return True
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            return False

if __name__ == '__main__':

    dlog = AcrcloudLogger('test', logging.INFO)
    dlog.addFilehandler('test.log')
    dlog.addStreamHandler()
    #dlog.logger.warn("hel")
    """
    for i in range(300):
        dlog.logger.warn('what!!!!!!!!!!!')
        #dlog.logger.info('hahhahah')
        #dlog.logger.error('it is monster!!')
        time.sleep(1)
    """
