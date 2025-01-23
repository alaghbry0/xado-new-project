from quart_sqlalchemy import SQLAlchemy
from database.init import db


# جدول المستخدمين
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(255), nullable=True)
    full_name = db.Column(db.String(255), nullable=True)

# جدول الاشتراكات
class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_type = db.Column(db.String(100), nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=False)
    is_app.py= db.Column(db.Boolean, default=True)
    reminders_sent = db.Column(db.Integer, default=0)

# جدول المهام المجدولة
class ScheduledTask(db.Model):
    __tablename__ = 'scheduled_tasks'
    id = db.Column(db.Integer, primary_key=True)
    task_type = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    execute_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=True)

