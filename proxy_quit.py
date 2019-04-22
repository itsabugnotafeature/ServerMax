#!/anaconda3/bin/python3

import socket
from proxy_options import *

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
client_socket.send(bytes('q', 'UTF-8'))
