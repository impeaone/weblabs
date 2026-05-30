from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, asc
from sqlalchemy.orm import joinedload
from models import db, Course, Category, User, Review
from tools import CoursesFilter, ImageSaver

bp = Blueprint('courses', __name__, url_prefix='/courses')

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]


def params():
    return {p: request.form.get(p) or None for p in COURSE_PARAMS}


def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }


@bp.route('/')
def index():
    courses = CoursesFilter(**search_params()).perform()
    pagination = db.paginate(courses)
    courses = pagination.items
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())


@bp.route('/new')
@login_required
def new():
    course = Course()
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()
    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)


@bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = Course()
    try:
        if f and f.filename:
            img = ImageSaver(f).save()

        image_id = img.id if img else None
        course = Course(**params(), background_image_id=image_id)
        db.session.add(course)
        db.session.commit()
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        return render_template('courses/new.html',
                               categories=categories,
                               users=users,
                               course=course)

    flash(f'Курс {course.name} был успешно добавлен!', 'success')

    return redirect(url_for('courses.index'))


@bp.route('/<int:course_id>')
def show(course_id):
    course = db.get_or_404(Course, course_id)

    # Получаем 5 последних отзывов
    reviews = db.session.execute(
        db.select(Review)
        .filter_by(course_id=course_id)
        .options(joinedload(Review.user))
        .order_by(desc(Review.created_at))
        .limit(5)
    ).scalars()

    # Проверяем, оставил ли текущий пользователь отзыв
    user_review = None
    if current_user.is_authenticated:
        user_review = db.session.execute(
            db.select(Review)
            .filter_by(course_id=course_id, user_id=current_user.id)
            .options(joinedload(Review.user))
        ).scalar()

    return render_template('courses/show.html',
                           course=course,
                           reviews=reviews,
                           user_review=user_review)


@bp.route('/<int:course_id>/reviews')
def reviews(course_id):
    course = db.get_or_404(Course, course_id)

    # Получаем параметры фильтрации и пагинации
    sort_type = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Строим базовый запрос
    query = db.select(Review).filter_by(course_id=course_id).options(joinedload(Review.user))

    # Применяем сортировку
    if sort_type == 'positive':
        query = query.order_by(desc(Review.rating), desc(Review.created_at))
    elif sort_type == 'negative':
        query = query.order_by(asc(Review.rating), desc(Review.created_at))
    else:  # newest (по умолчанию)
        query = query.order_by(desc(Review.created_at))

    # Пагинация
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    reviews_list = pagination.items

    # Проверяем, оставил ли текущий пользователь отзыв
    user_review = None
    if current_user.is_authenticated:
        user_review = db.session.execute(
            db.select(Review)
            .filter_by(course_id=course_id, user_id=current_user.id)
        ).scalar()

    return render_template('courses/reviews.html',
                           course=course,
                           reviews=reviews_list,
                           user_review=user_review,
                           pagination=pagination,
                           sort_type=sort_type)


@bp.route('/<int:course_id>/reviews/create', methods=['POST'])
@login_required
def create_review(course_id):
    course = db.get_or_404(Course, course_id)

    # Проверяем, не оставил ли уже пользователь отзыв
    existing_review = db.session.execute(
        db.select(Review)
        .filter_by(course_id=course_id, user_id=current_user.id)
    ).scalar()

    if existing_review:
        flash('Вы уже оставили отзыв на этот курс.', 'warning')
        return redirect(url_for('courses.show', course_id=course_id))

    # Получаем данные из формы
    rating = request.form.get('rating')
    text = request.form.get('text', '').strip()

    if not rating:
        flash('Выберите оценку.', 'danger')
        return redirect(url_for('courses.show', course_id=course_id))

    if not text:
        flash('Введите текст отзыва.', 'danger')
        return redirect(url_for('courses.show', course_id=course_id))

    try:
        rating = int(rating)
        if rating < 0 or rating > 5:
            raise ValueError
    except ValueError:
        flash('Оценка должна быть целым числом от 0 до 5.', 'danger')
        return redirect(url_for('courses.show', course_id=course_id))

    # Создаем отзыв
    review = Review(
        rating=rating,
        text=text,
        course_id=course_id,
        user_id=current_user.id
    )

    # Обновляем рейтинг курса
    course.rating_sum += rating
    course.rating_num += 1

    try:
        db.session.add(review)
        db.session.commit()
        flash('Ваш отзыв успешно добавлен!', 'success')
    except IntegrityError as err:
        db.session.rollback()
        flash(f'Произошла ошибка при сохранении отзыва: {err}', 'danger')

    # Определяем, откуда пришел запрос
    if request.referrer and 'reviews' in request.referrer:
        return redirect(url_for('courses.reviews', course_id=course_id))
    else:
        return redirect(url_for('courses.show', course_id=course_id))