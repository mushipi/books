import os
import sys
import logging
from config import OPENBD_API_URL, NDL_API_URL, UPLOAD_FOLDER
from services.api_service import ApiService

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_cover_image_download(isbn):
    """
    指定されたISBNで表紙画像取得をテストする
    
    Args:
        isbn: テストするISBN番号
        
    Returns:
        dict: 取得された書籍情報
    """
    logger.info(f"====== テスト開始: ISBN={isbn} ======")
    
    # 設定情報の表示
    logger.info(f"設定: API URL = {OPENBD_API_URL}")
    logger.info(f"設定: カバーフォルダ = {UPLOAD_FOLDER}")
    logger.info(f"設定: 絶対パス = {os.path.abspath(UPLOAD_FOLDER)}")
    
    # APIサービスの初期化
    api_service = ApiService(OPENBD_API_URL, NDL_API_URL, UPLOAD_FOLDER)
    
    # 書籍情報の取得
    logger.info(f"ISBNによる書籍検索を実行: {isbn}")
    book_info = api_service.lookup_isbn(isbn)
    
    # 結果の確認
    if book_info:
        logger.info("===== 書籍情報取得成功 =====")
        logger.info(f"タイトル: {book_info.get('title', 'タイトルなし')}")
        logger.info(f"著者: {book_info.get('author', '著者なし')}")
        logger.info(f"出版社: {book_info.get('publisher', '出版社なし')}")
        logger.info(f"表紙URL: {book_info.get('cover_url', 'なし')}")
        logger.info(f"表紙パス: {book_info.get('cover_image_path', 'なし')}")
        
        # 表紙画像の存在確認
        cover_path = book_info.get('cover_image_path')
        if cover_path:
            # 相対パスから絶対パスに変換
            if not os.path.isabs(cover_path):
                abs_path = os.path.abspath(os.path.join('static', cover_path))
                logger.info(f"表紙絶対パス: {abs_path}")
                
                if os.path.exists(abs_path):
                    file_size = os.path.getsize(abs_path)
                    logger.info(f"✅ 表紙画像ファイルが存在します: {abs_path} ({file_size} bytes)")
                else:
                    logger.error(f"❌ 表紙画像ファイルが存在しません: {abs_path}")
            else:
                # 既に絶対パスの場合
                if os.path.exists(cover_path):
                    file_size = os.path.getsize(cover_path)
                    logger.info(f"✅ 表紙画像ファイルが存在します: {cover_path} ({file_size} bytes)")
                else:
                    logger.error(f"❌ 表紙画像ファイルが存在しません: {cover_path}")
        else:
            logger.warning("表紙画像パスがnullです")
    else:
        logger.error("書籍情報の取得に失敗しました。")
    
    logger.info(f"====== テスト終了: ISBN={isbn} ======")
    return book_info

def run_all_tests():
    """複数のISBNでテストを実行"""
    # テスト用のISBNリスト
    test_isbns = [
        "9784297127473",  # 存在するISBN
        "9784774142230",  # 別の存在するISBN
        "9784873119656",  # Pythonプログラミング本
        "9784048930598",  # 小説
        "978-4-06-521808-4",  # ハイフン入りISBN
        "9784999999996",  # 存在しないISBN
    ]
    
    results = {}
    success_count = 0
    
    for isbn in test_isbns:
        print(f"\n{'='*50}")
        print(f"テスト実行中: ISBN={isbn}")
        print(f"{'='*50}")
        
        book_info = test_cover_image_download(isbn)
        results[isbn] = book_info
        
        if book_info and book_info.get('cover_image_path'):
            success_count += 1
            print(f"結果: ✅ 成功")
        else:
            print(f"結果: ❌ 失敗")
    
    # 結果の要約
    print(f"\n{'='*50}")
    print(f"テスト結果サマリー")
    print(f"{'='*50}")
    print(f"総テスト数: {len(test_isbns)}")
    print(f"成功数: {success_count}")
    print(f"失敗数: {len(test_isbns) - success_count}")
    print(f"成功率: {success_count / len(test_isbns) * 100:.1f}%")
    
    # 成功した項目の詳細
    print("\n✅ 成功したISBN:")
    for isbn, info in results.items():
        if info and info.get('cover_image_path'):
            print(f"- {isbn}: {info.get('title', '不明')} ({info.get('cover_image_path')})")
    
    # 失敗した項目の詳細
    print("\n❌ 失敗したISBN:")
    for isbn, info in results.items():
        if not info or not info.get('cover_image_path'):
            print(f"- {isbn}")

if __name__ == "__main__":
    print("表紙画像取得テストを開始します...\n")
    
    try:
        if len(sys.argv) > 1:
            # コマンドライン引数がある場合、特定のISBNでテスト
            isbn = sys.argv[1]
            print(f"指定されたISBN {isbn} でテストを実行します")
            test_cover_image_download(isbn)
        else:
            # 引数がない場合、全テストを実行
            run_all_tests()
    
    except Exception as e:
        import traceback
        print(f"\nエラーが発生しました: {str(e)}")
        traceback.print_exc()
    
    print("\nテスト完了")
