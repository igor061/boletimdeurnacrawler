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

socket_result = context.socket(zmq.REP)
socket_result.bind("tcp://*:5556")

cont = 0

urls = [f'url-{cont}' for cont in range(20)]

step = 3
index = 0

results = []

while len(results) < len(urls):
    #  Wait for next request from client
    message = socket_result.recv()
    jsn_msg = json.loads(message.decode())

    result = jsn_msg.get('result')
    pprint(result)
    results.extend(result)
    socket_result.send_json({'cmd': 'recebido'})


pprint("FINISH")
pprint(results)