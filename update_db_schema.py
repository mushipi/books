"""
データベーススキーマ更新スクリプト
- Cコードカラムの追加
- JANコードが'NON'の場合は空文字列に変換
- 価格がNULLの場合は0に設定
"""

import os
import sys

# バーコード機能を無効化する環境変数を設定
os.environ['DISABLE_BARCODE'] = 'true'

# アプリ作成前にバーコードコントローラのインポートを回避
sys.modules['controllers.barcode_controller'] = object()

from models.book import db, Book
from app import create_app
import sqlite3

def update_db_schema():
    """データベーススキーマを更新する"""
    app = create_app()
    with app.app_context():
        # インスタンスディレクトリのパスを取得
        instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
        db_path = os.path.join(instance_path, 'books.db')
        
        print(f"データベースファイルのパス: {db_path}")
        
        # SQLite3データベースに接続
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # c_codeカラムが存在するか確認
            cursor.execute("PRAGMA table_info(book)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            # c_codeカラムが存在しない場合は追加
            if 'c_code' not in column_names:
                print("c_codeカラムをbookテーブルに追加します...")
                cursor.execute("ALTER TABLE book ADD COLUMN c_code TEXT")
                conn.commit()
                print("c_codeカラムが追加されました")
            else:
                print("c_codeカラムは既に存在します")
            
            # JANコードが'NON'の場合は空文字列に変換
            print("JANコードの修正を開始します...")
            cursor.execute("UPDATE book SET jan_code = '' WHERE jan_code = 'NON'")
            jan_code_updates = cursor.rowcount
            conn.commit()
            print(f"{jan_code_updates}件のJANコードを修正しました")
            
            # 価格がNULLの場合は0に設定
            print("価格の修正を開始します...")
            cursor.execute("UPDATE book SET price = 0 WHERE price IS NULL")
            price_updates = cursor.rowcount
            conn.commit()
            print(f"{price_updates}件の価格を修正しました")
            
            conn.close()
            print("データベーススキーマの更新が完了しました")
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return False
        
        return True

if __name__ == "__main__":
    print("=" * 50)
    print("データベーススキーマ更新ユーティリティ")
    print("=" * 50)
    
    # スキーマ更新を実行
    if update_db_schema():
        print("更新が正常に完了しました")
    else:
        print("更新中にエラーが発生しました")
