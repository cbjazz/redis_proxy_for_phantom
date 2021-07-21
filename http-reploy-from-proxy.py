from mitmproxy import http
import uuid
from redisproxy import OuterRequest
import json

def request(flow: http.HTTPFlow) -> None:
    # Remove redis_server code later. 
    redis_server = "1.1.1.1:6379" 
    topic = str(uuid.uuid4())
    outerRequest = OuterRequest(redis_server, topic)
    header = {}

    for key in flow.request.headers.keys():
        header[key] = flow.request.headers[key]
    query = {}
    for key in flow.request.query.keys():
        query[key] = flow.request.query[key]

    request_dict = { "uri" : flow.request.pretty_url, 
            "method" : "GET",
            "headers" : header,
            "data" : query
            }

    outerReuqest = OuterRequest(redis_server, topic)
    response = outerRequest.request(json.dumps(request_dict))
    response_dict = json.loads(str(response, "utf-8"))

    flow.response = http.Response.make(response_dict["status_code"], response_dict["response"], {"Content-Type":"application/json"} )
