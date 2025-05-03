import os
import sys
import time
import argparse
from pprint import pprint

# プロジェクトルートをPythonパスに追加
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# サービスモジュールをインポート
from services.book_code_extractor import BookCodeExtractor

def test_extraction(image_path, use_ai=True):
    """
    単一の画像に対して書籍コード抽出をテストする
    
    Args:
        image_path: テストする画像のパス
        use_ai: AIバックアップ認識を使用するかどうか
    """
    print(f"画像ファイル: {image_path}")
    print(f"AIバックアップ認識: {'有効' if use_ai else '無効'}")
    print("-" * 50)
    
    # 画像ファイルのチェック
    if not os.path.exists(image_path):
        print(f"エラー: ファイル {image_path} が見つかりません")
        return
    
    # BookCodeExtractorの初期化
    try:
        extractor = BookCodeExtractor(use_ai_fallback=use_ai)
        print(f"BookCodeExtractor初期化成功")
    except Exception as e:
        print(f"BookCodeExtractor初期化エラー: {e}")
        return
    
    try:
        # 処理時間の計測
        start_time = time.time()
        
        # 画像からコードを抽出
        codes = extractor.extract_codes_from_image(image_path)
        
        # 処理時間
        processing_time = time.time() - start_time
        
        print("\n抽出結果:")
        print(f"処理時間: {processing_time:.2f}秒")
        
        # 結果の表示
        if codes:
            pprint(codes)
        else:
            print("コードが抽出できませんでした")
        
    except Exception as e:
        print(f"処理エラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='書籍コード抽出テスト')
    parser.add_argument('image_path', help='テストする画像のパス')
    parser.add_argument('--no-ai', action='store_true', help='AIバックアップ認識を無効化する')
    
    args = parser.parse_args()
    test_extraction(args.image_path, not args.no_ai)

if __name__ == "__main__":
    main()
