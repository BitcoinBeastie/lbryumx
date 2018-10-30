#!/usr/bin/env python3
#import sys
#import ujson
#sys.modules['json'] = ujson

import logging
import traceback

from electrumx.server.env import Env

from lbryumx.coin import LBC
from lbryumx.controller import LBRYController


def main():
    '''Set up logging and run the server.'''
    log_fmt = Env.default('LOG_FORMAT', '%(levelname)s:%(name)s:%(message)s')
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logging.info('LbryumX server starting')
    try:
        controller = LBRYController(Env(LBC))
        controller.run()
    except Exception:
        traceback.print_exc()
        logging.critical('LbryumX server terminated abnormally')
    else:
        logging.info('LbryumX server terminated normally')


if __name__ == '__main__':
    main()
