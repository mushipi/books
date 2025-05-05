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

def scan_covers_directory():
    """表紙画像ディレクトリをスキャンして利用可能な画像ファイルを取得"""
    covers_dir = os.path.join("static", "covers")
    available_images = {}
    
    # ディレクトリが存在するか確認
    if os.path.exists(covers_dir):
        # すべての画像ファイルを検索
        for ext in ["jpg", "jpeg", "png", "gif"]:
            pattern = os.path.join(covers_dir, f"*.{ext}")
            for img_path in glob.glob(pattern):
                # ファイル名からISBNを抽出（拡張子を除く）
                filename = os.path.basename(img_path)
                isbn = os.path.splitext(filename)[0]
                # 相対パスを保存（"covers/ファイル名"形式）
                rel_path = os.path.join("covers", filename)
                available_images[isbn] = {
                    "path": rel_path,
                    "full_path": img_path,
                    "size": os.path.getsize(img_path)
                }
    
    print(f"スキャン結果: {len(available_images)}個の画像ファイルが見つかりました")
    return available_images

def auto_link_covers(app):
    """ISBNに基づいて表紙画像を自動でリンク"""
    with app.app_context():
        try:
            # データベースの接続確認
            print("\n📚 データベース接続確認中...")
            books = Book.query.all()
            print(f"データベース内の合計書籍数: {len(books)}冊\n")
            
            # 利用可能な表紙画像ファイルをスキャン
            print("🔍 表紙画像ディレクトリをスキャン中...")
            available_covers = scan_covers_directory()
            
            # カウンター初期化
            linked_count = 0
            already_linked = 0
            no_matching_cover = 0
            no_isbn_count = 0
            
            print("\n⚙️ ISBN照合による表紙画像の自動リンクを開始...\n")
            
            # 全書籍のチェックと自動リンク
            for book in books:
                isbn = book.isbn
                current_path = book.cover_image_path
                
                # ISBNがない場合はスキップ
                if not isbn:
                    no_isbn_count += 1
                    continue
                
                # ISBNからダッシュを除去して正規化
                clean_isbn = isbn.replace("-", "")
                
                # 既に有効なパスがある場合はスキップ
                if current_path and os.path.exists(os.path.join("static", current_path)):
                    already_linked += 1
                    continue
                
                # ISBNに対応する表紙画像があるか確認
                if clean_isbn in available_covers:
                    # 対応する表紙画像が見つかった場合
                    new_path = available_covers[clean_isbn]["path"]
                    book.cover_image_path = new_path
                    print(f"✅ リンク: 「{book.title}」→ {new_path}")
                    linked_count += 1
                else:
                    # 対応する表紙画像が見つからない場合
                    if current_path:  # リンク切れを修正
                        book.cover_image_path = None
                        print(f"❌ リンク切れ修正: 「{book.title}」のパス({current_path})をNullに変更")
                    no_matching_cover += 1
            
            # 変更があれば保存
            if linked_count > 0:
                db.session.commit()
                print(f"\n✅ {linked_count}冊の書籍に表紙画像をリンクしました")
            else:
                print("\n📝 リンクした書籍はありませんでした")
            
            # 結果サマリーの表示
            print("\n📊 処理結果サマリー:")
            print(f"  - 新たにリンクした書籍: {linked_count}冊")
            print(f"  - 既にリンク済みの書籍: {already_linked}冊")
            print(f"  - 対応する表紙が見つからなかった書籍: {no_matching_cover}冊")
            print(f"  - ISBNがない書籍: {no_isbn_count}冊")
            
            # データの全体確認
            null_cover_count = Book.query.filter(Book.cover_image_path == None).count()
            not_null_cover_count = Book.query.filter(Book.cover_image_path != None).count()
            print(f"\n📊 データ確認:")
            print(f"  - 表紙画像なし(NULL): {null_cover_count}冊")
            print(f"  - 表紙画像あり: {not_null_cover_count}冊")
            
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    app = create_app()
    auto_link_covers(app)
    print("\n実行完了！")
