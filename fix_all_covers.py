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
    
    # データベースの初期化
    db.init_app(app)
    
    return app

def scan_cover_images():
    """表紙画像ファイルをスキャンして利用可能なISBNを取得する"""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    covers_dir = os.path.join(base_dir, 'static', 'covers')
    
    # ディレクトリの存在確認
    if not os.path.exists(covers_dir):
        print(f"エラー: 表紙画像ディレクトリが存在しません: {covers_dir}")
        return {}
    
    # 画像ファイルの検索
    cover_files = {}
    for ext in ['jpg', 'jpeg', 'png', 'gif']:
        pattern = os.path.join(covers_dir, f"*.{ext}")
        found = glob.glob(pattern)
        print(f"  - {ext}: {len(found)}ファイル")
        
        for img_path in found:
            filename = os.path.basename(img_path)
            isbn = os.path.splitext(filename)[0]
            cover_files[isbn] = {
                'path': img_path,
                'rel_path': os.path.join('covers', filename),
                'size': os.path.getsize(img_path)
            }
    
    print(f"合計: {len(cover_files)}ファイル")
    return cover_files

def fix_cover_paths(app):
    """表紙画像パスの総合修正"""
    # 利用可能な表紙画像ファイルのスキャン
    print("表紙画像ファイルをスキャンしています...")
    available_covers = scan_cover_images()
    
    with app.app_context():
        # データベース内の全書籍を取得
        books = Book.query.all()
        print(f"\nデータベース内の書籍数: {len(books)}冊")
        
        # 問題カウンター
        fixed_count = 0
        linked_count = 0
        already_ok = 0
        no_isbn = 0
        invalid_cleared = 0
        
        # 各書籍の表紙画像パスを確認
        for book in books:
            isbn = book.isbn
            if not isbn:
                no_isbn += 1
                continue
            
            # ISBNの正規化
            clean_isbn = isbn.replace('-', '')
            current_path = book.cover_image_path
            
            # 現在のパスが有効かチェック
            static_path = os.path.join('static', current_path) if current_path else None
            path_valid = static_path and os.path.isfile(static_path)
            
            # 対応する表紙画像があるかチェック
            if clean_isbn in available_covers:
                cover_info = available_covers[clean_isbn]
                expected_path = cover_info['rel_path']
                
                if not path_valid:
                    # パスが無効なので更新
                    book.cover_image_path = expected_path
                    print(f"リンク: 「{book.title}」-> {expected_path}")
                    linked_count += 1
                elif current_path != expected_path:
                    # パスが正しくないので更新
                    book.cover_image_path = expected_path
                    print(f"修正: 「{book.title}」- {current_path} -> {expected_path}")
                    fixed_count += 1
                else:
                    # パスは正しい
                    already_ok += 1
            elif current_path:
                # ISBNに対応する表紙画像がなくて、現在のパスも無効
                if not path_valid:
                    print(f"クリア: 「{book.title}」- 無効なパス: {current_path}")
                    book.cover_image_path = None
                    invalid_cleared += 1
        
        # 変更を保存
        if fixed_count + linked_count + invalid_cleared > 0:
            db.session.commit()
            print(f"\n変更を保存しました。")
        else:
            print("\n変更はありませんでした。")
        
        # 結果サマリー
        print("\n=== 修正結果 ===")
        print(f"正常なパス: {already_ok}冊")
        print(f"パス修正: {fixed_count}冊")
        print(f"新規リンク: {linked_count}冊")
        print(f"無効パスクリア: {invalid_cleared}冊")
        print(f"ISBNなし: {no_isbn}冊")
        print(f"合計: {already_ok + fixed_count + linked_count + invalid_cleared + no_isbn}冊")

if __name__ == "__main__":
    print("表紙画像パスの総合修正を実行します...")
    app = create_app()
    fix_cover_paths(app)
    print("\n処理が完了しました。")
