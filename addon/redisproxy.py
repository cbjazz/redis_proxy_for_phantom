import redis
# from json import dumps
import time


class OuterRequest:
    def __init__(self, servers, topic):
        self.servers = servers
        self.topic = "id:" + topic
        self.status_db = "proxy_status"
        self.request_db = "proxy_request"
        self._client = None
        self._initialize()

    def _initialize(self):
        self._createTopic()

    def _finallize(self):
        self._deleteTopic()
        self._unsubscribeTopic()
        self._close()

    def _getClient(self):
        if not self._client:
            self._client = redis.StrictRedis(host=self.servers.split(":")[0], port=int(self.servers.split(":")[1]), db=0)

        return self._client

    def _close(self):
        if self._client:
            self._client.close()

    def _createTopic(self):
        client = self._getClient()

        client.hset( self.status_db, self.topic, 'new')
        client.hset( self.request_db, self.topic, '')
        print("Create Topic %s, Topic Status is %s" % (self.topic, 'new') )

    def _deleteTopic(self):
        client = self._getClient()
        client.hdel( self.status_db, self.topic)
        client.hdel( self.request_db, self.topic)
        print("Delete Topic %s, Topic Status is %s" % (self.topic, 'close') )

    def _addTopic(self, requestMessage):
        client = self._getClient()

        client.hset( self.status_db, self.topic, 'ready')
        client.hset( self.request_db, self.topic, requestMessage)
        print("Update Topic %s, Topic Status is %s" % (self.topic, 'ready') )
        print("Request Message is %s" % (requestMessage) )

    def _unsubscribeTopic(self):
        client = self._getClient()
        pubsub = client.pubsub()
        pubsub.unsubscribe(self.topic)

    def _getStatus(self):
        client = self._getClient()
        status = client.hget(self.status_db, self.topic).decode('utf-8')
        print("Current Topic status is %s" % status)
        return status

    def _subscribeTopic(self, timeout=10):
        client = self._getClient()
        pubsub = client.pubsub()
        result = []

        pubsub.subscribe(self.topic)
        stop_time = time.time() + timeout
        print("Wait Result with %s..." % (self.topic) )
        while time.time() < stop_time:
            message = pubsub.get_message(timeout=stop_time - time.time())
            if message:
                result.append( message['data'] )
                print("Got Message %s" % (message['data']))

            status = self._getStatus()
            if status == "success" or status == "fail":
                break

        if len(result) < 1:
            self._finallize()
            print("Timeout, Shutdown")

        self._finallize()
        return result[1]

    def request(self, requestMessage, timeout=10):
        self._addTopic(requestMessage)
        result = self._subscribeTopic(timeout)

        return result
if __name__ == "__main__":
    import uuid
    redis_servers = '13.125.161.122:6379'
    topic = str(uuid.uuid4())
    start_time = time.time()
    outerRequest = OuterRequest(redis_servers, topic)
    outerRequest.request('{"uri" : "https://ipinfo.io/8.8.8.8/geo", "method" : "GET"}', 60)
    #outerRequest.request('{"uri" : "http://wttr.in/Dunedin?0", "method" : "GET"}', 60)
    end_time = time.time()
    print("Total Execution Time: %f" % (end_time - start_time) )
