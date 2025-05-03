from flask import Flask
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

def fix_cover_paths(app):
    """表紙画像パスの修正 - 最終版"""
    with app.app_context():
        # 全ての書籍を取得
        books = Book.query.all()
        print(f"合計 {len(books)} 冊の書籍があります")
        
        fixed_count = 0
        
        for book in books:
            isbn = book.isbn
            if not isbn:
                continue
            
            # ISBNから画像ファイル名を生成
            clean_isbn = isbn.replace("-", "")
            
            # 現在のパスと予想されるパスを出力
            print(f"\n書籍: {book.title}")
            print(f"ISBN: {isbn}")
            print(f"現在のパス: {book.cover_image_path}")
            
            # 画像ファイルの存在確認（異なるパスパターンを試す）
            possible_paths = [
                os.path.join(app.static_folder, 'covers', f"{clean_isbn}.jpg"),  # covers/isbn.jpg
                os.path.join('static', 'covers', f"{clean_isbn}.jpg"),  # static/covers/isbn.jpg
                os.path.abspath(os.path.join('covers', f"{clean_isbn}.jpg")),  # 絶対パス
            ]
            
            found_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    found_path = path
                    print(f"ファイルが見つかりました: {path}")
                    break
            
            if found_path:
                # 見つかったファイルから、適切な相対パスを設定
                # Flaskのurl_for('static', filename=...)に適したパス
                correct_path = os.path.join('covers', f"{clean_isbn}.jpg")
                
                if book.cover_image_path != correct_path:
                    print(f"パスを修正します: {book.cover_image_path} -> {correct_path}")
                    book.cover_image_path = correct_path
                    fixed_count += 1
                else:
                    print("パスは正しいです、修正は不要です")
            else:
                # 画像ファイルが見つからない場合
                print("画像ファイルが見つかりません。以下のパスを検索しました:")
                for path in possible_paths:
                    print(f" - {path}")
                
                # パスをNoneに設定（表示されなくする）
                if book.cover_image_path is not None:
                    print("表紙画像パスをクリアします")
                    book.cover_image_path = None
                    fixed_count += 1
        
        # 変更があれば保存
        if fixed_count > 0:
            print(f"\n{fixed_count}冊の書籍のパスを修正しました。変更を保存します。")
            db.session.commit()
        else:
            print("\n修正すべきパスはありませんでした。")

if __name__ == '__main__':
    app = create_app()
    fix_cover_paths(app)
    print("\n実行完了！")
