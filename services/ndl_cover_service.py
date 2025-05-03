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
logger = logging.getLogger(__name__)

class NDLCoverService:
    """
    国立国会図書館の書籍サムネイルAPIを利用して表紙画像を取得するサービス
    """
    
    def __init__(self, cover_folder="static/covers"):
        """
        国会図書館表紙画像サービスの初期化
        
        Args:
            cover_folder: 表紙画像を保存するフォルダパス
        """
        self.base_url = "https://ndlsearch.ndl.go.jp/thumbnail/"
        self.cover_folder = Path(cover_folder)
        
        # 保存先フォルダの作成
        if not self.cover_folder.exists():
            logger.info(f"保存先フォルダ作成: {self.cover_folder}")
            self.cover_folder.mkdir(parents=True, exist_ok=True)
    
    def get_cover_image(self, isbn):
        """
        ISBNから表紙画像を取得して保存する
        
        Args:
            isbn: ISBN番号（ハイフンあり/なし両方対応）
            
        Returns:
            str: 保存されたファイルの相対パス、失敗時はNone
        """
        try:
            # ISBNの正規化（ハイフン除去）
            clean_isbn = isbn.replace("-", "")
            
            # ISBNの検証
            if not self._validate_isbn(clean_isbn):
                logger.warning(f"無効なISBN形式: {isbn}")
                return None
            
            # 既にダウンロード済みの場合はそのパスを返す
            relative_path = f"covers/{clean_isbn}.jpg"
            absolute_path = self.cover_folder / f"{clean_isbn}.jpg"
            if absolute_path.exists():
                logger.info(f"既存のカバー画像を使用: {absolute_path}")
                return relative_path
            
            # 表紙画像のダウンロード
            url = f"{self.base_url}{clean_isbn}.jpg"
            logger.info(f"表紙画像のダウンロード試行: {url}")
            
            response = requests.get(
                url, 
                timeout=10, 
                headers={'User-Agent': 'BookManager/1.0'}
            )
            
            # 404エラーの場合は画像が存在しない
            if response.status_code == 404:
                logger.warning(f"画像が存在しません: {url}")
                return None
                
            # その他のHTTPエラー
            response.raise_for_status()
            
            # レスポンスの内容チェック
            if len(response.content) < 100:
                logger.warning(f"画像データが小さすぎます: {url}")
                return None
            
            # 画像のロードと検証
            img = Image.open(BytesIO(response.content))
            if img.format not in ['JPEG', 'PNG']:
                logger.warning(f"サポートされない画像形式: {img.format}")
                return None
            
            # 画像のリサイズ（必要に応じて）
            if max(img.size) > 800:
                logger.info(f"画像のリサイズ: {img.size}")
                img.thumbnail((300, 400))
            
            # 画像の保存
            img.convert('RGB').save(absolute_path, format='JPEG', quality=85)
            logger.info(f"表紙画像の保存完了: {absolute_path}")
            
            return relative_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"リクエスト失敗: {isbn} - {str(e)}")
        except Exception as e:
            logger.error(f"画像処理エラー: {isbn} - {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        return None
    
    @staticmethod
    def _validate_isbn(isbn):
        """
        ISBN13の形式チェックとチェックディジット検証
        
        Args:
            isbn: 検証するISBN（ハイフンなし13桁）
            
        Returns:
            bool: 有効なISBNならTrue
        """
        # 基本的な形式チェック
        if len(isbn) != 13 or not isbn.isdigit():
            return False
        
        # チェックディジットの検証
        total = sum(int(isbn[i]) * (3 if i % 2 else 1) for i in range(12))
        check_digit = (10 - (total % 10)) % 10
        
        return int(isbn[-1]) == check_digit
