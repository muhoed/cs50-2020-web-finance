from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime

db = SQLAlchemy()

# map tables to classes
class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    hash = db.Column(db.String, nullable=False)
    cash = db.Column(db.Float, nullable=False, default=10000.00)

class Transactions(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    name = db.Column(db.Text, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.TIMESTAMP, nullable=False, default=text('CURRENT_TIMESTAMP')) # datetime.utcnow)
    type = db.Column(db.String(4), nullable=False)
    users = db.relationship('Users', backref=db.backref('transactions', lazy=True))