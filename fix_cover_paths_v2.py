from flask import Flask
import os
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

def fix_cover_paths_comprehensive(app):
    """表紙画像パスの総合的な修正"""
    with app.app_context():
        try:
            # データベースの接続確認
            print("\n📚 データベース接続確認中...")
            books = Book.query.all()
            print(f"データベース内の合計書籍数: {len(books)}冊\n")
            
            print("🔍 表紙画像パスの問題を検出中...\n")
            
            # カウンター初期化
            empty_fixed = 0
            broken_fixed = 0
            
            # 全書籍の表紙パスチェックと修正
            for book in books:
                cover_path = book.cover_image_path
                
                # 1. 空文字列のケース
                if cover_path == "":
                    print(f"修正: 「{book.title}」- 空文字列のパスをNullに変更")
                    book.cover_image_path = None
                    empty_fixed += 1
                    continue
                
                # 2. パスはあるがファイルが存在しないケース
                if cover_path is not None:
                    static_path = os.path.join("static", cover_path)
                    if not os.path.exists(static_path):
                        print(f"修正: 「{book.title}」- リンク切れのパス({cover_path})をNullに変更")
                        book.cover_image_path = None
                        broken_fixed += 1
            
            # 変更があれば保存
            total_fixed = empty_fixed + broken_fixed
            if total_fixed > 0:
                db.session.commit()
                print(f"\n✅ 合計{total_fixed}冊の書籍のパスを修正しました:")
                print(f"  - 空文字列のパス: {empty_fixed}冊")
                print(f"  - リンク切れのパス: {broken_fixed}冊")
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
            print("データベース接続やモデルの初期化に問題がある可能性があります。")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    app = create_app()
    fix_cover_paths_comprehensive(app)
    print("\n実行完了！")
