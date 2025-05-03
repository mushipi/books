from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 書籍とジャンルの中間テーブル
book_genre = db.Table('book_genre',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True)
)

# 書籍とタグの中間テーブル
book_tag = db.Table('book_tag',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    publisher = db.Column(db.String(100))
    isbn = db.Column(db.String(20))
    jan_code = db.Column(db.String(20))
    published_date = db.Column(db.String(20))
    price = db.Column(db.Integer)
    page_count = db.Column(db.Integer)
    cover_image_path = db.Column(db.String(255), nullable=True, default=None)
    added_date = db.Column(db.String(20), nullable=False, default=datetime.now().strftime('%Y-%m-%d'))
    memo = db.Column(db.Text)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    
    # リレーションシップ
    location = db.relationship('Location', backref='books')
    genres = db.relationship('Genre', secondary=book_genre, backref=db.backref('books', lazy='dynamic'))
    tags = db.relationship('Tag', secondary=book_tag, backref=db.backref('books', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Book {self.title}>'
