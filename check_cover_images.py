from flask import Flask
import os
import glob
from models.location import Location
from models.genre import Genre
from models.tag import Tag
from models.book import db, Book
from helpers import cover_image_exists, get_cover_url

def create_app():
    """テスト用アプリケーションの作成"""
    app = Flask(__name__)
    
    # 設定の読み込み
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'books.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 静的ファイルの設定
    app.static_folder = 'static'
    app.static_url_path = '/static'
    
    # データベースの初期化
    db.init_app(app)
    
    return app

def check_cover_images(app):
    """表紙画像の状態を詳細にチェックし、問題があれば修正する"""
    with app.app_context():
        try:
            print("\n📚 表紙画像の状態チェックを実行します...")
            
            # 画像ディレクトリ内のファイル一覧取得
            covers_dir = os.path.join(app.static_folder, 'covers')
            print(f"表紙画像ディレクトリ: {covers_dir}")
            
            # ディレクトリが存在するか確認
            if not os.path.exists(covers_dir):
                print(f"❌ 表紙画像ディレクトリが存在しません: {covers_dir}")
                try:
                    os.makedirs(covers_dir)
                    print(f"✅ 表紙画像ディレクトリを作成しました: {covers_dir}")
                except Exception as e:
                    print(f"❌ ディレクトリ作成エラー: {e}")
                return
            
            # 画像ファイルを取得
            image_files = []
            for ext in ['jpg', 'jpeg', 'png', 'gif']:
                image_files.extend(glob.glob(os.path.join(covers_dir, f"*.{ext}")))
            
            print(f"📊 利用可能な表紙画像ファイル数: {len(image_files)}")
            
            # 画像ファイル一覧（最初の10個まで）
            if image_files:
                print("\n📋 画像ファイル一覧（最初の10個）:")
                for i, img_path in enumerate(image_files[:10]):
                    filename = os.path.basename(img_path)
                    size = os.path.getsize(img_path)
                    print(f"  {i+1}. {filename} ({size/1024:.1f} KB)")
                if len(image_files) > 10:
                    print(f"  ... 他 {len(image_files)-10} ファイル")
            
            # データベースの表紙画像パスを確認
            books = Book.query.all()
            books_with_cover = [book for book in books if book.cover_image_path]
            
            # パスの存在チェック
            valid_covers = []
            broken_links = []
            
            for book in books_with_cover:
                if cover_image_exists(book.cover_image_path):
                    valid_covers.append(book)
                else:
                    broken_links.append(book)
            
            print(f"\n📊 データベース内の書籍: {len(books)}冊")
            print(f"  - 表紙画像パスあり: {len(books_with_cover)}冊")
            print(f"  - 有効な表紙画像: {len(valid_covers)}冊")
            print(f"  - リンク切れ: {len(broken_links)}冊")
            
            # リンク切れの書籍一覧
            if broken_links:
                print("\n❌ リンク切れの書籍:")
                for i, book in enumerate(broken_links):
                    print(f"  {i+1}. 「{book.title}」- パス: {book.cover_image_path}")
                    
                # 自動修正の確認
                user_input = input("\n🛠️ リンク切れの表紙パスを自動的にNULLに修正しますか？(y/n): ")
                if user_input.lower() == 'y':
                    for book in broken_links:
                        print(f"  修正: 「{book.title}」- パス: {book.cover_image_path} -> NULL")
                        book.cover_image_path = None
                    
                    db.session.commit()
                    print(f"✅ {len(broken_links)}冊の書籍の表紙パスを修正しました")
                else:
                    print("⏩ 表紙パスの修正をスキップしました")
            
            # ISBNに基づく表紙画像の自動リンクチェック
            books_without_cover = [book for book in books if not book.cover_image_path]
            isbn_matches = []
            
            for book in books_without_cover:
                if book.isbn:
                    clean_isbn = book.isbn.replace("-", "")
                    for img_path in image_files:
                        filename = os.path.basename(img_path)
                        name_without_ext = os.path.splitext(filename)[0]
                        if name_without_ext == clean_isbn:
                            isbn_matches.append((book, os.path.join('covers', filename)))
            
            # マッチした表紙があれば表示
            if isbn_matches:
                print(f"\n🔍 ISBNにマッチする表紙画像が見つかりました: {len(isbn_matches)}冊")
                for i, (book, img_path) in enumerate(isbn_matches):
                    print(f"  {i+1}. 「{book.title}」- 画像: {img_path}")
                
                # 自動リンクの確認
                user_input = input("\n🛠️ これらの表紙画像を自動的にリンクしますか？(y/n): ")
                if user_input.lower() == 'y':
                    for book, img_path in isbn_matches:
                        book.cover_image_path = img_path
                        print(f"  リンク: 「{book.title}」-> {img_path}")
                    
                    db.session.commit()
                    print(f"✅ {len(isbn_matches)}冊の書籍に表紙画像をリンクしました")
                else:
                    print("⏩ 表紙画像の自動リンクをスキップしました")
        
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    app = create_app()
    check_cover_images(app)
    print("\n✅ チェック完了！")
