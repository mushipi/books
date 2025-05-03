import requests
import os
import re
from PIL import Image
from io import BytesIO
import logging

# ロギングの設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ApiService:
    def __init__(self, openbd_api_url, ndl_api_url, cover_folder):
        self.openbd_api_url = openbd_api_url
        self.ndl_api_url = ndl_api_url
        self.cover_folder = cover_folder
        
        # カバー画像保存フォルダの作成（絶対パスで処理）
        self.abs_cover_folder = os.path.abspath(cover_folder)
        logger.debug(f"カバー画像保存フォルダ(絶対パス): {self.abs_cover_folder}")
        if not os.path.exists(self.abs_cover_folder):
            os.makedirs(self.abs_cover_folder)
            logger.info(f"カバー画像フォルダを作成しました: {self.abs_cover_folder}")
    
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
        url = f"{self.openbd_api_url}?isbn={isbn}"
        try:
            response = requests.get(url, timeout=10)
            logger.debug(f"API応答ステータス: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data and data[0]:
                    # データ整形
                    book_info = self._extract_openbd_data(data[0])
                    logger.debug(f"抽出された書籍情報: {book_info}")
                    
                    # 表紙画像の保存
                    if book_info.get('cover_url'):
                        cover_path = self._save_cover_image(book_info['cover_url'], isbn)
                        if cover_path:
                            book_info['cover_image_path'] = cover_path
                            logger.info(f"カバー画像保存成功: {cover_path}")
                        else:
                            logger.warning(f"カバー画像の保存に失敗: {book_info['cover_url']}")
                            book_info['cover_image_path'] = None
                    else:
                        logger.info("カバー画像URLが取得できませんでした")
                        book_info['cover_image_path'] = None
                    
                    return book_info
                else:
                    logger.warning(f"書籍情報が取得できませんでした: {isbn}")
            else:
                logger.error(f"APIエラー: {response.status_code}")
                
        except Exception as e:
            logger.error(f"APIリクエスト中にエラーが発生: {str(e)}", exc_info=True)
        
        # OpenBDで見つからない場合、国会図書館APIで検索
        logger.info(f"国会図書館APIでの検索を試みます: {isbn}")
        return self._lookup_isbn_ndl(isbn)
    
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
        # 国立国会図書館APIの実装
        # 現状では簡易実装のみ（将来拡張予定）
        logger.info("国会図書館APIは未実装です")
        return None
    
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
            logger.warning("カバー画像URLが指定されていません")
            return None
            
        try:
            logger.debug(f"カバー画像のダウンロード試行: {cover_url}")
            
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
                    filepath = os.path.join(self.abs_cover_folder, filename)
                    logger.debug(f"保存先パス: {filepath}")
                    
                    # 画像の保存
                    img.save(filepath, "JPEG")
                    logger.info(f"カバー画像を保存しました: {filepath}")
                    
                    # 相対パスを返す（static/coversからの相対パス）
                    rel_path = os.path.join('covers', filename)
                    logger.debug(f"返却する相対パス: {rel_path}")
                    
                    return rel_path
                except Exception as e:
                    logger.error(f"画像処理中にエラー: {str(e)}", exc_info=True)
                    return None
            else:
                logger.error(f"画像ダウンロード失敗: ステータスコード {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"表紙画像の保存に失敗しました: {str(e)}", exc_info=True)
            return None
