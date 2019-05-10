import socket
import selectors
import Logger
import options
import os

class Message:

    def __init__(self, selector, connection, address):
        self._address = address
        self._connection = connection
        self._selector = selector
        self._event_mask = selectors.EVENT_READ | selectors.EVENT_WRITE

        self._recv_buffer = b''
        self._send_buffer = b''

        #Reading states
        self._start_line = None         #Request start line
        self._headers = None            #Request headers
        self._body = None               #Request body
        self._recieved_request = False

        #Writing states
        self.status_line = None
        self.response_headers = None
        self.response_body = None
        self._completed_response = False
        self.sent = False

    def _read(self):
        try:
            data = self._connection.recv(1024)
        except BlockingIOError:
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                Logger.log(f"Peer closed connection {self._address[0]}:{self._address[1]}", Logger.LogLevel.NOTICE)

    def _write(self):
        if self._send_buffer:
            try:
                sent = self._connection.send(self._send_buffer)
            except BlockingIOError:
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]

                if self._completed_response and not self._send_buffer:
                    self.sent = True
                    self._close()

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self._selector.modify(self._connection, events, data=self)

    def _close(self):
        Logger.log(f"Closing connection with {self._address[0]}:{self._address[1]}", Logger.LogLevel.NOTICE)
        print()
        try:
            self._selector.unregister(self._connection)
        except Exception as e:
            Logger.log(f"error: selector.unregister() exception for {self._address}: {repr(e)}", Logger.LogLevel.ERROR)

        try:
            self._connection.close()
        except OSError as e:
            Logger.log(f"error: socket.close() exception for {self._address}: {repr(e)}", Logger.LogLevel.ERROR)
        finally:
            # Delete reference to socket object for garbage collection
            self._connection = None

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()

        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):
        self._read()

        if self._start_line is None:
            self.process_start_line()

        if self._start_line is not None:
            if self._headers is None:
                self.process_headers()

        if self._headers is not None:
            if self._body is None:
                self.process_body()

        if self._recieved_request:
            self._set_selector_events_mask('w')

    def process_start_line(self):
        try:
            end_of_start_line = self._recv_buffer.index(b'\n')
            _start_line = self._recv_buffer[:end_of_start_line + 1].decode("utf8")
            self._recv_buffer = self._recv_buffer[end_of_start_line + 1:]
        except ValueError:
            return

        try:
            values = _start_line.strip().split(" ")
            self._start_line = {"method" : values[0], "request-uri" : values[1], "http-version" : values[2]}
        except IndexError:
            Logger.log("Invalid start line", Logger.LogLevel.ERROR)

    def process_headers(self):
        try:
            end_of_header = self._recv_buffer.index(b"\r\n\r\n")
            _headers = self._recv_buffer[:end_of_header + 2].decode("utf8")
            self._recv_buffer = self._recv_buffer[end_of_header + 2:]
        except ValueError:
            return

        _header_lines = _headers.strip().split("\r\n")

        self._headers = {}
        for header_pair in _header_lines:
            try:
                colon_index = header_pair.index(":")
                key, value = header_pair[:colon_index], header_pair[colon_index + 1:]
                key = key.strip()
                value = value.strip()
                self._headers[key] = value
            except ValueError as error:
                Logger.log(error, Logger.LogLevel.ERROR)

    def process_body(self):
        Logger.log("Ignored body", Logger.LogLevel.WARNING)
        self._recieved_request = True

    def write(self):
        if self._start_line and not self.status_line:
            self.create_status()

        if self._headers and not self.response_headers:
            self.create_headers()

        if self._start_line and self._headers and not self.response_body:
            self.create_response()

        self._write()

    def create_status(self):
        self.status_line = {"http-version" : "HTTP/1.1"}
        if os.path.isfile(options.ROOT + self._start_line["request-uri"]):
            self.status_line["status-code"] = "200"
            self.status_line["status-text"] = "OK"
        else:
            self.status_line["status-code"] = "404"
            self.status_line["status-text"] = "Not Found."

    def create_headers(self):
        pass

    def create_response(self):
        response_string = f"{self.status_line['http-version']} {self.status_line['status-code']} {self.status_line['status-text']}\r\n"

        if self.response_headers:
            for header, value in self.response_headers.items():
                response_string += f"{header} : {value}\r\n"

        response_string += "\r\n"

        if self.status_line["status-code"] == "200":
            with open(options.ROOT + self._start_line["request-uri"], mode="r") as file:
                response_string += file.read()
                Logger.log(f"Served file for: {self._start_line['request-uri']}", Logger.LogLevel.PLAIN)
        else:
            Logger.log(f"Unable to serve file for: {self._start_line['request-uri']}", Logger.LogLevel.WARNING)

        self._completed_response = True

        self._send_buffer += bytes(response_string, 'utf-8')
