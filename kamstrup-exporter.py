from prometheus_client import start_http_server, Gauge, Counter
import time
import logging
import yaml
import os
import datetime
import requests
import importlib
from PyKamstrup.kamstrup import kamstrup

# define default config
default_config = {
    'serialport': '/dev/ttyU0',
    'webport': 8000,
    'registervar': 'kamstrup_684_var', 
}

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s:%(funcName)s():%(lineno)i:  %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S %z',
)
logger = logging.getLogger("kamstrup-exporter.%s" % __name__)

def read_config():
    try:
        with open("kamstrup-exporter.yml") as f:
            return (yaml.safe_load(f.read()), edittime)
    except FileNotFoundError:
        return ({}, 0)

def process_request():
    global adjusttimes

    for register in register_var:
        try:
            value, unit = kamstrup.readvar(register)
        except IndexError:
            logger.error("Register %s does not exist on the meter" % register)
            continue
        if unit == "ASCII":
            metrics[register].labels(asciistring=bytearray.fromhex(s2).decode('ascii')).set(1)
        else:
            metrics[register].set(value)

    # sleep a bit before returning
    logger.debug("------------------------")
    time.sleep(5)

# read config file
fileconf = read_config()
config = default_config
config.update(fileconf)
logger.debug("Running with config %s" % config)

# initialise serial
kamstrup = kamstrup(config['serialport'])

# import register var
register_var = importlib.import_module(config['registervar'])

# define metrics
metrics = {}
for register, name in register_var.items():
    try:
        value, unit = kamstrup.readvar(register)
    except IndexError:
        logger.error("Register %s does not exist on the meter" % register)
        continue
    if unit == "ASCII":
        metrics[register] = Counter('kamstrup_register_%s_%s' % (register, name), register, ['asciistring'])
    else:
        metrics[register] = Counter('kamstrup_register_%s_%s' % (register, name), register)

start_http_server(config['webport'])

while True:
    process_request()

