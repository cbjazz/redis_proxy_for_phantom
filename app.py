from flask import Flask, render_template, request, abort, Response
import requests
import logging
import json
from OpenSSL import SSL
from redisworker import JobManager
import threading
import configparser

from multiprocessing import Process, Pool
import os
from os import path

app = Flask(__name__.split('.')[0])

jobManager = None
_pool = None
logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger('app.py')

@app.route('/', methods=["GET"])
def root():
    return "On Running"

@app.route('/info', methods=["GET"])
def info():
    jobStatus = jobManager.getJobStatus()

    return json.dumps(jobStatus)

def get_config_section():
    if not hasattr(get_config_section, 'section_dict'):
        get_config_section.section_dict = dict()

    for section in config.sections():
        get_config_section.section_dict[section] = dict(config.items(section))
                                            
    return get_config_section.section_dict

if __name__ == '__main__':
    config = configparser.RawConfigParser()
    if "PROXY_HOME" not in os.environ.keys():
        print("PROXY_HOME is not defined")
        exit(0)

    HOME_DIR = os.environ["PROXY_HOME"]
    config.read(HOME_DIR + "/conf/properties.conf")
    config_dict = get_config_section()
    redis_servers = config_dict['messagequeue']['servers']
    port = config_dict['webserver']['port']
    jobManager = JobManager(redis_servers)
    _pool = Pool(1)
    _pool.apply_async(jobManager.runJobs)
    app.run("0.0.0.0", debug=True)
    _pool.close()
    _pool.join()
