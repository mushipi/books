from flask import Flask
import os
from models.book import db, Book
from models.location import Location
from models.genre import Genre
from models.tag import Tag

def create_app():
    """テスト用アプリケーションの作成"""
    app = Flask(__name__)
    
    # 設定の読み込み
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'books.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # データベースの初期化
    db.init_app(app)
    
    return app

def check_image_paths(app):
    """表紙画像パスの簡易確認"""
    with app.app_context():
        # 全ての書籍を取得
        books = Book.query.all()
        print(f"合計 {len(books)} 冊の書籍があります")
        
        # カバー画像のあるものを確認
        books_with_cover = 0
        for book in books:
            if book.cover_image_path:
                books_with_cover += 1
                print(f"\n書籍ID: {book.id}")
                print(f"タイトル: {book.title}")
                print(f"ISBN: {book.isbn}")
                print(f"カバー画像パス: {book.cover_image_path}")
                
                # 画像ファイルの存在確認
                image_path = os.path.join('static', book.cover_image_path)
                if os.path.exists(image_path):
                    print(f"画像ファイルは存在します: {image_path}")
                else:
                    print(f"画像ファイルが見つかりません: {image_path}")
        
        if books_with_cover == 0:
            print("\nカバー画像が設定された書籍が見つかりません")

if __name__ == '__main__':
    app = create_app()
    check_image_paths(app)
    print("\n実行完了！")
