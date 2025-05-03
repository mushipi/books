import os
import sys
from config import OPENBD_API_URL, NDL_API_URL, UPLOAD_FOLDER
from services.api_service import ApiService

def test_cover_image_download():
    # APIサービスの初期化
    api_service = ApiService(OPENBD_API_URL, NDL_API_URL, UPLOAD_FOLDER)
    
    # テスト用のISBN
    test_isbn = "9784297127473"  # 実在する書籍のISBNを使用
    
    print(f"テスト実行: ISBN={test_isbn} でカバー画像の取得を試みます")
    
    # 書籍情報の取得とカバー画像のダウンロード
    book_info = api_service.lookup_isbn(test_isbn)
    
    # 結果の確認
    if book_info:
        print(f"書籍タイトル: {book_info.get('title', 'タイトルなし')}")
        print(f"著者: {book_info.get('author', '著者なし')}")
        print(f"出版社: {book_info.get('publisher', '出版社なし')}")
        print(f"カバー画像URL: {book_info.get('cover_url', 'なし')}")
        print(f"カバー画像保存パス: {book_info.get('cover_image_path', 'なし')}")
    else:
        print("書籍情報の取得に失敗しました。")
    
    return book_info

if __name__ == "__main__":
    print("表紙画像ダウンロードのテストを開始します...")
    book_info = test_cover_image_download()
    
    # 詳細なデバッグ情報
    if book_info:
        print("\n詳細情報:")
        for key, value in book_info.items():
            print(f"{key}: {value}")
    
    print("\nテスト完了")
