import socket
import signal
import sys
import os

# Глобальный флаг для управления сервером
server_running = True

# Таблица маршрутов
routes = {}

def render_response(content, status_code="200 OK", content_type="text/html"):
    """
    Генерация HTTP-ответа.
    :param content: Тело ответа (HTML, JSON и т. д.).
    :param status_code: HTTP статус код.
    :param content_type: Тип контента (например, text/html или application/json).
    :return: Строка HTTP-ответа.
    """
    response = f"HTTP/1.1 {status_code}\nContent-Type: {content_type}; charset=utf-8\nConnection: close\n\n{content}"
    print(f"Сформирован ответ: {response}")  # Логируем полностью сформированный ответ
    return response

def render_template(template_name, **kwargs):
    """
    Загрузка и рендеринг шаблона с заменой переменных.
    :param template_name: Имя файла шаблона.
    :param kwargs: Словарь значений для замены в шаблоне.
    :return: Строка с результатом рендеринга.
    """
    print(f"Пытаемся загрузить шаблон: {template_name}")
    try:
        template_path = f"templates/{template_name}"
        if os.path.exists(template_path):
            print(f"Шаблон найден: {template_path}")
            with open(template_path, 'r', encoding='utf-8') as file:
                template = file.read()

            # Замена переменных на их значения
            for key, value in kwargs.items():
                template = template.replace(f"{{{{ {key} }}}}", str(value))

            return template
        else:
            print(f"Шаблон не найден: {template_path}")
            return render_response("<p>404 Шаблон не найден</p>", status_code="404 Not Found")
    except Exception as e:
        print(f"Ошибка при загрузке шаблона: {e}")
        return render_response("<p>500 Внутренняя ошибка сервера</p>", status_code="500 Internal Server Error")

def route(path):
    """
    Декоратор для регистрации маршрутов.
    :param path: URL-путь.
    """
    def decorator(func):
        routes[path] = func  # Сохраняем обработчик маршрута
        return func
    return decorator

def get_local_ip():
    """
    Получает локальный IP-адрес устройства.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

def signal_handler(sig, frame):
    """
    Обработчик сигнала прерывания (Ctrl+C).
    """
    global server_running
    print("\nСервер останавливается...")
    server_running = False  # Устанавливаем флаг для завершения работы

def handle_request(request):
    """
    Обрабатывает HTTP-запрос.
    :param request: Текст HTTP-запроса.
    :return: HTTP-ответ.
    """
    lines = request.split("\r\n")
    if not lines:
        return render_response("<p>400 Некорректный запрос</p>", status_code="400 Bad Request")

    method, path, *_ = lines[0].split()
    print(f"Метод: {method}, Путь: {path}")

    # Проверяем наличие маршрута
    if path in routes:
        print(f"Обрабатываем маршрут: {path}")
        response = routes[path]()  # Вызываем обработчик маршрута
        return response
    else:
        print(f"Маршрут не найден: {path}")
        return render_response("<p>404 Страница не найдена</p>", status_code="404 Not Found")

def run_server(host="0.0.0.0", port=8080):
    """
    Запуск HTTP-сервера.
    :param host: Адрес, на котором сервер будет работать.
    :param port: Порт для подключения.
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
        print("\nСервер завершил работу.")
    finally:
        server_socket.close()
        print("Сервер завершил работу.")

# Регистрируем маршруты
@route("/")
def index():
    return render_response(render_template("index.html", title="Главная страница", content="Добро пожаловать!"))

@route("/about")
def about():
    title = "О нас"
    content = "Информация о проекте."
    return render_response(render_template("about.html", title=title, content=content))

@route("/contact")
def contact():
    title = "Контакты"
    content = "Свяжитесь с нами через email."
    return render_response(render_template("contact.html", title=title, content=content))

@route("/favicon.ico")
def favicon():
    return render_response("<p>404 Фавикон не найден</p>", status_code="404 Not Found")


# Запуск сервера
if __name__ == "__main__":
    # Устанавливаем кодировку для консоли
    if os.name == 'nt':  # Для Windows
        sys.stdout.reconfigure(encoding='utf-8')
    run_server()
