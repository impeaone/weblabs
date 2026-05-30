import re


def validate_username(username):
    """Валидация имени пользователя"""
    errors = []

    if not username:
        errors.append("Поле не может быть пустым")
    elif len(username) < 5:
        errors.append("Логин должен содержать не менее 5 символов")
    elif not re.match(r'^[a-zA-Z0-9]+$', username):
        errors.append("Логин должен содержать только латинские буквы и цифры")

    return errors


def validate_password(password, confirm_password=None, is_change=False, old_password=None):
    """Валидация пароля"""
    errors = []

    if not is_change and not password:
        errors.append("Поле не может быть пустым")

    if password:
        # Проверка длины
        if len(password) < 8:
            errors.append("Пароль должен содержать не менее 8 символов")
        elif len(password) > 128:
            errors.append("Пароль должен содержать не более 128 символов")

        # Проверка на пробелы
        if ' ' in password:
            errors.append("Пароль не должен содержать пробелов")

        # Проверка на наличие хотя бы одной цифры
        if not re.search(r'\d', password):
            errors.append("Пароль должен содержать хотя бы одну цифру")

        # Проверка на наличие заглавных и строчных букв
        if not (re.search(r'[A-ZА-Я]', password) and re.search(r'[a-zа-я]', password)):
            errors.append("Пароль должен содержать как минимум одну заглавную и одну строчную букву")

        # Проверка допустимых символов
        allowed_pattern = r'^[a-zA-Zа-яА-Я0-9~!?@#$%^&*_\-+()\[\]{}><\/\\|"\'\.,:;]+$'
        if not re.match(allowed_pattern, password):
            errors.append("Пароль содержит недопустимые символы")

        # Проверка соответствия подтверждения пароля
        if confirm_password is not None and password != confirm_password:
            errors.append("Пароли не совпадают")

    return errors


def validate_name(field_name, value, required=True):
    """Валидация имени, фамилии, отчества"""
    errors = []

    if required and not value:
        errors.append("Поле не может быть пустым")
    elif value and not re.match(r'^[a-zA-Zа-яА-ЯёЁ\- ]+$', value):
        errors.append("Может содержать только буквы, дефисы и пробелы")

    return errors


def validate_user_data(data, is_edit=False):
    """Комплексная валидация данных пользователя"""
    errors = {}

    if not is_edit:
        username_errors = validate_username(data.get('username'))
        if username_errors:
            errors['username'] = username_errors

        password_errors = validate_password(data.get('password'))
        if password_errors:
            errors['password'] = password_errors

    first_name_errors = validate_name('first_name', data.get('first_name'))
    if first_name_errors:
        errors['first_name'] = first_name_errors

    last_name_errors = validate_name('last_name', data.get('last_name'), required=False)
    if last_name_errors:
        errors['last_name'] = last_name_errors

    middle_name_errors = validate_name('middle_name', data.get('middle_name'), required=False)
    if middle_name_errors:
        errors['middle_name'] = middle_name_errors

    return errors