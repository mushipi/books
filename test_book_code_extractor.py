import os
import sys

# 現在のディレクトリをプロジェクトルートに設定
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

from services.book_code_extractor import BookCodeExtractor

def test_extract_codes(image_path):
    """
    指定された画像からコードを抽出するテスト
    
    Args:
        image_path: テストする画像のパス
    """
    print(f"画像ファイル: {image_path}")
    print("-" * 50)
    
    # BookCodeExtractorの初期化
    extractor = BookCodeExtractor(use_ai_fallback=True)
    
    # コード抽出
    results = extractor.extract_codes_from_image(image_path)
    
    # 結果の表示
    print("抽出結果:")
    print(f"ISBN バーコード: {results.get('isbn_barcode')}")
    print(f"JAN コード: {results.get('jan_barcode')}")
    print(f"ISBN テキスト: {results.get('isbn_text')}")
    print(f"C コード: {results.get('c_code')}")
    print(f"価格コード: {results.get('price_code')}")
    print("-" * 50)
    
    return results

if __name__ == "__main__":
    # コマンドライン引数から画像パスを取得
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        test_extract_codes(image_path)
    else:
        print("使用方法: python test_book_code_extractor.py <画像パス>")
        print("例: python test_book_code_extractor.py test_images/book1.jpg")
