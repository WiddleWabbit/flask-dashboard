from flask_sqlalchemy import SQLAlchemy
from app.models import db

class Report(db.Model):
    __tablename__ = "report"
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    template_file = db.Column(db.String(100), nullable=False)
    js_file = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Integer, default=0)
    position = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<{self.name}>'
