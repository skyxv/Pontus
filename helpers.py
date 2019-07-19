import socket


def communicate(dispatcher_host, dispatcher_port, command):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((dispatcher_host, dispatcher_port))
    except (ConnectionRefusedError, ConnectionResetError):
        return
    s.sendall(command.encode())
    response = s.recv(1024)
    s.close()
    return response.decode()


