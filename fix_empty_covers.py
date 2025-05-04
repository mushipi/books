from flask import Flask
import os
# 全てのモデルを正しい順序でインポートする
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
    
    # データベースの初期化
    db.init_app(app)
    
    return app

def fix_empty_cover_paths(app):
    """空の表紙画像パスの修正"""
    with app.app_context():
        try:
            # データベースの接続確認
            print("\nデータベース接続確認中...")
            book_count = Book.query.count()
            print(f"データベース内の合計書籍数: {book_count}\n")
            
            # 空文字列の表紙パスを持つ書籍を検索
            print("空の表紙パスを持つ書籍を検索中...")
            books_with_empty_path = Book.query.filter(Book.cover_image_path == '').all()
            print(f"空の表紙パスを持つ書籍: {len(books_with_empty_path)}冊\n")
            
            # 修正：空文字列をNoneに変更
            for book in books_with_empty_path:
                print(f"修正: {book.title} - パス: '{book.cover_image_path}' -> None")
                book.cover_image_path = None
            
            # 変更を保存
            if books_with_empty_path:
                db.session.commit()
                print(f"\n{len(books_with_empty_path)}冊の書籍のパスを修正しました。")
            else:
                print("\n修正すべき書籍はありませんでした。")
                
            # データの全体確認
            print("\nデータ確認:")
            null_cover_count = Book.query.filter(Book.cover_image_path == None).count()
            not_null_cover_count = Book.query.filter(Book.cover_image_path != None).count()
            print(f"表紙画像なし(空): {null_cover_count}冊")
            print(f"表紙画像あり: {not_null_cover_count}冊")
            
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            print("データベース接続やモデルの初期化に問題がある可能性があります。")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    app = create_app()
    fix_empty_cover_paths(app)
    print("\n実行完了！")
