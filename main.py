import socket
import signal

# Глобальный флаг для управления сервером
server_running = True

# Таблица маршрутов
routes = {}

def route(path):
    """
    Декоратор для регистрации маршрутов.
    :param path: URL-путь.
    """
    def decorator(func):
        routes[path] = func  # Сохраняем обработчик для маршрута
        return func
    return decorator

def get_local_ip():
    """
    Получает локальный IP-адрес машины.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

def signal_handler(sig, frame):
    """
    Обрабатывает сигнал прерывания (Ctrl+C).
    """
    global server_running
    print("\nСервер останавливается...")
    server_running = False

def handle_request(request):
    """
    Обрабатывает HTTP-запрос и вызывает соответствующий маршрут.
    :param request: Текст запроса от клиента.
    :return: HTTP-ответ.
    """
    # Разбираем первую строку HTTP-запроса, чтобы извлечь метод и путь
    lines = request.split("\r\n")
    if not lines:
        return "HTTP/1.1 400 Bad Request\n\n<p>Некорректный запрос</p>"

    method, path, *_ = lines[0].split()
    print(f"Метод: {method}, Путь: {path}")

    # Проверяем наличие маршрута
    if path in routes:
        return routes[path]()  # Вызываем обработчик маршрута
    else:
        # Если маршрут не найден, возвращаем 404
        return "HTTP/1.1 404 Not Found\n\n<p>Страница не найдена</p>"

def run_server(host="0.0.0.0", port=8080):
    """
    Основная функция для запуска сервера.
    :param host: Хост (адрес), на котором сервер будет работать.
    :param port: Порт, на котором сервер будет слушать соединения.
    """
    global server_running
    local_ip = get_local_ip()
    print(f"Локальный IP-адрес: {local_ip}")

    # Создаём серверный сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Сервер запущен на {host}:{port} (доступен на {local_ip}:{port})")

    signal.signal(signal.SIGINT, signal_handler)  # Обработчик Ctrl+C

    try:
        while server_running:
            server_socket.settimeout(1.0)
            try:
                client_socket, client_address = server_socket.accept()
                with client_socket:
                    print(f"Подключение от {client_address}")
                    request = client_socket.recv(1024).decode("utf-8")
                    print(f"Запрос: {request}")

                    # Обрабатываем запрос и формируем ответ
                    response = handle_request(request)
                    client_socket.sendall(response.encode("utf-8"))
            except socket.timeout:
                continue
    finally:
        server_socket.close()
        print("Сервер завершил работу.")

# Регистрируем маршруты
@route("/")
def index():
    return "HTTP/1.1 200 OK\nContent-Type: text/html; charset=utf-8\n\n<h1>Главная страница</h1><p>Добро пожаловать!</p>"

@route("/about")
def about():
    return "HTTP/1.1 200 OK\nContent-Type: text/html; charset=utf-8\n\n<h1>О нас</h1><p>Информация о проекте.</p>"

@route("/contact")
def contact():
    return "HTTP/1.1 200 OK\nContent-Type: text/html; charset=utf-8\n\n<h1>Контакты</h1><p>Свяжитесь с нами.</p>"

# Запуск сервера
if __name__ == "__main__":
    run_server()
