from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Ассоциативная таблица эскиз-тег
sketch_tags = db.Table('sketch_tags',
                       db.Column('sketch_id', db.Integer, db.ForeignKey('sketch.id'), primary_key=True),
                       db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
                       )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'client', 'master'
    name = db.Column(db.String(100), nullable=False)
    about = db.Column(db.Text, default='')
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)

    client_appointments = db.relationship('Appointment', foreign_keys='Appointment.client_id', backref='client',
                                          lazy=True)
    master_appointments = db.relationship('Appointment', foreign_keys='Appointment.master_id', backref='master',
                                          lazy=True)
    sketches = db.relationship('Sketch', backref='author', lazy=True)
    time_slots = db.relationship('TimeSlot', backref='master', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_master(self):
        return self.role == 'master'

    def is_client(self):
        return self.role == 'client'


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class Sketch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_file = db.Column(db.String(100), nullable=False)
    thumbnail_file = db.Column(db.String(100))
    style = db.Column(db.String(50))
    color_type = db.Column(db.String(20))
    size = db.Column(db.String(50))
    price = db.Column(db.Float)
    uploaded_on = db.Column(db.DateTime, default=datetime.utcnow)
    master_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tags = db.relationship('Tag', secondary=sketch_tags, lazy='subquery', backref=db.backref('sketches', lazy=True))


class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_available = db.Column(db.Boolean, default=True)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    master_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sketch_id = db.Column(db.Integer, db.ForeignKey('sketch.id'), nullable=True)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comment = db.Column(db.Text)

    time_slot = db.relationship('TimeSlot')
    sketch = db.relationship('Sketch')