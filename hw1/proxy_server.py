import os
import socket
import sys


def handle_request(request):
    print(request)
    parts = request.decode().split()
    if len(parts) != 2 or parts[0] != 'get_result':
        return 'Error: Invalid request'
    format_name = parts[1]

    server_port = int(os.environ.get(f'{format_name}_PORT'))
    server_name = os.environ.get(f'{format_name}_NAME')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.sendto(b"work", (server_name, server_port))
    response, _ = server_socket.recvfrom(1024)
    return response


def serve():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', 2000))

    while True:
        request, address = server_socket.recvfrom(1024)
        response = handle_request(request)
        server_socket.sendto(response, address)


if __name__ == '__main__':
    serve()
