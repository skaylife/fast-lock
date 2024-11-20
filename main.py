import socket
import signal
import sys
import os

# Глобальный флаг для управления сервером
server_running = True

# Таблица маршрутов
routes = {}

def render_response(text, status_code="200 OK"):
    """
    Функция для создания HTTP-ответа.
    :param text: Тело страницы (HTML-контент).
    :param status_code: Код ответа (по умолчанию 200 OK).
    :return: Форматированный HTTP-ответ.
    """
    return f"HTTP/1.1 {status_code}\nContent-Type: text/html; charset=utf-8\n\n{text}"

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
    server_running = False  # Устанавливаем флаг для завершения работы

def handle_request(request):
    """
    Обрабатывает HTTP-запрос и вызывает соответствующий маршрут.
    :param request: Текст запроса от клиента.
    :return: HTTP-ответ.
    """
    # Разбираем первую строку HTTP-запроса, чтобы извлечь метод и путь
    lines = request.split("\r\n")
    if not lines:
        return render_response("<p>400 Некорректный запрос</p>", status_code="400 Bad Request")

    method, path, *_ = lines[0].split()
    print(f"Метод: {method}, Путь: {path}")

    # Проверяем наличие маршрута
    if path in routes:
        return routes[path]()  # Вызываем обработчик маршрута
    else:
        # Если маршрут не найден, возвращаем 404
        return render_response("<p>404 Страница не найдена</p>", status_code="404 Not Found")

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
            try:
                client_socket, client_address = server_socket.accept()
                with client_socket:
                    print(f"Подключение от {client_address}")
                    request = client_socket.recv(1024).decode("utf-8", errors="replace")
                    print(f"Запрос: {request}")

                    # Обрабатываем запрос и формируем ответ
                    response = handle_request(request)
                    client_socket.sendall(response.encode("utf-8"))
            except socket.timeout:
                continue  # Если соединений нет, продолжаем ожидание
            except Exception as e:
                print(f"Ошибка обработки запроса: {e}")
                continue  # Игнорируем ошибку и продолжаем работать

    except KeyboardInterrupt:
        # Обработка сигнала KeyboardInterrupt (Ctrl+C)
        print("\nСервер завершил работу.")
    finally:
        server_socket.close()
        print("Сервер завершил работу.")

# Регистрируем маршруты
@route("/")
def index():
    return render_response("<h1>Главная страница</h1><p>Добро пожаловать!</p>")

@route("/about")
def about():
    return render_response("<h1>О нас</h1><p>Информация о проекте.</p>")

@route("/contact")
def contact():
    return render_response("<h1>Контакты</h1><p>Свяжитесь с нами.</p>")

# Запуск сервера
if __name__ == "__main__":
    # Устанавливаем кодировку для консоли
    if os.name == 'nt':  # Для Windows
        sys.stdout.reconfigure(encoding='utf-8')
    run_server()
