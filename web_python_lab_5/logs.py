from flask import request
import database


def init_logging(app):
    """Инициализация логирования посещений"""

    @app.before_request
    def log_visit():
        """Логирование каждого посещения страницы"""
        try:
            # Исключаем статические файлы и некоторые страницы
            excluded_paths = ['/static/', '/favicon.ico', '/_debug_toolbar/']

            if any(request.path.startswith(path) for path in excluded_paths):
                return

            # Получаем ID пользователя из запроса
            user_id = None

            # Проверяем наличие сессии в контексте запроса
            from flask import has_request_context, session

            if has_request_context():
                user_id = session.get('user_id')

            # Добавляем запись в журнал
            database.add_visit_log(request.path, user_id)

        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            app.logger.error(f"Ошибка при логировании посещения: {e}")