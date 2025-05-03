import os
import logging
from pathlib import Path
import requests
from PIL import Image
from io import BytesIO

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class NDLCoverDownloader:
    def __init__(self, save_dir="covers"):
        self.base_url = "https://ndlsearch.ndl.go.jp/thumbnail/"
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

    def download_cover(self, isbn: str) -> str:
        """
        指定したISBNの国立国会図書館サムネイル画像をダウンロードし保存する。
        保存先パスを返す。失敗時はNone。
        """
        try:
            clean_isbn = isbn.replace("-", "")
            if not self._validate_isbn(clean_isbn):
                logging.warning(f"無効なISBN形式: {isbn}")
                return None

            url = f"{self.base_url}{clean_isbn}.jpg"
            response = requests.get(url, timeout=10, headers={'User-Agent': 'BookManager/1.0'})
            if response.status_code == 404:
                logging.warning(f"画像が存在しません: {url}")
                return None
            response.raise_for_status()

            # 画像データが小さすぎる場合はエラーとみなす
            if len(response.content) < 100:
                logging.warning(f"画像データが空または小さすぎます: {url}")
                return None

            img = Image.open(BytesIO(response.content))
            if img.format not in ['JPEG', 'PNG']:
                logging.warning(f"サポートされない画像形式: {img.format}")
                return None

            save_path = self.save_dir / f"{clean_isbn}.jpg"
            img.convert('RGB').save(save_path, quality=85)
            logging.info(f"保存完了: {save_path}")
            return str(save_path)

        except requests.exceptions.RequestException as e:
            logging.error(f"リクエスト失敗: {isbn} - {str(e)}")
        except Exception as e:
            logging.error(f"画像処理失敗: {isbn} - {str(e)}")
        return None

    @staticmethod
    def _validate_isbn(isbn: str) -> bool:
        """
        ISBN13の形式チェックとチェックディジット検証
        """
        if len(isbn) != 13 or not isbn.isdigit():
            return False
        total = sum(int(isbn[i]) * (3 if i % 2 else 1) for i in range(12))
        check_digit = (10 - (total % 10)) % 10
        return int(isbn[-1]) == check_digit

if __name__ == "__main__":
    downloader = NDLCoverDownloader()

    # テスト用ISBNリスト
    test_isbns = [
        "9784043898039",      # 有効なISBN
        "9784999999996",      # 存在しないISBN
        "978-4-06-521808-4"   # ハイフン入り
    ]

    for isbn in test_isbns:
        print(f"\nISBN: {isbn}")
        result = downloader.download_cover(isbn)
        if result:
            print(f"Success: {result}")
        else:
            print("Failed to download cover")
