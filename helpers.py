import socket


def communicate(dispatcher_host, dispatcher_port, command):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((dispatcher_host, dispatcher_port))
    s.send(command.encode())
    s.close()


