import time
import datetime
import falcon
import pymongo
import redis
import zmq.green as zmq
from bson.json_util import dumps

"""
    falcon + mongo + redis on gunicorn w/gevent
    (Python 2.7.9, single instance each of mongo, redis, & zmq, gunicorn w/gevent & 8 workers)

    deps: falcon, pymongo, redis-py, gunicorn, gevent
    setup:  install mongodb & redis
            create names collection in test db w/dummy names
            start server with: gunicorn hello:app -w 8 -k gevent
            see output at: http://localhost/people
            test load with: siege -u http://localhost:8000/people -d1 -r10 -c60

    Transactions:                    600 hits
    Availability:                 100.00 %
    Elapsed time:                   8.23 secs
    Data transferred:               0.37 MB
    Response time:                  0.03 secs
    Transaction rate:              72.90 trans/sec
    Throughput:                     0.04 MB/sec
    Concurrency:                    1.90
    Successful transactions:         600
    Failed transactions:               0
    Longest transaction:            0.12
    Shortest transaction:           0.00
"""

# default handler
class PeopleResource:
    def on_get(self, req, resp):
        # mongo - simple names collection in the test db
        connection = pymongo.MongoClient('localhost', 27017)
        db = connection.test
        names = db.names.find()

        # redis
        r = redis.StrictRedis(host='localhost', port=6379, db=0)

        # Timestamp for logging the current request in redis
        epoch = time.time()
        timestamp = datetime.datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S')

        # check in ipython that r.get('foo') == request_obj
        request_obj = {
            'timestamp': timestamp,
            'protocol': req.protocol,
            'method': req.method,
            'host': req.host,
            'resource': 'people',
            'user-agent': req.user_agent
        }

        r.set('request', request_obj)

        # zmq client - send 10 messages upon each request
        context = zmq.Context()
        client_socket = context.socket(zmq.REQ)
        client_socket.connect("tcp://127.0.0.1:5050")

        for i in range(10):
            client_msg = "msg {0}".format(i)
            client_socket.send(client_msg)
            print "SEND", client_msg
            msg_in = client_socket.recv()


        # return 200 OK
        resp.status = falcon.HTTP_200

        # send all the names as json
        resp.body = dumps(names)

app = falcon.API()
people = PeopleResource()

app.add_route('/people', people)



