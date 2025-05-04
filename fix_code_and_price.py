"""
JANコード、Cコード、価格の修正スクリプト
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

def fix_jan_code_and_price():
    """JANコードと価格を修正する"""
    app = create_app()
    with app.app_context():
        # 全書籍レコードの取得
        books = Book.query.all()
        jan_code_fixed_count = 0
        price_fixed_count = 0
        
        print(f"全書籍数: {len(books)}")
        
        for book in books:
            # JANコードの修正
            if book.jan_code == 'NON':
                print(f"ID {book.id} ('{book.title}'): JANコード 'NON' → ''")
                book.jan_code = ''
                jan_code_fixed_count += 1
            
            # 価格の修正
            if book.price is None:
                print(f"ID {book.id} ('{book.title}'): 価格 NULL → 0")
                book.price = 0
                price_fixed_count += 1
        
        # 変更をコミット
        db.session.commit()
        
        print(f"修正完了: {jan_code_fixed_count}件のJANコードと{price_fixed_count}件の価格を修正しました")
        
        return jan_code_fixed_count, price_fixed_count

if __name__ == "__main__":
    print("=" * 50)
    print("JANコードと価格の修正ユーティリティ")
    print("=" * 50)
    
    # 修正を実行
    jan_count, price_count = fix_jan_code_and_price()
    
    # 結果の表示
    if jan_count > 0 or price_count > 0:
        print("修正が正常に完了しました")
        print(f"- JANコード修正数: {jan_count}")
        print(f"- 価格修正数: {price_count}")
    else:
        print("修正が必要なレコードはありませんでした")
