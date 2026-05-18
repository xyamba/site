import os
from flask import Flask, render_template, url_for, flash, redirect, request, abort, jsonify, session
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from datetime import datetime
from config import Config
from api_client import (
    API_BASE_URL,
    login_user_api, register_user_api, get_user_by_id, update_user_bio,
    get_sketches, get_sketch_detail, create_sketch_api, delete_sketch_api,
    create_booking_api, get_client_bookings, get_master_bookings,
    update_booking_status, get_masters, get_time_slots, create_time_slot,
    delete_time_slot, get_recommendations, toggle_favorite
)
from forms import (
    RegistrationForm, LoginForm, SketchUploadForm, SketchFilterForm,
    TimeSlotForm, AppointmentForm
)

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в аккаунт.'


@app.context_processor
def inject_api_url():
    return dict(API_BASE_URL=API_BASE_URL)


class ApiUser:
    def __init__(self, user_data):
        self.id = user_data['id']
        self.full_name = user_data.get('full_name', '')
        self.name = self.full_name
        self.email = user_data['email']
        self.role = user_data.get('role', 'user')
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def is_master(self): return self.role == 'master'

    def is_client(self): return self.role == 'user' or self.role == 'client'

    def is_admin(self): return self.role == 'admin'

    def get_id(self): return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    if 'user_id' not in session: return None
    user_data = get_user_by_id(int(user_id))
    return ApiUser(user_data) if user_data else None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/catalog')
def catalog():
    form = SketchFilterForm(request.args)
    page = request.args.get('page', 1, type=int)
    user_id = session.get('user_id')
    sort = request.args.get('sort') or 'date_desc'

    filters = {}
    if form.search.data: filters['search'] = form.search.data
    if form.style.data and form.style.data != 'all': filters['style'] = form.style.data
    if form.color_type.data and form.color_type.data != 'all': filters['color_type'] = form.color_type.data
    if form.size.data and form.size.data != 'all': filters['size'] = form.size.data
    if form.min_price.data: filters['min_price'] = form.min_price.data
    if form.max_price.data: filters['max_price'] = form.max_price.data
    if form.master_name.data: filters['master_name'] = form.master_name.data

    sketches, total, current_page, total_pages = get_sketches(
        page=page, per_page=8, filters=filters, user_id=user_id, sort=sort
    )

    pagination = None
    if total_pages > 1:
        pagination = {
            'page': current_page,
            'pages': total_pages,
            'has_prev': current_page > 1,
            'has_next': current_page < total_pages,
            'prev_num': current_page - 1,
            'next_num': current_page + 1,
        }
    return render_template('catalog.html', sketches=sketches, pagination=pagination, form=form, sort=sort)


@app.route('/sketch/<int:id>')
def sketch_detail(id):
    user_id = session.get('user_id')
    sketch = get_sketch_detail(id, user_id=user_id)
    if not sketch:
        abort(404)
    recommendations = get_recommendations(id, user_id=user_id)
    return render_template('sketch_detail.html', sketch=sketch, recommendations=recommendations)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_sketch():
    if not current_user.is_master():
        flash('Только тату-мастера могут добавлять эскизы.', 'danger')
        return redirect(url_for('catalog'))

    form = SketchUploadForm()

    if request.method == 'POST':
        # Прямое чтение параметров формы в обход строгой валидации WTForms
        title = request.form.get('title') or form.title.data
        description = request.form.get('description') or form.description.data
        price = request.form.get('price') or form.price.data

        # Проверяем все возможные варианты названий полей в HTML шаблоне
        style = request.form.get('style') or request.form.get('sketch_style') or form.style.data
        color_type = request.form.get('color_type') or request.form.get('color') or form.color_type.data
        size = request.form.get('size') or request.form.get('sketch_size') or form.size.data

        image_file = request.files.get('image') or request.files.get('file') or form.image.data

        if title and price and image_file:
            # Предотвращаем падение API из-за отсутствующих необязательных параметров
            style_str = str(style).lower() if style else 'графика'
            color_str = str(color_type).lower() if color_type else 'черно-белый'
            size_str = str(size).lower() if size else 'средний'

            # Корректируем русские названия под ожидания API бэкенда
            if 'цвет' in color_str: color_str = 'цветной'
            if 'черн' in color_str or 'ч/б' in color_str: color_str = 'черно-белый'

            resp = create_sketch_api(
                title=title,
                description=description,
                price=price,
                master_id=current_user.id,
                style=style_str,
                color_type=color_str,
                size=size_str,
                image_file=image_file
            )
            if resp:
                flash('Эскиз успешно добавлен и отправлен на модерацию!', 'success')
                return redirect(url_for('master_dashboard'))
            else:
                flash('Бэкенд-сервер отклонил сохранение эскиза.', 'danger')
        else:
            flash('Пожалуйста, заполните название, цену и выберите файл изображения.', 'danger')

    return render_template('upload_sketch.html', form=form)


@app.route('/master/dashboard')
@login_required
def master_dashboard():
    if not current_user.is_master():
        abort(403)
    bookings = get_master_bookings(current_user.id)
    sketches, _, _, _ = get_sketches(page=1, per_page=100)
    my_sketches = [s for s in sketches if s.get('master_id') == int(current_user.id)]
    slots = get_time_slots(current_user.id)
    return render_template('master_dashboard.html', appointments=bookings, sketches=my_sketches, slots=slots)


@app.route('/master/slots/add', methods=['GET', 'POST'])
@login_required
def add_slot():
    if not current_user.is_master():
        abort(403)
    form = TimeSlotForm()

    if request.method == 'POST':
        start_raw = request.form.get('start_time')
        end_raw = request.form.get('end_time')

        if start_raw and end_raw:
            # Удаляем символ 'T', который отправляет браузерный календарь, и заменяем на пробел
            start_clean = start_raw.replace('T', ' ').strip()
            end_clean = end_raw.replace('T', ' ').strip()

            # Если в строке нет секунд (длина 16 символов вида YYYY-MM-DD HH:MM), дополняем их
            if len(start_clean) == 16: start_clean += ":00"
            if len(end_clean) == 16: end_clean += ":00"

            resp = create_time_slot(current_user.id, start_clean, end_clean)
            if resp:
                flash('Слот времени добавлен в расписание!', 'success')
                return redirect(url_for('master_dashboard'))
            else:
                flash('Ошибка при записи слота на сервер.', 'danger')
        else:
            flash('Пожалуйста, заполните поля начала и окончания времени.', 'danger')

    return render_template('master_slots.html', form=form)


@app.route('/master/slot/delete/<int:slot_id>')
@login_required
def delete_slot(slot_id):
    if not current_user.is_master():
        abort(403)
    resp = delete_time_slot(slot_id, current_user.id)
    flash('Слот удалён.' if resp else 'Ошибка удаления слота.', 'success' if resp else 'danger')
    return redirect(url_for('master_dashboard'))


@app.route('/master/appointment/<int:id>/<action>')
@login_required
def handle_appointment(id, action):
    if not current_user.is_master():
        abort(403)
    new_status = 'confirmed' if action == 'confirm' else 'cancelled'
    resp = update_booking_status(id, current_user.id, new_status)
    flash('Статус обновлён.' if resp else 'Ошибка обновления статуса.', 'success' if resp else 'danger')
    return redirect(url_for('master_dashboard'))


@app.route('/appointment/new', methods=['GET', 'POST'])
@login_required
def new_appointment():
    if not current_user.is_client():
        flash('Только клиенты могут бронировать сеансы.', 'danger')
        return redirect(url_for('catalog'))
    form = AppointmentForm()
    masters = get_masters()
    form.master_id.choices = [(0, 'Выберите мастера')] + [(m['id'], m['full_name']) for m in masters]
    form.slot_id.choices = []
    sketches, _, _, _ = get_sketches(page=1, per_page=100)
    form.sketch_id.choices = [(0, 'Без эскиза')] + [(s['id'], s['title']) for s in sketches]

    if form.validate_on_submit():
        resp = create_booking_api(
            user_id=current_user.id,
            master_id=form.master_id.data,
            slot_id=form.slot_id.data,
            sketch_id=form.sketch_id.data if form.sketch_id.data != 0 else None,
            note=form.comment.data
        )
        if resp and 'id' in resp:
            flash('Запись успешно создана!', 'success')
        else:
            flash('Не удалось создать бронирование.', 'danger')
        return redirect(url_for('client_dashboard'))
    return render_template('appointment.html', form=form)


@app.route('/get_slots/<int:master_id>')
def get_slots_ajax(master_id):
    slots = get_time_slots(master_id)
    slots_data = [{'id': s['id'], 'start': s['start_time'], 'end': s['end_time']} for s in slots]
    return jsonify(slots_data)


@app.route('/client/dashboard')
@login_required
def client_dashboard():
    if not current_user.is_client():
        abort(403)
    bookings = get_client_bookings(current_user.id)
    return render_template('client_dashboard.html', appointments=bookings)


@app.route('/client/cancel_appointment/<int:id>')
@login_required
def cancel_appointment(id):
    resp = update_booking_status(id, current_user.id, 'cancelled')
    flash('Запись отменена.' if resp else 'Ошибка отмены.', 'success' if resp else 'danger')
    return redirect(url_for('client_dashboard'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        resp = register_user_api(form.name.data, form.email.data, form.password.data)
        if resp and 'id' in resp:
            flash('Вы успешно зарегистрировались!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email уже занят.', 'danger')
    return render_template('login_register.html', form=form, title='Регистрация', action='register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user_data, _ = login_user_api(form.email.data, form.password.data)
        if user_data:
            session['user_id'] = user_data['id']
            login_user(ApiUser(user_data), remember=True)
            flash('Успешный вход!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный email или пароль.', 'danger')
    return render_template('login_register.html', form=form, title='Вход', action='login')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    logout_user()
    return redirect(url_for('index'))


@app.route('/delete_sketch/<int:id>')
@login_required
def delete_sketch(id):
    if not current_user.is_master():
        abort(403)
    resp = delete_sketch_api(id, current_user.id)
    flash('Эскиз удалён.' if resp else 'Ошибка удаления эскиза.', 'success' if resp else 'danger')
    return redirect(url_for('master_dashboard'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)