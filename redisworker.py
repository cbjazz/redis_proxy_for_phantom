import sys
from queue import Queue
from threading import Thread
import redis
from time import sleep
import configparser
import os
from os import path

import requests
import json
import traceback
import logging


LOG = logging.getLogger("ProxyWorker.py")


class Worker(Thread):
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try: 
                func(*args, **kargs)
            except Exception as e:
                LOG.error(e)
            finally:
                self.tasks.task_done()


class ThreadPool:
    def __init__(self, thread_max):
        self.tasks = Queue(thread_max)
        for _ in range(thread_max):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        self.tasks.put((func, args, kargs))


    def add_map(self, func, args_list):
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        self.tasks.join()


class JobManager:
    # COMMAND
    command = ["none", "start", "stop"]
    COMMAND_NONE = command[0]
    COMMAND_START = command[1]
    COMMAND_STOP = command[2]

    # STATUS
    status = ["none", "running", "stopped"]
    STATUS_NONE = status[0]
    STATUS_RUNNING = status[1]
    STATUS_STOPPED= status[2]

    def __init__(self, servers="127.0.0.1:6379", thread_max=100):
        self.servers = servers
        self.status_db = "proxy_status"
        self.request_db = "proxy_request"
        self._running_jobs = 0 
        self._client = None
        self._pool = None
        self.thread_max = thread_max
        self._status = JobManager.STATUS_STOPPED
        self._command = JobManager.COMMAND_NONE
        #self._initialize()

    #def _initialize(self):

    def _finallize(self):
        self._deleteTopic()
        self._close()

    def _getClient(self):
        if not self._client:
            self._client = redis.StrictRedis(host=self.servers.split(":")[0], port=int(self.servers.split(":")[1]), db=0)

        return self._client

    def _close(self):
        if self._client :
            self._clent.close()

    def _setKeyStatus(self, key, status):
        self._getClient().hset( self.status_db, key, status)
        LOG.info("Changed topic %s status is %s" % (key, status))
   
    def _getKeyStatus(self, key):
        client = self._getClient()
        status = client.hget(self.status_db, key).decode('utf-8')
        LOG.info("Topic %s status is %s" % (key, status))
        return status
    
    def _getRequest(self, key):
        client = self._getClient()
        request = json.loads(client.hget(self.request_db, key))
        LOG.info("Topic %s request is %s" % (key,request))
        return request

    def _publish(self, key, result):
        self._getClient().publish(key, result)

    def run_http_request(self, key):
        self._setKeyStatus(key, "run")
        request = self._getRequest(key)
        url = request['uri']
        method = request['method']
        headers = {}

        try:
            LOG.debug("Receive method: %s\n " \
                  "          url: %s\n " \
                  "          headers: %s\n " \
                  "          data : %s" % (method, url, request['headers'], request['data']))

            for hkey in request['headers']:
                if hkey.lower() not in ['user-agent', 'host']: 
                    headers[hkey] = request['headers'][hkey]

            #res = requests.request(method, url, params=request['params'], headers=headers, data=request['data'])
            #res = requests.request(method, url, params=request['params'], headers=headers, data=request['data'])
            """ 
            if 'params' in request.keys(): 
                params = request['params']
            """
            LOG.debug("Sending method: %s\n " \
                  "          url: %s\n " \
                  "          headers: %s\n " \
                  "          data : %s" % (method, url, headers, request['data']))

            if method.upper() == 'GET':
                res = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                res = requests.post(url, headers=headers, data=request['data'])
            else:
                res = requests.get(url, headers=headers)

            result = {"status_code" : res.status_code, "response" : json.dumps(res.json())}
            if res.status_code == 200:
                LOG.debug("Response Message: " + json.dumps(result))
                self._publish(key, json.dumps(result) ) 
                self._setKeyStatus(key, "success")
            else:
                self._setKeyStatus(key, "fail")
                self._publish(key, json.dumps(result) ) 
        except Exception as e:
            LOG.error(e)

    def stopJob(self):
        self.setCommand(JobManager.COMMAND_STOP)

    def getCommand(self):
        return self._command

    def setCommand(self, command):
        self._command = command

    def getJobStatus(self):
        keyStatus = []
        keys = self._getClient().hkeys(self.status_db)
        for key in keys:
            status = self._getKeyStatus(key)
            keyStatus.append({"key" : str(key), "status" : str(status)})

        return keyStatus

    def deleteJob(self, key):
        self._getClient().hdel(self.status_db, key)
        self._getClient().hdel(self.request_db, key)
        pubsub = self._getClient().pubsub()
        pubsub.unsubscribe(self.topic)


    def runJobs(self):
        self.setCommand(JobManager.COMMAND_START)
        self._pool = ThreadPool(self.thread_max)

        while self.getCommand() == JobManager.COMMAND_START:
            self.jobNum = 0
            keys = self._getClient().hkeys(self.status_db)
            for key in keys:
                status = self._getKeyStatus(key)
                if status == "ready":
                    self.jobNum =+ self.jobNum + 1
                    self._setKeyStatus(key, "wait")
                    self._pool.add_task(self.run_http_request, key)

            if self.jobNum == 0:
                sleep(1)

        self._pool.wait_completion()

def get_config_section():
    if not hasattr(get_config_section, 'section_dict'):
        get_config_section.section_dict = dict()

        for section in config.sections():
            get_config_section.section_dict[section] = dict(config.items(section))

    return get_config_section.section_dict

if __name__ == "__main__":
    config = configparser.RawConfigParser()
    config.read("./conf/properties.conf")
    
    config_dict = get_config_section()
    redis_servers = config_dict['messagequeue']['servers']
    jobManager = JobManager(redis_servers)
    jobManager.runJobs()
