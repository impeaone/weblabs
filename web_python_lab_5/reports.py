from flask import Blueprint, render_template, request, send_file, session, flash, redirect, url_for
import database
import auth
import csv
import io
from datetime import datetime

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/visit_logs')
@auth.login_required
@auth.check_rights('admin', 'user')
def visit_logs():
    """Страница журнала посещений"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Проверяем права
    if auth.is_admin():
        # Администратор видит все логи
        logs_data = database.get_visit_logs(page, per_page)
    else:
        # Обычный пользователь видит только свои логи
        user_id = session.get('user_id')
        logs_data = database.get_visit_logs(page, per_page, user_id)

    return render_template('visit_logs.html',
                           logs=logs_data['logs'],
                           page=logs_data['page'],
                           pages=logs_data['pages'],
                           total=logs_data['total'])


@reports_bp.route('/page_stats')
@auth.login_required
@auth.check_rights('admin')
def page_stats():
    """Статистика по страницам (только для администраторов)"""
    stats = database.get_page_stats()
    return render_template('page_stats.html', stats=stats)


@reports_bp.route('/user_stats')
@auth.login_required
@auth.check_rights('admin')
def user_stats():
    """Статистика по пользователям (только для администраторов)"""
    stats = database.get_user_stats()
    return render_template('user_stats.html', stats=stats)


@reports_bp.route('/page_stats/export')
@auth.login_required
@auth.check_rights('admin')
def export_page_stats():
    """Экспорт статистики по страницам в CSV"""
    stats = database.get_page_stats()

    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовки
    writer.writerow(['№', 'Страница', 'Количество посещений'])

    # Данные
    for i, row in enumerate(stats, 1):
        writer.writerow([i, row['path'], row['visits']])

    # Подготавливаем файл для отправки
    output.seek(0)

    # Создаем имя файла с текущей датой
    filename = f'page_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@reports_bp.route('/user_stats/export')
@auth.login_required
@auth.check_rights('admin')
def export_user_stats():
    """Экспорт статистики по пользователям в CSV"""
    stats = database.get_user_stats()

    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовки
    writer.writerow(['№', 'Пользователь', 'Количество посещений'])

    # Данные
    for i, row in enumerate(stats, 1):
        writer.writerow([i, row['user_name'], row['visits']])

    # Подготавливаем файл для отправки
    output.seek(0)

    # Создаем имя файла с текущей датой
    filename = f'user_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )