import os
import sys
import logging
from config import OPENBD_API_URL, NDL_API_URL, UPLOAD_FOLDER
from services.api_service_enhanced import ApiService

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_api_service():
    """
    強化版APIサービスのテスト
    """
    logger.info("=" * 50)
    logger.info("強化版APIサービステスト開始")
    logger.info("=" * 50)
    
    # 設定情報表示
    logger.info(f"OpenBD API URL: {OPENBD_API_URL}")
    logger.info(f"NDL API URL: {NDL_API_URL}")
    logger.info(f"カバー画像保存フォルダ: {UPLOAD_FOLDER}")
    
    # 絶対パスに変換
    abs_cover_folder = os.path.abspath(UPLOAD_FOLDER)
    logger.info(f"カバー画像保存フォルダ (絶対パス): {abs_cover_folder}")
    
    # カバー画像フォルダ存在確認
    if not os.path.exists(abs_cover_folder):
        os.makedirs(abs_cover_folder, exist_ok=True)
        logger.info(f"カバー画像フォルダを作成しました: {abs_cover_folder}")
    
    # APIサービスの初期化
    api_service = ApiService(OPENBD_API_URL, NDL_API_URL, UPLOAD_FOLDER)
    
    # テスト用ISBNリスト
    test_cases = [
        {
            "isbn": "9784297127473",  # 技術評論社の本（OpenBDに存在する可能性が高い）
            "name": "OpenBDに存在する書籍"
        },
        {
            "isbn": "9784043898039",  # 国会図書館に存在する可能性が高い
            "name": "国会図書館で検索する書籍"
        },
        {
            "isbn": "978-4-7973-9720-4",  # ハイフン入りISBN
            "name": "ハイフン入りISBN形式"
        },
        {
            "isbn": "9784999999996",  # 存在しない可能性が高いISBN
            "name": "存在しない可能性が高いISBN"
        }
    ]
    
    results = []
    
    # 各テストケースを実行
    for test_case in test_cases:
        isbn = test_case["isbn"]
        name = test_case["name"]
        
        logger.info("\n" + "-" * 40)
        logger.info(f"テストケース: {name}")
        logger.info(f"ISBN: {isbn}")
        
        try:
            # 書籍情報の取得
            book_info = api_service.lookup_isbn(isbn)
            
            # 結果の評価
            if book_info:
                logger.info(f"書籍情報の取得に成功しました")
                logger.info(f"タイトル: {book_info.get('title', 'なし')}")
                logger.info(f"著者: {book_info.get('author', 'なし')}")
                logger.info(f"出版社: {book_info.get('publisher', 'なし')}")
                logger.info(f"表紙URL: {book_info.get('cover_url', 'なし')}")
                logger.info(f"表紙画像パス: {book_info.get('cover_image_path', 'なし')}")
                
                # 表紙画像の存在確認
                cover_path = book_info.get('cover_image_path')
                if cover_path:
                    # 相対パスを絶対パスに変換
                    if cover_path.startswith('covers/'):
                        abs_path = os.path.join('static', cover_path)
                    else:
                        abs_path = os.path.join('static', cover_path)
                    
                    abs_path = os.path.abspath(abs_path)
                    if os.path.exists(abs_path):
                        logger.info(f"表紙画像ファイルが存在します: {abs_path}")
                        file_size = os.path.getsize(abs_path)
                        logger.info(f"ファイルサイズ: {file_size} バイト")
                        test_case["result"] = "成功"
                        test_case["file_path"] = abs_path
                        test_case["file_size"] = file_size
                    else:
                        logger.error(f"表紙画像ファイルが存在しません: {abs_path}")
                        test_case["result"] = "ファイルなし"
                else:
                    logger.warning("表紙画像パスがnullです")
                    test_case["result"] = "画像なし"
            else:
                logger.warning(f"書籍情報の取得に失敗しました: {isbn}")
                test_case["result"] = "書籍情報なし"
            
        except Exception as e:
            logger.error(f"テスト実行中にエラーが発生しました: {str(e)}", exc_info=True)
            test_case["result"] = f"エラー: {str(e)}"
        
        results.append(test_case)
    
    # 結果サマリーの表示
    logger.info("\n" + "=" * 50)
    logger.info("テスト結果サマリー")
    logger.info("=" * 50)
    
    for idx, result in enumerate(results, 1):
        logger.info(f"{idx}. {result['name']} (ISBN: {result['isbn']}): {result.get('result', '不明')}")
    
    return results

if __name__ == "__main__":
    print("強化版APIサービスのテストを開始します...")
    results = test_api_service()
    
    print("\n結果サマリー:")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result['name']} (ISBN: {result['isbn']}): {result.get('result', '不明')}")
    
    print("\nテスト完了")
