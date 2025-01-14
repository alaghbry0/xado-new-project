from models import db, app

with app.app_context():
    db.create_all()
    print("تم إنشاء الجداول بنجاح!")
