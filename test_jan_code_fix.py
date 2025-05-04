"""
JANコードとCコードの修正テスト用スクリプト
問題が修正されたかを検証します
"""

import os
import sys
from datetime import datetime

# バーコード機能を無効化する環境変数を設定
os.environ['DISABLE_BARCODE'] = 'true'

# アプリ作成前にバーコードコントローラのインポートを回避
sys.modules['controllers.barcode_controller'] = object()

from models.book import db, Book
from app import create_app
from services.book_code_extractor_new import BookCodeExtractor

def test_book_code_extraction():
    """書籍コード抽出機能のテスト"""
    print("=" * 50)
    print("書籍コード抽出機能テスト")
    print("=" * 50)
    
    # テスト用サンプル画像パスの設定
    # 注: 実際のテスト画像をプロジェクト内に配置してください
    test_image_path = os.path.join('test_images', 'test_barcode.jpg')
    if not os.path.exists(test_image_path):
        print(f"テスト画像が見つかりません: {test_image_path}")
        print("test_imagesフォルダに有効なバーコード画像を配置してください。")
        return
    
    # BookCodeExtractorインスタンスの作成
    extractor = BookCodeExtractor(use_ai_fallback=True)
    
    # 画像からコードを抽出
    print(f"テスト画像からコードを抽出中: {test_image_path}")
    
    result = extractor.extract_codes_from_image(test_image_path)
    
    # 結果の表示
    print("\n抽出結果:")
    print(f"ISBNバーコード: {result.get('isbn_barcode', 'なし')}")
    print(f"JANコード: {result.get('jan_barcode', 'なし')} (NONではないことを確認)")
    print(f"ISBN文字列: {result.get('isbn_text', 'なし')}")
    print(f"Cコード: {result.get('c_code', 'なし')} (NONではないことを確認)")
    print(f"価格コード: {result.get('price_code', 'なし')}")
    
    if result.get('jan_barcode') == 'NON' or result.get('c_code') == 'NON':
        print("\n[エラー] 'NON'値が見つかりました。修正が必要です。")
    else:
        print("\n[成功] 'NON'値は見つかりませんでした。修正が機能しています。")

def test_database_records():
    """データベース内のレコードをテスト"""
    print("\n" + "=" * 50)
    print("データベースレコードテスト")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        # JANコードとCコードの値をチェック
        books = Book.query.all()
        
        print(f"全書籍数: {len(books)}")
        
        non_jan_count = 0
        non_c_code_count = 0
        
        for book in books:
            if book.jan_code == 'NON':
                non_jan_count += 1
                print(f"ID {book.id} ('{book.title}'): JANコードが'NON'です")
            
            if book.c_code == 'NON':
                non_c_code_count += 1
                print(f"ID {book.id} ('{book.title}'): Cコードが'NON'です")
        
        if non_jan_count == 0 and non_c_code_count == 0:
            print("\n[成功] 'NON'値は見つかりませんでした。データベースは正常です。")
        else:
            print(f"\n[警告] {non_jan_count}件のJANコードと{non_c_code_count}件のCコードが'NON'です。")
            print("fix_code_and_price.batを実行して修正してください。")

if __name__ == "__main__":
    # 書籍コード抽出テスト
    test_book_code_extraction()
    
    # データベースレコードテスト
    test_database_records()
