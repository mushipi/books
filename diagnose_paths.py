from flask import Flask
import os
import glob
from models.location import Location
from models.genre import Genre
from models.tag import Tag
from models.book import db, Book

def create_app():
    """テスト用アプリケーションの作成"""
    app = Flask(__name__)
    
    # 設定の読み込み
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'books.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 静的ファイルの設定
    app.static_folder = 'static'
    app.static_url_path = ''
    
    # データベースの初期化
    db.init_app(app)
    
    return app

def diagnose_paths(app):
    """パスの問題を詳細に診断する"""
    with app.app_context():
        try:
            print("\n📚 表紙画像パスの詳細診断を実行します...\n")
            
            # データベース内の全書籍取得
            books = Book.query.all()
            print(f"データベース内の書籍数: {len(books)}冊")
            
            # 表紙画像が設定されている書籍
            books_with_cover = [book for book in books if book.cover_image_path]
            print(f"表紙画像パスが設定されている書籍: {len(books_with_cover)}冊")
            
            # 表紙画像ディレクトリ内のファイルを取得
            covers_dir = os.path.join('static', 'covers')
            image_files = []
            for ext in ['jpg', 'jpeg', 'png', 'gif']:
                image_files.extend(glob.glob(os.path.join(covers_dir, f"*.{ext}")))
            
            print(f"covers/ディレクトリ内の画像ファイル数: {len(image_files)}")
            print(f"covers/ディレクトリパス: {os.path.abspath(covers_dir)}")
            
            # 画像ファイル名のリスト
            image_filenames = [os.path.basename(img) for img in image_files]
            print(f"\n最初の5つの画像ファイル:")
            for i, filename in enumerate(image_filenames[:5]):
                print(f"  {i+1}. {filename}")
            
            # 正規化されたパスをチェック
            def normalize_path(path):
                if not path:
                    return None
                if path.startswith('/static/'):
                    path = path[8:]
                elif path.startswith('static/'):
                    path = path[7:]
                return path
            
            # データベース内のパスをチェック
            print("\n📊 データベース内のパス分析:")
            path_patterns = {}
            for book in books_with_cover:
                path = book.cover_image_path
                pattern = None
                
                if path.startswith('/static/covers/'):
                    pattern = "パターン1: /static/covers/[filename