from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Декоратор для проверки аутентификации"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Для доступа к этой странице необходимо войти в систему', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def check_rights(*required_roles):
    """Декоратор для проверки прав пользователя"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Для доступа к этой странице необходимо войти в систему', 'error')
                return redirect(url_for('login'))

            user_role = session.get('role_name')

            if not user_role or user_role not in required_roles:
                flash('У вас недостаточно прав для доступа к данной странице.', 'error')
                return redirect(url_for('index'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def check_auth(username, password):
    """Проверка учетных данных"""
    import database
    user = database.get_user_by_username(username)
    if user and database.verify_password(password, user['password_hash']):
        return user
    return None


def login_user(user):
    """Вход пользователя в систему"""
    import database
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['first_name'] = user['first_name']
    session['last_name'] = user['last_name']
    session['role_id'] = user['role_id']

    # Сохраняем название роли для удобства
    if user['role_id']:
        role = database.get_role_by_id(user['role_id'])
        if role:
            session['role_name'] = role['name']
            session['role_description'] = role['description']


def logout_user():
    """Выход пользователя из системы"""
    session.clear()


def get_current_user():
    """Получение текущего пользователя"""
    import database
    if 'user_id' in session:
        return database.get_user_by_id(session['user_id'])
    return None


def is_admin():
    """Проверка, является ли текущий пользователь администратором"""
    return session.get('role_name') == 'admin'


def can_create_users():
    """Проверка прав на создание пользователей"""
    return is_admin()


def can_edit_users():
    """Проверка прав на редактирование пользователей"""
    return is_admin()


def can_delete_users():
    """Проверка прав на удаление пользователей"""
    return is_admin()


def can_view_all_logs():
    """Проверка прав на просмотр всех логов"""
    return is_admin()


def can_edit_own_profile(user_id):
    """Проверка, может ли пользователь редактировать свой профиль"""
    if 'user_id' not in session:
        return False
    return session['user_id'] == user_id or is_admin()