from flask import Flask, url_for
import os
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

def debug_image_paths(app):
    """表紙画像パスのデバッグ情報"""
    with app.app_context():
        # ISBNでカバー画像がある書籍を検索
        book = Book.query.filter(Book.cover_image_path.isnot(None)).first()
        
        if book:
            print(f"\n書籍: {book.title}")
            print(f"ISBN: {book.isbn}")
            print(f"保存されているパス: {book.cover_image_path}")
            
            # 絶対パスを計算
            if book.cover_image_path:
                abs_path = os.path.join(app.static_folder, book.cover_image_path)
                print(f"絶対パス: {abs_path}")
                print(f"ファイルの存在: {os.path.exists(abs_path)}")
            
            # テスト用の関数を作成して実際のURLを生成
            def debug_view():
                pass
            
            app.add_url_rule('/debug', 'debug_view', debug_view)
            with app.test_request_context('/debug'):
                if book.cover_image_path:
                    url = url_for('static', filename=book.cover_image_path)
                    print(f"生成されるURL: {url}")
        else:
            print("カバー画像が設定された書籍が見つかりません")
        
        # 全ての書籍のカバー画像パスを確認
        books = Book.query.all()
        print("\n全書籍のカバー画像パス情報:")
        for i, book in enumerate(books):
            print(f"{i+1}. {book.title} - カバーパス: {book.cover_image_path}")
        
        # ファイルシステム上の実際の画像ファイルを確認
        covers_dir = os.path.join(app.static_folder, 'covers')
        print(f"\ncoversディレクトリの内容 ({covers_dir}):")
        if os.path.exists(covers_dir):
            files = os.listdir(covers_dir)
            for f in files:
                full_path = os.path.join(covers_dir, f)
                print(f" - {f} ({os.path.getsize(full_path)} bytes)")
        else:
            print("coversディレクトリが見つかりません")

if __name__ == '__main__':
    app = create_app()
    debug_image_paths(app)
    print("\n実行完了！")
