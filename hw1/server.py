import socket


def handle_request(request):
    parts = request.split()
    if len(parts) != 2 or parts[0] != 'get_result':
        return 'Error: Invalid request'
    format_name = parts[1]

    # run docker command {format_name}

    return


def serve():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 2000))
    server_socket.listen()

    while True:
        client_socket, _ = server_socket.accept()
        request = client_socket.recv(1024).decode()
        response = handle_request(request)
        client_socket.sendall(response.encode())
        client_socket.close()


if __name__ == '__main__':
    serve()
