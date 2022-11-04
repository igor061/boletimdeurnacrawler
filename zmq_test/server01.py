#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

import time
from pprint import pprint

import zmq
from pip._vendor.rich import json

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

cont = 0

urls = [f'url-{cont}' for cont in range(20)]

step = 3
index = 0

results = []

while len(results) < len(urls):
    #  Wait for next request from client
    message = socket.recv()
    jsn_msg = json.loads(message.decode())

    if index > len(urls):
        resp = {'cmd': 'finish'}
    else:
        resp = {'list_urls': urls[index:index+step]}
        index += step

    socket.send_json(resp)


pprint("FINISH")
pprint(results)