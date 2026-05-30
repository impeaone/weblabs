from flask import Flask, render_template, request
import re

app = Flask(__name__)
app.secret_key = 'sedlokpjrntggoipkjwegiop34rfgipjo234tjio0p342jioperwoipjkr32e34'


@app.route('/')
def index():
    """Главная страница с навигацией"""
    return render_template('base.html')


@app.route('/request-info')
def request_info():
    """Страница с отображением параметров запроса"""
    # Получаем все данные запроса
    url_params = dict(request.args)
    headers = dict(request.headers)
    cookies = dict(request.cookies)

    return render_template('request_info.html',
                           url_params=url_params,
                           headers=headers,
                           cookies=cookies)


@app.route('/auth-form', methods=['GET'])
def auth_form():
    """Страница с формой авторизации"""
    return render_template('auth_form.html')


@app.route('/auth-submit', methods=['POST'])
def auth_submit():
    """Обработка формы авторизации"""
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    return render_template('auth_result.html',
                           username=username,
                           password=password)


@app.route('/phone-form', methods=['GET'])
def phone_form():
    """Страница с формой для ввода номера телефона"""
    return render_template('phone_form.html')


@app.route('/phone-validate', methods=['POST'])
def phone_validate():
    """Валидация номера телефона"""
    phone_input = request.form.get('phone', '')
    error_message = None
    formatted_phone = None
    is_valid = False

    if phone_input:
        # Удаляем все допустимые нецифровые символы
        cleaned = re.sub(r'[\s\(\)\-\.\+]', '', phone_input)

        # Проверка на недопустимые символы
        if not re.match(r'^[\d\s\(\)\-\.\+]+$', phone_input):
            error_message = 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'
        # Проверка длины
        elif len(cleaned) not in [10, 11]:
            error_message = 'Недопустимый ввод. Неверное количество цифр.'
        else:
            # Проверка специфических случаев
            if len(cleaned) == 11:
                if not (phone_input.startswith('+7') or phone_input.startswith('8') or
                        cleaned.startswith('7') or cleaned.startswith('8')):
                    error_message = 'Недопустимый ввод. Неверное количество цифр.'
                else:
                    is_valid = True
            elif len(cleaned) == 10:
                is_valid = True

            if is_valid:
                # Форматируем номер
                if len(cleaned) == 11:
                    if cleaned.startswith('7') or cleaned.startswith('8'):
                        digits = cleaned[1:]  # Убираем первую цифру (7 или 8)
                    else:
                        digits = cleaned
                else:
                    digits = cleaned

                # Формат: 8-***-***-**-**
                formatted_phone = f"8-{digits[:3]}-{digits[3:6]}-{digits[6:8]}-{digits[8:]}"

    return render_template('phone_result.html',
                           phone_input=phone_input,
                           formatted_phone=formatted_phone,
                           error_message=error_message,
                           is_valid=is_valid)


if __name__ == '__main__':
    app.run(debug=True, port=5000)