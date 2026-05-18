import os
import requests # type: ignore
from flask import session # type: ignore
from config import API_BASE_URL


def _request(endpoint, method='GET', data=None, params=None, files=None):
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"

    if params:
        params = {k: v for k, v in params.items() if v is not None and v != ''}

    try:
        if files:
            clean_data = {k: str(v) for k, v in data.items()} if data else None
            response = requests.request(method, url, data=clean_data, files=files, params=params, timeout=30)
        elif data and method in ('POST', 'PUT'):
            response = requests.request(method, url, json=data, params=params, timeout=30)
        else:
            response = requests.request(method, url, params=params, timeout=30)

        if response.status_code == 200:
            return response.json()

        print(f"API Error [{response.status_code}] on {endpoint}: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Network error on {endpoint}: {e}")
        return None


# ---------- Auth ----------
def login_user_api(email, password):
    resp = _request('login', method='POST', data={'email': email, 'password': password})
    if resp and 'id' in resp:
        return resp, None
    return None, None


def register_user_api(full_name, email, password):
    return _request('register', method='POST', data={'full_name': full_name, 'email': email, 'password': password})


def get_user_by_id(user_id):
    return _request(f'users/{user_id}')


def update_user_bio(user_id, bio):
    return _request('update_bio', method='POST', data={'user_id': user_id, 'bio': bio})


def get_all_users():
    return _request('users') or []


def get_masters():
    users = get_all_users()
    return [u for u in users if u.get('role') == 'master']


# ---------- Sketches ----------
def get_sketches(page=1, per_page=8, filters=None, user_id=None, sort=None):
    params = {'page': page, 'per_page': per_page}
    if user_id:
        params['user_id'] = user_id
    if sort:
        params['sort'] = sort
    if filters:
        params.update(filters)

    data = _request('sketches', params=params)
    if data and isinstance(data, dict):
        return data.get('items', []), data.get('total', 0), data.get('page', page), data.get('pages', 1)
    return [], 0, page, 1


def get_sketch_detail(sketch_id, user_id=None):
    params = {'user_id': user_id} if user_id else None
    return _request(f'sketches/{sketch_id}', params=params)


def create_sketch_api(title, description, price, master_id, style, color_type, size, image_file):
    form_data = {
        'title': title,
        'description': description or '',
        'price': str(price),
        'master_id': str(master_id),
        'style': style,
        'color_type': color_type,
        'size': size
    }

    filename = getattr(image_file, 'filename', 'image.jpg') or 'image.jpg'
    stream = getattr(image_file, 'stream', image_file)
    content_type = getattr(image_file, 'content_type', 'image/jpeg') or 'image/jpeg'

    files = {
        'file': (filename, stream, content_type)
    }
    return _request('add_sketch', method='POST', data=form_data, files=files)


def delete_sketch_api(sketch_id, user_id):
    return _request(f'sketches/{sketch_id}', method='DELETE', params={'user_id': user_id})


# ---------- Time Slots ----------
def get_time_slots(master_id):
    return _request(f'time_slots/{master_id}') or []


def create_time_slot(master_id, start_time, end_time):
    data = {
        'master_id': int(master_id),
        'start_time': str(start_time),
        'end_time': str(end_time),
        'is_available': True
    }
    return _request('time_slots', method='POST', data=data)


def delete_time_slot(slot_id, master_id):
    return _request(f'time_slots/{slot_id}', method='DELETE', params={'master_id': master_id})


# ---------- Bookings ----------
def create_booking_api(user_id, master_id, slot_id, sketch_id=None, note=None):
    data = {
        'user_id': int(user_id),
        'master_id': int(master_id),
        'slot_id': int(slot_id),
        'sketch_id': int(sketch_id) if sketch_id else None,
        'note': note
    }
    return _request('bookings', method='POST', data=data)


def get_client_bookings(user_id):
    return _request('bookings', params={'user_id': user_id}) or []


def get_master_bookings(master_id):
    return _request('bookings_master', params={'master_id': master_id}) or []


def update_booking_status(booking_id, user_id, status):
    return _request(f'bookings/{booking_id}/status', method='POST',
                    data={'user_id': user_id, 'status': status})


# ---------- Favorites ----------
def toggle_favorite(user_id, sketch_id=None, master_id=None):
    params = {'user_id': user_id}
    if sketch_id:
        params['sketch_id'] = sketch_id
    if master_id:
        params['master_id'] = master_id
    return _request('toggle_favorite', method='POST', params=params)


def get_favorites(user_id):
    return _request(f'favorites/{user_id}') or {'sketches': [], 'masters': []}


# ---------- Recommendations ----------
def get_recommendations(sketch_id, user_id=None, limit=4):
    params = {'sketch_id': sketch_id, 'limit': limit}
    if user_id:
        params['user_id'] = user_id
    return _request('recommendations', params=params) or []