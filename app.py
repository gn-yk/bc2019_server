import socketserver
import handler


def main():
    host = '0.0.0.0'
    # host = 'localhost'
    port = 5000
    with socketserver.TCPServer((host, port), handler.RESPRequestHandler) as server:
        print('Server start')
        print('Socket:', server.socket.getsockname())
        print(flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
