from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

# user table


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    first_name = db.Column(db.String(150))
    surname = db.Column(db.String(150))
    mobile = db.Column(db.String(150))
    password = db.Column(db.String(150))
    vehicle = db.relationship('Vehicle')

# table of vehicles registered


class Vehicle(db.Model):
    vehicle_id = db.Column(db.Integer, primary_key=True)
    license_plate = db.Column(db.String(12), unique=True)
    make = db.Column(db.String(150))
    type = db.Column(db.String(150))
    engine_type = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    order = db.relationship('Order')

# table of orders


class Order(db.Model):
    order_number = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(150))
    price = db.Column(db.Integer)
    status = db.Column(db.String(150))
    parts = db.Column(db.String(150))
    comments = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.vehicle_id'))
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'))
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.booking_id'))

# staff table


class Staff(db.Model):
    staff_id = db.Column(db.Integer, primary_key=True)
    staff_first_name = db.Column(db.String(150))
    staff_surname = db.Column(db.String(150))
    role = db.Column(db.String(150))
    order = db.relationship('Order')

# table of all bookings made


class Booking(db.Model):
    booking_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    order_id = db.relationship('Order', backref='booking', uselist=False)
