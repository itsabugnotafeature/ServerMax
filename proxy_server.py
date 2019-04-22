#!/anaconda3/bin/python3

import socket
from proxy_options import *
import sys


def parse_http_uri(http_request):
    first_sp = http_request.index(" ")
    len_to_first_sp = len(http_request[:first_sp])
    second_sp = http_request[first_sp + 1:].index(" ")
    uri = http_request[first_sp + 1:second_sp + len_to_first_sp + 1]
    print("Resource request for {uri}".format(uri=uri))
    return uri

def edit_options(key, value):
    with open("proxy_options.py", 'r+') as file:
        lines = file.readlines()
        if key == "host":
            line = lines[0].rstrip().split("'")
            line[1] = value
            line = "'".join(line)
            while len(line) < len(lines[0]):
                line += " "
            line += "\n"
            lines[0] = line
        
        elif key == "port":
            line = lines[1].rstrip().split(" ")
            line[2] = value
            line = " ".join(line)
            while len(line) < len(lines[1]):
                line += " "
            line += "\n"
            lines[1] = line
        file.seek(0)
        for line in lines:
            file.write(line)


def parse_cmd_line_args():
    global HOST
    global PORT
    argv = []
    for index in range(1,len(sys.argv), 2):
        try:
            if sys.argv[index].index("-") != 0:
                print("{cmd} takes an argument".format(cmd=sys.argv[index]))
                continue
            argv.append((sys.argv[index], sys.argv[index + 1]))
        except IndexError:
            print("{cmd} takes an argument".format(cmd=sys.argv[index]))
    for cmd, arg in argv:
        if cmd == "-h":
            if arg != HOST:
                HOST = arg
                edit_options("host", arg)
                print("Set host")
            else:
                print("Host same as host already set. \n Host left unchanged.")
        elif cmd == "-p":
            if arg != str(PORT):
                PORT = int(arg)
                edit_options("port", arg)
                print("Set port")
            else:
                print("Port already in use.\n Port left unchanged.")
        elif cmd == "-m":
            if arg == "lh":
                HOST = "localhost"
                PORT = 80
                edit_options("host", "localhost")
                edit_options("port", "80")
    print("Running server on {host}:{port}".format(host=HOST, port=PORT))

### Beginning of code ###

parse_cmd_line_args()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

is_running = True

while is_running:
    connection, address = server_socket.accept()
    print("Connected to {address}".format(address=address))
    data = connection.recv(1024)
    if data:
        string_rep = data.decode('UTF-8')
        if string_rep == 'q':
            is_running = False
            break
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.connect((PORT, PROXY_HOST))
        proxy_socket.send(data)
        proxy_response = proxy_socket.recv(1024)
        connection.send(proxy_response)
    print("Closing connection")
    connection.close()
print("Closing server socket")
server_socket.close()
