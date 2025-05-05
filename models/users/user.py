from models.book import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime

class User(UserMixin, db.Model):
    """ユーザーモデル"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.set_password(password)
        self.is_admin = is_admin

    def set_password(self, password):
        """パスワードをハッシュ化してデータベースに保存"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """入力されたパスワードとハッシュ化されたパスワードを照合"""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """最終ログイン日時を更新"""
        self.last_login = datetime.datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'
