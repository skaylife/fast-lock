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
    response = f"HTTP/1.1 {status_code}\nContent-Type: text/html; charset=utf-8\nConnection: close\n\n{text}"
    print(f"Формируем ответ: {response}")  # Логируем полностью сформированный ответ
    return response





def render_template(template_name, **kwargs):
    print(f"Пытаемся загрузить шаблон: {template_name}")  # Логируем попытку загрузки шаблона
    try:
        template_path = f"templates/{template_name}"
        if os.path.exists(template_path):
            print(f"Шаблон найден: {template_path}")  # Шаблон существует
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()

            # Заменяем переменные
            for key, value in kwargs.items():
                template = template.replace(f"{{{{ {key} }}}}", str(value))

            return template
        else:
            print(f"Шаблон не найден: {template_path}")  # Шаблон не найден
            return render_response("<p>404 Шаблон не найден</p>", status_code="404 Not Found")
    except Exception as e:
        print(f"Ошибка при загрузке шаблона {template_name}: {e}")
        return render_response("<p>500 Внутренняя ошибка сервера</p>", status_code="500 Internal Server Error")

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
        print(f"Обрабатываем маршрут: {path}")
        response = routes[path]()  # Вызываем обработчик маршрута
        print(f"Ответ для маршрута {path}: {response}")  # Логируем результат ответа
        return response
    else:
        # Если маршрут не найден, возвращаем 404
        print(f"Маршрут не найден: {path}")
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
    except Exception as e:
        print(f"Ошибка при запуске сервера: {e}")
    finally:
        server_socket.close()
        print("Сервер завершил работу.")

# Регистрируем маршруты
@route("/")
def index():
    return render_response("<h1>Главная страница</h1><p>Добро пожаловать!</p>")

@route("/about")
def about():
    print("Вызвана функция about()")  # Логируем вызов функции
    title = "О нас"
    content = "Информация о проекте."
    # Используем шаблон для рендеринга
    return render_template("about.html", title=title, content=content)

@route("/contact")
def contact():
    print("Вызвана функция contact()")  # Логируем вызов функции
    title = "Контакты"
    content = "Свяжитесь с нами через email."
    return render_template("contact.html", title=title, content=content)
    

# Запуск сервера
if __name__ == "__main__":
    # Устанавливаем кодировку для консоли
    if os.name == 'nt':  # Для Windows
        sys.stdout.reconfigure(encoding='utf-8')
    run_server()
