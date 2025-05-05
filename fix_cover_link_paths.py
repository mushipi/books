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
            for img_path in glob.glob(os.path.join(covers_dir, f"*.{ext}")):
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
    
    return available_images

def fix_cover_links_with_scan(app):
    """表紙画像のリンク切れを修正 - 実ファイルスキャン方式"""
    with app.app_context():
        try:
            # データベースの接続確認
            print("\n📚 データベース接続確認中...")
            books = Book.query.all()
            print(f"データベース内の合計書籍数: {len(books)}冊\n")
            
            # 利用可能な表紙画像ファイルをスキャン
            print("🔍 表紙画像ディレクトリをスキャン中...")
            available_covers = scan_covers_directory()
            print(f"利用可能な表紙画像ファイル: {len(available_covers)}個\n")
            
            # カウンター初期化
            empty_fixed = 0
            broken_fixed = 0
            linked_fixed = 0
            
            # 全書籍の表紙パスチェックと修正
            for book in books:
                isbn = book.isbn
                cover_path = book.cover_image_path
                
                # 1. 空文字列のケース
                if cover_path == "":
                    print(f"📄 修正: 「{book.title}」- 空文字列のパスをNullに変更")
                    book.cover_image_path = None
                    empty_fixed += 1
                    continue
                
                # 2. パスはあるがファイルが存在しないケース
                if cover_path is not None:
                    static_path = os.path.join("static", cover_path)
                    if not os.path.exists(static_path):
                        # 2.1 ISBNから対応するカバー画像があるか確認
                        if isbn and isbn.replace("-", "") in available_covers:
                            correct_path = available_covers[isbn.replace("-", "")]["path"]
                            print(f"🔄 修正: 「{book.title}」- リンク切れのパス({cover_path})を有効なパス({correct_path})に変更")
                            book.cover_image_path = correct_path
                            linked_fixed += 1
                        else:
                            print(f"❌ 修正: 「{book.title}」- リンク切れのパス({cover_path})をNullに変更")
                            book.cover_image_path = None
                            broken_fixed += 1
            
            # 変更があれば保存
            total_fixed = empty_fixed + broken_fixed + linked_fixed
            if total_fixed > 0:
                db.session.commit()
                print(f"\n✅ 合計{total_fixed}冊の書籍のパスを修正しました:")
                print(f"  - 空文字列のパス: {empty_fixed}冊")
                print(f"  - リンク切れのパス(Nullに変更): {broken_fixed}冊")
                print(f"  - リンク切れのパス(有効なパスに修正): {linked_fixed}冊")
            else:
                print("\n✅ 修正すべき書籍はありませんでした。")
                
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
    fix_cover_links_with_scan(app)
    print("\n実行完了！")
