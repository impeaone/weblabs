import sqlite3
import hashlib
from datetime import datetime
from contextlib import contextmanager

DATABASE = 'users.db'


def init_db():
    """Инициализация базы данных"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Создание таблицы ролей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')

        # Создание таблицы пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                last_name TEXT,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                role_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles (id)
            )
        ''')

        # Создание таблицы журнала посещений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path VARCHAR(100) NOT NULL,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Добавление стандартных ролей, если их нет
        cursor.execute("SELECT COUNT(*) FROM roles")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO roles (name, description) VALUES (?, ?)",
                [
                    ('admin', 'Администратор системы'),
                    ('user', 'Обычный пользователь')
                ]
            )
            conn.commit()

        # Добавление демо-пользователей, если их нет
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Пароль для admin: Admin123
            admin_password_hash = hash_password('Admin123')
            # Пароль для user1: User12345
            user1_password_hash = hash_password('User12345')

            # Получаем ID ролей
            cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
            admin_role_id = cursor.fetchone()[0]

            cursor.execute("SELECT id FROM roles WHERE name = 'user'")
            user_role_id = cursor.fetchone()[0]

            cursor.executemany(
                '''INSERT INTO users 
                   (username, password_hash, first_name, last_name, role_id) 
                   VALUES (?, ?, ?, ?, ?)''',
                [
                    ('admin', admin_password_hash, 'Иван', 'Иванов', admin_role_id),
                    ('user1', user1_password_hash, 'Петр', 'Петров', user_role_id)
                ]
            )

        conn.commit()


@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def hash_password(password):
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """Проверка пароля"""
    return hash_password(password) == password_hash


# CRUD операции для пользователей
def create_user(username, password, first_name, last_name=None, middle_name=None, role_id=None):
    """Создание нового пользователя"""
    password_hash = hash_password(password)
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, last_name, first_name, 
                             middle_name, role_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, last_name, first_name, middle_name, role_id, created_at))
        conn.commit()
        return cursor.lastrowid


def get_all_users():
    """Получение всех пользователей с информацией о роли"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, r.name as role_name 
            FROM users u 
            LEFT JOIN roles r ON u.role_id = r.id
            ORDER BY u.id
        ''')
        return cursor.fetchall()


def get_user_by_id(user_id):
    """Получение пользователя по ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, r.name as role_name 
            FROM users u 
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.id = ?
        ''', (user_id,))
        return cursor.fetchone()


def get_user_by_username(username):
    """Получение пользователя по имени пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, r.name as role_name 
            FROM users u 
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.username = ?
        ''', (username,))
        return cursor.fetchone()


def update_user(user_id, first_name, last_name=None, middle_name=None, role_id=None):
    """Обновление данных пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET last_name = ?, first_name = ?, middle_name = ?, role_id = ?
            WHERE id = ?
        ''', (last_name, first_name, middle_name, role_id, user_id))
        conn.commit()
        return cursor.rowcount > 0


def update_user_profile(user_id, first_name, last_name=None, middle_name=None):
    """Обновление профиля пользователя (без изменения роли)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET last_name = ?, first_name = ?, middle_name = ?
            WHERE id = ?
        ''', (last_name, first_name, middle_name, user_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_user(user_id):
    """Удаление пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        return cursor.rowcount > 0


def change_password(user_id, new_password):
    """Изменение пароля пользователя"""
    password_hash = hash_password(new_password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?
            WHERE id = ?
        ''', (password_hash, user_id))
        conn.commit()
        return cursor.rowcount > 0


# Операции для ролей
def get_all_roles():
    """Получение всех ролей"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM roles ORDER BY id')
        return cursor.fetchall()


def get_role_by_id(role_id):
    """Получение роли по ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM roles WHERE id = ?', (role_id,))
        return cursor.fetchone()


# Операции для журнала посещений
def add_visit_log(path, user_id=None):
    """Добавление записи в журнал посещений"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO visit_logs (path, user_id, created_at)
            VALUES (?, ?, datetime('now'))
        ''', (path, user_id))
        conn.commit()
        return cursor.lastrowid


def get_visit_logs(page=1, per_page=20, user_id=None):
    """Получение журнала посещений с пагинацией"""
    offset = (page - 1) * per_page

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if user_id:
            cursor.execute('''
                SELECT COUNT(*) FROM visit_logs WHERE user_id = ?
            ''', (user_id,))
        else:
            cursor.execute('SELECT COUNT(*) FROM visit_logs')

        total = cursor.fetchone()[0]

        if user_id:
            cursor.execute('''
                SELECT vl.*, 
                       u.first_name || ' ' || u.last_name as user_name,
                       u.username
                FROM visit_logs vl
                LEFT JOIN users u ON vl.user_id = u.id
                WHERE vl.user_id = ?
                ORDER BY vl.created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, per_page, offset))
        else:
            cursor.execute('''
                SELECT vl.*, 
                       CASE 
                           WHEN u.id IS NULL THEN 'Неаутентифицированный пользователь'
                           ELSE u.first_name || ' ' || u.last_name
                       END as user_name,
                       u.username
                FROM visit_logs vl
                LEFT JOIN users u ON vl.user_id = u.id
                ORDER BY vl.created_at DESC
                LIMIT ? OFFSET ?
            ''', (per_page, offset))

        logs = cursor.fetchall()

        return {
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }


def get_page_stats():
    """Статистика посещений по страницам"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT path, COUNT(*) as visits
            FROM visit_logs
            GROUP BY path
            ORDER BY visits DESC
        ''')
        return cursor.fetchall()


def get_user_stats():
    """Статистика посещений по пользователям"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN u.id IS NULL THEN 'Неаутентифицированный пользователь'
                    ELSE u.first_name || ' ' || u.last_name
                END as user_name,
                COUNT(vl.id) as visits
            FROM visit_logs vl
            LEFT JOIN users u ON vl.user_id = u.id
            GROUP BY vl.user_id
            ORDER BY visits DESC
        ''')
        return cursor.fetchall()


def get_total_visits():
    """Общее количество посещений"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM visit_logs')
        return cursor.fetchone()[0]


def get_user_visit_stats(user_id):
    """Статистика посещений для конкретного пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as total_visits,
                   COUNT(DISTINCT path) as unique_pages
            FROM visit_logs
            WHERE user_id = ?
        ''', (user_id,))
        return cursor.fetchone()