from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import database
import auth
import validation
import logs
from reports import reports_bp

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-in-production'
app.config['DATABASE'] = 'users.db'

# Регистрация Blueprint
app.register_blueprint(reports_bp)

# Инициализация базы данных
with app.app_context():
    database.init_db()

# Инициализация логирования
logs.init_logging(app)


# Главная страница - список пользователей
@app.route('/')
def index():
    users = database.get_all_users()
    current_user = auth.get_current_user()

    # Получаем статистику для текущего пользователя
    user_stats = None
    if current_user:
        user_stats = database.get_user_visit_stats(current_user['id'])

    return render_template('index.html',
                           users=users,
                           current_user=current_user,
                           user_stats=user_stats,
                           auth=auth)


# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = auth.check_auth(username, password)
        if user:
            auth.login_user(user)
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


# Выход
@app.route('/logout')
def logout():
    auth.logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


# Просмотр пользователя
@app.route('/user/<int:user_id>')
def view_user(user_id):
    user = database.get_user_by_id(user_id)
    if not user:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('index'))

    # Проверяем права - пользователь может смотреть только свой профиль или быть администратором
    current_user = auth.get_current_user()
    if not current_user or (current_user['id'] != user_id and not auth.is_admin()):
        flash('У вас недостаточно прав для просмотра этого профиля', 'error')
        return redirect(url_for('index'))

    return render_template('view_user.html', user=user)


# Создание пользователя (только для администраторов)
@app.route('/user/create', methods=['GET', 'POST'])
@auth.login_required
@auth.check_rights('admin')
def create_user():
    if request.method == 'POST':
        # Получение данных из формы
        user_data = {
            'username': request.form.get('username'),
            'password': request.form.get('password'),
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'middle_name': request.form.get('middle_name'),
            'role_id': request.form.get('role_id') or None
        }

        # Валидация
        errors = validation.validate_user_data(user_data, is_edit=False)

        # Проверка уникальности логина
        if not errors.get('username'):
            existing_user = database.get_user_by_username(user_data['username'])
            if existing_user:
                errors['username'] = ['Пользователь с таким логином уже существует']

        if errors:
            roles = database.get_all_roles()
            return render_template('user_form.html',
                                   errors=errors,
                                   form_data=user_data,
                                   roles=roles,
                                   is_edit=False,
                                   is_admin_form=True)

        try:
            # Создание пользователя
            user_id = database.create_user(
                username=user_data['username'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                middle_name=user_data['middle_name'],
                role_id=user_data['role_id']
            )

            flash('Пользователь успешно создан', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Ошибка при создании пользователя: {str(e)}', 'error')
            roles = database.get_all_roles()
            return render_template('user_form.html',
                                   errors={},
                                   form_data=user_data,
                                   roles=roles,
                                   is_edit=False,
                                   is_admin_form=True)

    # GET запрос - отображение формы
    roles = database.get_all_roles()
    return render_template('user_form.html',
                           errors={},
                           form_data={},
                           roles=roles,
                           is_edit=False,
                           is_admin_form=True)


# Редактирование профиля (для пользователей - только своих данных)
@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@auth.login_required
def edit_user(user_id):
    user = database.get_user_by_id(user_id)
    if not user:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('index'))

    current_user = auth.get_current_user()

    # Проверяем права
    if not auth.can_edit_own_profile(user_id):
        flash('У вас недостаточно прав для редактирования этого профиля', 'error')
        return redirect(url_for('index'))

    # Определяем, является ли это формой администратора
    is_admin_form = auth.is_admin() and current_user['id'] != user_id

    if request.method == 'POST':
        if is_admin_form:
            # Администратор редактирует другого пользователя
            user_data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'middle_name': request.form.get('middle_name'),
                'role_id': request.form.get('role_id') or None
            }

            # Валидация
            errors = validation.validate_user_data(user_data, is_edit=True)

            if errors:
                roles = database.get_all_roles()
                return render_template('user_form.html',
                                       errors=errors,
                                       form_data={**user_data, 'id': user_id},
                                       roles=roles,
                                       is_edit=True,
                                       is_admin_form=True,
                                       user=user)

            try:
                # Обновление пользователя
                success = database.update_user(
                    user_id=user_id,
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    middle_name=user_data['middle_name'],
                    role_id=user_data['role_id']
                )

                if success:
                    flash('Данные пользователя успешно обновлены', 'success')
                else:
                    flash('Пользователь не найден', 'error')

                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Ошибка при обновлении пользователя: {str(e)}', 'error')
                roles = database.get_all_roles()
                return render_template('user_form.html',
                                       errors={},
                                       form_data={**user_data, 'id': user_id},
                                       roles=roles,
                                       is_edit=True,
                                       is_admin_form=True,
                                       user=user)
        else:
            # Пользователь редактирует свой профиль
            user_data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'middle_name': request.form.get('middle_name')
            }

            # Валидация
            errors = validation.validate_user_data(user_data, is_edit=True)

            if errors:
                return render_template('user_form.html',
                                       errors=errors,
                                       form_data={**user_data, 'id': user_id},
                                       roles=[],
                                       is_edit=True,
                                       is_admin_form=False,
                                       user=user)

            try:
                # Обновление профиля (без изменения роли)
                success = database.update_user_profile(
                    user_id=user_id,
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    middle_name=user_data['middle_name']
                )

                if success:
                    # Обновляем сессию
                    session['first_name'] = user_data['first_name']
                    session['last_name'] = user_data['last_name']
                    flash('Ваш профиль успешно обновлен', 'success')
                else:
                    flash('Пользователь не найден', 'error')

                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Ошибка при обновлении профиля: {str(e)}', 'error')
                return render_template('user_form.html',
                                       errors={},
                                       form_data={**user_data, 'id': user_id},
                                       roles=[],
                                       is_edit=True,
                                       is_admin_form=False,
                                       user=user)

    # GET запрос - отображение формы с текущими данными
    if is_admin_form:
        roles = database.get_all_roles()
        form_data = {
            'id': user['id'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'middle_name': user['middle_name'],
            'role_id': user['role_id']
        }

        return render_template('user_form.html',
                               errors={},
                               form_data=form_data,
                               roles=roles,
                               is_edit=True,
                               is_admin_form=True,
                               user=user)
    else:
        form_data = {
            'id': user['id'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'middle_name': user['middle_name']
        }

        return render_template('user_form.html',
                               errors={},
                               form_data=form_data,
                               roles=[],
                               is_edit=True,
                               is_admin_form=False,
                               user=user)


# Удаление пользователя (только для администраторов)
@app.route('/user/<int:user_id>/delete', methods=['POST'])
@auth.login_required
@auth.check_rights('admin')
def delete_user(user_id):
    try:
        user = database.get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})

        # Нельзя удалить самого себя
        current_user = auth.get_current_user()
        if current_user and current_user['id'] == user_id:
            return jsonify({'success': False, 'message': 'Нельзя удалить свою учетную запись'})

        success = database.delete_user(user_id)
        if success:
            return jsonify({'success': True, 'message': 'Пользователь успешно удален'})
        else:
            return jsonify({'success': False, 'message': 'Ошибка при удалении пользователя'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})


# Изменение пароля
@app.route('/change-password', methods=['GET', 'POST'])
@auth.login_required
def change_password():
    current_user = auth.get_current_user()

    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Проверка старого пароля
        if not database.verify_password(old_password, current_user['password_hash']):
            flash('Неверный старый пароль', 'error')
            return render_template('change_password.html')

        # Валидация нового пароля
        errors = validation.validate_password(new_password, confirm_password, is_change=True)

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('change_password.html')

        try:
            # Смена пароля
            success = database.change_password(current_user['id'], new_password)
            if success:
                flash('Пароль успешно изменен', 'success')
                return redirect(url_for('index'))
            else:
                flash('Ошибка при изменении пароля', 'error')
        except Exception as e:
            flash(f'Ошибка: {str(e)}', 'error')

    return render_template('change_password.html')


if __name__ == '__main__':
    app.run(debug=True)