#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5556")
cont = 0

urls = [f'url-{cont}' for cont in range(1000)]

step = 10
index = 0
while True:
    #  Wait for next request from client
    message = socket.recv()
    print(f"Received result: {message}")

    #  Do some 'work'
    time.sleep(1)

    #  Send reply back to client
    url_list = urls[index:index+step]

    socket.send_json(url_list)

    #socket.send_string(f"World{cont}")

    index += step