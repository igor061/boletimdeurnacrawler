#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#
from pprint import pprint
from time import sleep

import zmq
from pip._vendor.rich import json

context = zmq.Context()

#  Socket to talk to server
print("Connecting to hello world server...")
socket_req = context.socket(zmq.REQ)
socket_req.connect("tcp://localhost:5555")

socket_resp = context.socket(zmq.REQ)
socket_resp.connect("tcp://localhost:5556")

#  Do 10 requests, waiting each time for a response
while True:
    print(f"Sending request  ...")
    socket_req.send_json({'cmd': 'sendme'})

    #  Get the reply.
    resp = json.loads(socket_req.recv().decode())

    if cmd := resp.get('cmd'):
        if cmd == 'finish':
            break
        else:
            print(f'cmd {cmd} not implemented')

    elif list_urls := resp.get('list_urls'):
        print(list_urls)
        sleep(5)
        resp = {'result': [('url1', 'bu1_base64'), ('url2', 'bu2_base64')]}
        socket_resp.send_json(resp)
        print("resp sended")
        socket_resp.recv()

print("Terminamos!!!")