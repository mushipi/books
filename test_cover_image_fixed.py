import os
import sys
import logging
from config import OPENBD_API_URL, NDL_API_URL, UPLOAD_FOLDER
from services.api_service_fixed import ApiService

# ロギングの設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_cover_image_download():
    # テスト開始
    logger.info("表紙画像ダウンロードテスト開始")
    
    # 設定の出力
    logger.info(f"OpenBD API URL: {OPENBD_API_URL}")
    logger.info(f"NDL API URL: {NDL_API_URL}")
    logger.info(f"アップロードフォルダ: {UPLOAD_FOLDER}")
    
    # カバーフォルダのパスを検証
    abs_cover_folder = os.path.abspath(UPLOAD_FOLDER)
    logger.info(f"カバーフォルダ絶対パス: {abs_cover_folder}")
    
    # フォルダ存在確認
    if os.path.exists(abs_cover_folder):
        logger.info(f"カバーフォルダは存在します: {abs_cover_folder}")
    else:
        logger.warning(f"カバーフォルダが存在しません。作成します: {abs_cover_folder}")
        os.makedirs(abs_cover_folder, exist_ok=True)
    
    # APIサービスの初期化
    api_service = ApiService(OPENBD_API_URL, NDL_API_URL, UPLOAD_FOLDER)
    
    # テスト用のISBN
    test_isbn = "9784297127473"  # 実在する書籍のISBNを使用
    
    logger.info(f"テスト実行: ISBN={test_isbn} でカバー画像の取得を試みます")
    
    # 書籍情報の取得とカバー画像のダウンロード
    book_info = api_service.lookup_isbn(test_isbn)
    
    # 結果の確認
    if book_info:
        logger.info("書籍情報取得成功:")
        logger.info(f"書籍タイトル: {book_info.get('title', 'タイトルなし')}")
        logger.info(f"著者: {book_info.get('author', '著者なし')}")
        logger.info(f"出版社: {book_info.get('publisher', '出版社なし')}")
        logger.info(f"カバー画像URL: {book_info.get('cover_url', 'なし')}")
        logger.info(f"カバー画像保存パス: {book_info.get('cover_image_path', 'なし')}")
        
        # カバー画像パスの検証
        cover_image_path = book_info.get('cover_image_path')
        if cover_image_path:
            # 相対パスを絶対パスに変換
            if not os.path.isabs(cover_image_path):
                # 'covers/'を'static/covers/'に置き換え
                if cover_image_path.startswith('covers/'):
                    abs_path = os.path.join('static', cover_image_path)
                else:
                    abs_path = os.path.join('static', cover_image_path)
                
                abs_path = os.path.abspath(abs_path)
                logger.info(f"カバー画像絶対パス: {abs_path}")
                
                if os.path.exists(abs_path):
                    logger.info(f"✅ カバー画像ファイルが存在します: {abs_path}")
                    # ファイルサイズの確認
                    file_size = os.path.getsize(abs_path)
                    logger.info(f"ファイルサイズ: {file_size} バイト")
                else:
                    logger.error(f"❌ カバー画像ファイルが存在しません: {abs_path}")
            else:
                # すでに絶対パスの場合
                if os.path.exists(cover_image_path):
                    logger.info(f"✅ カバー画像ファイルが存在します: {cover_image_path}")
                else:
                    logger.error(f"❌ カバー画像ファイルが存在しません: {cover_image_path}")
        else:
            logger.warning("カバー画像パスがnullです")
    else:
        logger.error("書籍情報の取得に失敗しました。")
    
    return book_info

if __name__ == "__main__":
    print("=" * 80)
    print("表紙画像ダウンロードのテストを開始します...")
    print("=" * 80)
    
    try:
        book_info = test_cover_image_download()
        
        print("\n結果サマリー:")
        if book_info:
            print(f"書籍タイトル: {book_info.get('title', 'タイトルなし')}")
            if book_info.get('cover_image_path'):
                print(f"カバー画像: ✅ 成功 ({book_info.get('cover_image_path')})")
            else:
                print("カバー画像: ❌ 失敗")
        else:
            print("書籍情報の取得に失敗しました。")
    
    except Exception as e:
        import traceback
        print(f"テスト実行中にエラーが発生しました: {str(e)}")
        traceback.print_exc()
    
    print("\nテスト完了")
    print("=" * 80)
