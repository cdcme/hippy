import zmq.green as zmq

"""
    zmq echo server
    (Python 2.7.9)

    deps: pyzmq, gevent
"""

context = zmq.Context()

# echo server numero uno
srv_socket = context.socket(zmq.REP)
srv_socket.bind('tcp://127.0.0.1:5050')

while True:
    srv_msg = srv_socket.recv()
    print "RECV", srv_msg
    srv_socket.send(srv_msg)


