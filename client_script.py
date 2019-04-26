#!/anaconda3/bin/python3

import socket
from options import *

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
message = input("Press q to quit: ")
while message != '':
    client_socket.send(bytes(message, 'UTF-8'))
    if message == "q":
        break
    message = input("Press q to quit: ")
print("Closing client socket")
client_socket.close()
