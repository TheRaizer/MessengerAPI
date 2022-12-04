"""Initializes logging."""

import logging
import logging.config

# load logger from config file before any other modules are loaded.
logging.config.fileConfig("logging.conf")
