import socket

def run_server(host="127.0.0.1", port=8080):
    """Запускает простой HTTP-сервер."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Сервер запущен на {host}:{port}")

        while True:
            client_socket, client_address = server_socket.accept()
            with client_socket:
                print(f"Подключение от {client_address}")
                request = client_socket.recv(1024).decode("utf-8")
                print(f"Запрос: {request}")

                # Простой HTTP-ответ
                response = (
                    "HTTP/1.1 200 OK\n"
                    "Content-Type: text/html\n\n"
                    "<h1>Привет, мир!</h1>"
                )
                client_socket.sendall(response.encode("utf-8"))

# Запуск сервера
if __name__ == "__main__":
    run_server()
