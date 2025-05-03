import requests
import os
import re
import logging
from PIL import Image
from io import BytesIO
from services.ndl_cover_service import NDLCoverService

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ApiService:
    def __init__(self, openbd_api_url, ndl_api_url, cover_folder):
        """
        書籍APIサービスの初期化
        
        Args:
            openbd_api_url: OpenBD APIのURL
            ndl_api_url: 国立国会図書館APIのURL（現在は未使用）
            cover_folder: 表紙画像保存先フォルダ
        """
        self.openbd_api_url = openbd_api_url
        self.ndl_api_url = ndl_api_url
        self.cover_folder = cover_folder
        
        # カバー画像保存フォルダの作成
        if not os.path.exists(cover_folder):
            os.makedirs(cover_folder)
            logger.info(f"カバー画像保存フォルダを作成しました: {cover_folder}")
        
        # 国会図書館表紙サービスの初期化
        self.ndl_cover_service = NDLCoverService(cover_folder)
    
    def lookup_isbn(self, isbn):
        """
        ISBNから書籍情報を検索する
        
        Args:
            isbn: ISBN番号
            
        Returns:
            dict: 書籍情報
        """
        logger.info(f"ISBNによる書籍検索: {isbn}")
        
        # OpenBD APIでの検索
        book_info = self._lookup_openbd(isbn)
        
        # OpenBDで見つからない場合は国会図書館APIで検索
        if not book_info:
            logger.info(f"OpenBDで情報が見つかりませんでした。国会図書館APIを試します: {isbn}")
            book_info = self._lookup_isbn_ndl(isbn)
        
        # どちらでも情報が取得できなかった場合
        if not book_info:
            logger.warning(f"すべてのAPIで書籍情報を取得できませんでした: {isbn}")
            return None
        
        # 表紙画像の取得処理
        book_info = self._process_cover_image(book_info, isbn)
        
        return book_info
    
    def _lookup_openbd(self, isbn):
        """
        OpenBD APIを使用して書籍情報を検索
        
        Args:
            isbn: ISBN番号
            
        Returns:
            dict: 書籍情報、見つからない場合はNone
        """
        try:
            url = f"{self.openbd_api_url}?isbn={isbn}"
            logger.debug(f"OpenBD APIリクエスト: {url}")
            
            response = requests.get(url, timeout=10)
            logger.debug(f"OpenBD API応答ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data and data[0]:
                    # データ整形
                    book_info = self._extract_openbd_data(data[0])
                    logger.debug(f"OpenBDから抽出された書籍情報: {book_info}")
                    return book_info
            
            logger.info(f"OpenBDで書籍情報が見つかりませんでした: {isbn}")
            return None
            
        except Exception as e:
            logger.error(f"OpenBD API検索中にエラー発生: {str(e)}")
            return None
    
    def _extract_openbd_data(self, data):
        """
        OpenBDのレスポンスから必要なデータを抽出する
        
        Args:
            data: OpenBD APIのレスポンスデータ
            
        Returns:
            dict: 整形された書籍情報
        """
        summary = data.get('summary', {})
        
        return {
            'title': summary.get('title', ''),
            'author': summary.get('author', ''),
            'publisher': summary.get('publisher', ''),
            'isbn': summary.get('isbn', ''),
            'published_date': summary.get('pubdate', ''),
            'cover_url': summary.get('cover', ''),
            'price': self._extract_price(summary.get('price', '')),
            'page_count': self._extract_pages(data)
        }
    
    def _extract_price(self, price_str):
        """
        価格文字列から数値を抽出する
        
        Args:
            price_str: 価格文字列
            
        Returns:
            int or None: 価格
        """
        if not price_str:
            return None
        
        # 数字のみを抽出
        numbers = re.findall(r'\d+', price_str)
        if numbers:
            return int(numbers[0])
        
        return None
    
    def _extract_pages(self, data):
        """
        ページ数を抽出する
        
        Args:
            data: 書籍データ
            
        Returns:
            int or None: ページ数
        """
        # OpenBDのデータ構造に基づいてページ数を抽出
        try:
            onix = data.get('onix', {})
            desc_detail = onix.get('DescriptiveDetail', {})
            extent = desc_detail.get('Extent', [])
            
            if isinstance(extent, list) and len(extent) > 0:
                extent_value = extent[0].get('ExtentValue', '')
                if extent_value:
                    return int(extent_value)
            
            return None
        except Exception as e:
            logger.error(f"ページ数抽出中にエラー: {str(e)}")
            return None
    
    def _lookup_isbn_ndl(self, isbn):
        """
        国立国会図書館APIを使って書籍情報を検索する
        
        Args:
            isbn: ISBN番号
            
        Returns:
            dict: 書籍情報
        """
        # 将来的に国会図書館API（書誌情報）が実装された場合の処理
        # 現時点では簡易的に空の辞書を返す
        logger.info("国会図書館書誌情報APIは未実装です（表紙画像のみ対応）")
        
        # ISBNがある場合は最低限の情報を設定
        if isbn:
            return {
                'title': '',
                'author': '',
                'publisher': '',
                'isbn': isbn,
                'published_date': '',
                'cover_url': '',  # 実際のURLはないが、あとで表紙画像を取得する用
                'price': None,
                'page_count': None
            }
        
        return None
    
    def _process_cover_image(self, book_info, isbn):
        """
        書籍情報に対して表紙画像の処理を行う
        複数のソースを試行してカバー画像を取得
        
        Args:
            book_info: 書籍情報
            isbn: ISBN番号
        
        Returns:
            dict: 表紙画像パスが追加された書籍情報
        """
        if not book_info:
            return None
        
        cover_image_path = None
        
        # 1. OpenBDから取得した表紙URLを使用
        if book_info.get('cover_url'):
            logger.info(f"OpenBDの表紙URLを使用して画像を取得します: {book_info.get('cover_url')}")
            cover_image_path = self._save_cover_image(book_info['cover_url'], isbn)
        
        # 2. OpenBDでの表紙取得に失敗した場合、国会図書館APIを試行
        if not cover_image_path:
            logger.info(f"OpenBDからの表紙取得に失敗したため、国会図書館APIを試行します: {isbn}")
            cover_image_path = self.ndl_cover_service.get_cover_image(isbn)
        
        # 表紙画像パスを設定
        book_info['cover_image_path'] = cover_image_path
        logger.info(f"最終的な表紙画像パス: {cover_image_path}")
        
        return book_info
    
    def _save_cover_image(self, cover_url, isbn):
        """
        表紙画像をダウンロードして保存する
        
        Args:
            cover_url: 表紙画像のURL
            isbn: ISBN番号
            
        Returns:
            str: 保存されたファイルのパス
        """
        if not cover_url:
            logger.warning("表紙画像URLが指定されていません")
            return None
            
        try:
            logger.debug(f"表紙画像のダウンロード試行: {cover_url}")
            
            # 画像ダウンロード（タイムアウト追加）
            response = requests.get(cover_url, timeout=10)
            
            if response.status_code == 200:
                # 画像処理
                try:
                    img = Image.open(BytesIO(response.content))
                    logger.debug(f"画像取得成功: サイズ {img.size}, モード {img.mode}")
                    
                    # サムネイルの作成
                    img.thumbnail((300, 400))
                    logger.debug(f"サムネイル作成: サイズ {img.size}")
                    
                    # 保存ファイル名の設定
                    filename = f"{isbn}.jpg"
                    filepath = os.path.join(self.cover_folder, filename)
                    logger.debug(f"保存先パス: {filepath}")
                    
                    # 画像の保存
                    img.convert('RGB').save(filepath, "JPEG", quality=85)
                    logger.info(f"表紙画像を保存しました: {filepath}")
                    
                    # 相対パスを返す（static/coversからの相対パス）
                    rel_path = os.path.join('covers', filename)
                    logger.debug(f"返却する相対パス: {rel_path}")
                    
                    return rel_path
                except Exception as e:
                    logger.error(f"画像処理中にエラー: {str(e)}")
                    return None
            else:
                logger.error(f"画像ダウンロード失敗: ステータスコード {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"表紙画像の保存に失敗しました: {str(e)}")
            return None
