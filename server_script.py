#!/anaconda3/bin/python3

import socket
from options import *
import sys
import selectors
import Message
import Logger

def edit_options(key, value):
    with open("options.py", 'r+') as file:
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
            elif arg == "lp":
                HOST = "localhost"
                PORT = 8080
                edit_options("host", "localhost")
                edit_options("port", "8080")
        elif cmd == "-help":
            for command, desc in options_explanations:
                print(command + " : " + desc)
            sys.exit()


html_404_string = "<!DOCTYPE html><html><body><h1 align='center'>404</h1> <p align='center'>File Not Found!</p></body></html>"
ROOT = "/Users/max/Desktop/My Projects/Websites/Test"

parse_cmd_line_args()

sel = selectors.DefaultSelector()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Avoid bind() exception: OSError: [Errno 48] Address already in use
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((HOST, PORT))

print("Running server on {host}:{port}".format(host=HOST, port=PORT))
print()

server_socket.listen(5)

is_running = True

server_socket.setblocking(False)
sel.register(server_socket, selectors.EVENT_READ, data=None)

def accept_wrapper(socket):
    connection, address = server_socket.accept()
    Logger.log(f"Connected to {address}", Logger.LogLevel.PLAIN)
    connection.setblocking(False)
    data = Message.Message(sel, connection, address)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(connection, events, data=data)

def service_connection(key, mask):
    data = key.data
    data.process_events(mask)

### Beginning of code ###

while is_running:
    events = sel.select(timeout=None)
    for key, mask in events:
        if key.data is None:
            accept_wrapper(key.fileobj)
        else:
            service_connection(key, mask)
print("Closing server socket")
server_socket.close()
