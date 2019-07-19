import socket


def communicate(dispatcher_host, dispatcher_port, command):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((dispatcher_host, dispatcher_port))
    s.sendall(command.encode())
    response = s.recv(1024)
    s.close()
    return response.decode()


