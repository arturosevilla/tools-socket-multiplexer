#!/usr/bin/env python
import socket
import sys
import thread
import time

def connection_handler(client, message):
    quit = False
    while True:
        try:
            quit = client.sendall(message + '\n') is not None
            time.sleep(1)
        except:
            quit = True

        if quit:
            quit = False
            client.close()
            break

def main(port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost', port))
    sock.listen(20)
    message = message.strip()

    while True:
        conn, _  = sock.accept()
        thread.start_new_thread(connection_handler, (conn, message))
        
if __name__ == '__main__':
    port = int(sys.argv[1])
    message = sys.argv[2]

    print('Running on port %d with message %s' % (port, message))
    main(port, message)


