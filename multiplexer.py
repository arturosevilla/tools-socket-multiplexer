#!/usr/bin/env python

import sys
import socket
import select

class Connection(object):
    BUFFER_SIZE = 1024

    def __init__(self, connection, address):
        self._connection = connection
        self._address = address
        self._buffer = ''

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def connection(self):
        return self._connection

    @connection.setter
    def connection(self, value):
        self._connection = value

    def get_data(self):
        return self._connection.recv(self.BUFFER_SIZE)

    def close(self):
        self._connection.close()

    def receive_message(self, message):
        lines = message.split('\n')
        if len(lines) == 1:
            # just store in temp buffer
            self._buffer += lines[0]
            return
        
        # send the temporary buffer
        if len(self._buffer) > 0:
            sys.stdout.write(self._buffer)

        if len(lines[-1]) > 0:
            # the last fragment does not end with a newline
            self._buffer = lines[-1]
        else:
            self._buffer = ''
        # the last line is either empty or capture into the buffer
        lines = lines[:-1]
        
        for line in lines:
            sys.stdout.write(line + '\n')


def printerr(message):
    sys.stderr.write(message + '\n')

def get_connections(*connection_arguments):
    host, port = None, None
    connections = []
    for config_arg in connection_arguments:
        if host is None:
            host = config_arg
        else:
            port = int(config_arg)
            address = '%s:%s' % (host, port)
            try:
                connection = socket.create_connection((host, port))
            except:
                printerr('Error while trying to connect to %s' % address)
                sys.exit(1)
            connections.append(Connection(connection, address))
            host = port = None
    return connections


def multiplex(connections):
    # build a dictionary for callback
    callbacks = {}
    for conn in connections:
        callbacks[conn.connection.fileno()] = conn

    poller = select.poll()
    READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
    for socket_descriptor in callbacks.keys():
        poller.register(socket_descriptor, READ_ONLY)

    while True:
        events = poller.poll()

        for socket_descriptor, flag in events:
            handler = callbacks[socket_descriptor]

            if flag & (select.POLLIN | select.POLLPRI):
                # everything ok
                data = handler.get_data()
                if data:
                    handler.receive_message(data)
                else:
                    # disconnect
                    printerr('Source %s closed the connection' % handler.address)
                    poller.unregister(socket_descriptor)
                    handler.close()
                    del callbacks[socket_descriptor]
            elif flag & select.HULLUP:
                printerr('Source %s hung up the connection' % handler.address)
                poller.unregister(socket_descriptor)
                handler.close()
                del callbacks[socket_descriptor]
            elif flag & select.POLLERR:
                printerr('There was an error with %s.' % handler.address)
                poller.unregister(socket_descriptor)
                handler.close()
                del callbacks[socket_descriptor]

if __name__ == '__main__':
    if len(sys.argv[1:]) % 2 == 1:
        printerr('You need to specify both the server and the port')
        sys.exit(1)

    connections = get_connections(*sys.argv[1:])
    multiplex(connections)

