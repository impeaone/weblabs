from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "sdgergewrgrwlfgwerlgwerlgwerlg"
# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице необходимо авторизоваться'
login_manager.login_message_category = 'warning'


# Модель пользователя
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash


# Пользователи
users = {
    1: User(1, 'user', generate_password_hash('qwerty'))
}


@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))


# Главная страница
@app.route('/')
def index():
    return render_template('index.html')


# Страница счетчика посещений
@app.route('/counter')
def counter():
    # Инициализируем счетчик в сессии если его нет
    if 'visit_count' not in session:
        session['visit_count'] = 0
    # Увеличиваем счетчик
    session['visit_count'] = session['visit_count'] + 1
    # Сохраняем сессию
    session.modified = True

    last_visit = session.get('last_visit', 'Это ваш первый визит!')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    session['last_visit'] = current_time

    return render_template('counter.html',
                           count=session['visit_count'],
                           last_visit=last_visit)


# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        # Поиск пользователя
        user = None
        for u in users.values():
            if u.username == username:
                user = u
                break

        # Проверка пользователя и пароля
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash('Вы успешно вошли в систему!', 'success')

            # Перенаправление на запрашиваемую страницу или главную
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html')


# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('index'))


# Секретная страница (только для авторизованных)
@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')


# API для сброса счетчика
@app.route('/reset-counter')
def reset_counter():
    if 'visit_count' in session:
        session.pop('visit_count')
        session.pop('last_visit', None)
        flash('Счетчик посещений сброшен', 'info')
    return redirect(url_for('counter'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)