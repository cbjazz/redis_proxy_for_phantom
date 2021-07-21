import sys
from queue import Queue
from threading import Thread
import redis
from time import sleep

import requests
import json
import traceback

#TODO Should add redis server 
# example 1.1.1.1:6379
redis_servers = ''

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
                print(e)
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
    def __init__(self, servers, thread_max=100):
        self.servers = servers
        self.status_db = "proxy_status"
        self.request_db = "proxy_request"        
        self._client = None
        self._pool = None
        self.thread_max = thread_max
        self._initialize()

    def _initialize(self):
        self._pool = ThreadPool(self.thread_max)

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

    def _setStatus(self, key, status):
        self._getClient().hset( self.status_db, key, status)
        print("Changed topic %s status is %s" % (key, status))
   
    def _getStatus(self, key):
        client = self._getClient()
        status = client.hget(self.status_db, key).decode('utf-8')
        print("Topic %s status is %s" % (key, status))
        return status
    
    def _getRequest(self, key):
        client = self._getClient()
        request = json.loads(client.hget(self.request_db, key))
        print("Topic %s request is %s" % (key,request))
        return request

    def _publish(self, key, result):
        self._getClient().publish(key, result)

    def run_http_request(self, key):
        self._setStatus(key, "run")
        request = self._getRequest(key)
        url = request['uri']
        method = request['method']
        headers = {}

        try:
            print("Receive method: %s\n " \
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
            print("Sending method: %s\n " \
                  "          url: %s\n " \
                  "          headers: %s\n " \
                  "          data : %s" % (method, url, headers, request['data']))

            if method.upper() == 'GET':
                res = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                res = requests.post(url, headers=headers, data=request['data'])
            else:
                res = requests.get(url, headers=headers)


            print("Response is: ")
            print(res)
            result = {"status_code" : res.status_code, "response" : json.dumps(res.json())}
            if res.status_code == 200:
                print(json.dumps(result))
                self._publish(key, json.dumps(result) ) 
                self._setStatus(key, "success")
            else:
                self._setStatus(key, "fail")
                self._publish(key, json.dumps(result) ) 
        except Exception as e:
            print(e)

    def runJobs(self):
        while True:
            jobNum = 0
            keys = self._getClient().hkeys(self.status_db)
            for key in keys:
                status = self._getStatus(key)
                if status == "ready":
                    jobNum =+ jobNum + 1
                    self._setStatus(key, "wait")
                    self._pool.add_task(self.run_http_request, key)

            if jobNum == 0:
                sleep(1)

        self._pool.wait_completion()

if __name__ == "__main__":
    jobManager = JobManager(redis_servers)
    jobManager.runJobs()
