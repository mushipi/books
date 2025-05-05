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

def diagnose_cover_paths(app):
    """表紙画像パスの詳細診断"""
    with app.app_context():
        try:
            # データベースの接続確認
            print("\n📚 データベース接続確認中...")
            books = Book.query.all()
            print(f"データベース内の合計書籍数: {len(books)}冊\n")
            
            print("🔍 表紙画像パスの詳細診断を実行中...\n")
            
            # 表紙画像の状態を分類
            books_no_cover = []  # 表紙パスがNullの書籍
            books_empty_cover = []  # 表紙パスが空文字の書籍
            books_with_path = []  # 表紙パスがあるが存在しない書籍
            books_with_valid_path = []  # 表紙パスがあり存在する書籍
            
            # 全書籍の表紙パスチェック
            for book in books:
                title = book.title
                # タイトルが長い場合は省略
                if len(title) > 50:
                    title = title[:47] + "..."
                    
                cover_path = book.cover_image_path
                
                if cover_path is None:
                    books_no_cover.append(book)
                    print(f"✓ NULL: 「{title}」- 表紙パスがNull")
                elif cover_path == "":
                    books_empty_cover.append(book)
                    print(f"✗ 空: 「{title}」- 表紙パスが空文字")
                else:
                    # 実際のファイルの存在確認
                    static_path = os.path.join("static", cover_path)
                    file_exists = os.path.exists(static_path)
                    
                    if file_exists:
                        books_with_valid_path.append(book)
                        print(f"✓ 有効: 「{title}」- パス: {cover_path}")
                    else:
                        books_with_path.append(book)
                        print(f"✗ リンク切れ: 「{title}」- パス: {cover_path}")
            
            # サマリー出力
            print("\n📊 診断結果サマリー:")
            print(f"  - 表紙なし(NULL): {len(books_no_cover)}冊")
            print(f"  - 表紙空文字列(\"\"):  {len(books_empty_cover)}冊")
            print(f"  - リンク切れ: {len(books_with_path)}冊")
            print(f"  - 有効な表紙: {len(books_with_valid_path)}冊")
            
            # 問題がある書籍の詳細リスト
            if books_empty_cover or books_with_path:
                print("\n⚠️ 修正が必要な書籍:")
                
                if books_empty_cover:
                    print("\n🔧 空文字の表紙パスがある書籍:")
                    for book in books_empty_cover:
                        print(f"  - 「{book.title}」(ID: {book.id})")
                        
                if books_with_path:
                    print("\n🔧 リンク切れの表紙パスがある書籍:")
                    for book in books_with_path:
                        print(f"  - 「{book.title}」(ID: {book.id}) - パス: {book.cover_image_path}")
                        
                print("\n🛠️ これらの書籍は自動修正スクリプトで修正できます。")
            else:
                print("\n✅ 修正が必要な書籍はありません。")
            
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    app = create_app()
    diagnose_cover_paths(app)
    print("\n実行完了！")
