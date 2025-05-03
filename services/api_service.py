import requests
import os
import re
import logging
from PIL import Image
from io import BytesIO
from pathlib import Path

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ApiService:
    def __init__(self, openbd_api_url, ndl_api_url, cover_folder):
        """
        書籍APIサービスの初期化
        
        Args:
            openbd_api_url: OpenBD APIのURL
            ndl_api_url: 国立国会図書館APIのURL
            cover_folder: 表紙画像保存先フォルダ
        """
        self.openbd_api_url = openbd_api_url
        self.ndl_api_url = ndl_api_url
        
        # カバー画像保存フォルダの正規化と作成
        # 相対パスを絶対パスに変換し、統一的に扱う
        self.cover_folder = cover_folder
        self.abs_cover_folder = os.path.abspath(cover_folder)
        logger.info(f"カバー画像保存フォルダ: {self.abs_cover_folder}")
        
        # フォルダがなければ作成
        Path(self.abs_cover_folder).mkdir(parents=True, exist_ok=True)
        
        # NDL用サムネイルURLベース
        self.ndl_thumbnail_base_url = "https://ndlsearch.ndl.go.jp/thumbnail/"
    
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
        
        # OpenBDで見つからない場合は最小限の情報を作成
        if not book_info:
            logger.info(f"OpenBDで情報が見つかりませんでした: {isbn}")
            # ISBNのみの最小限情報を作成
            book_info = {
                'title': '',
                'author': '',
                'publisher': '',
                'isbn': isbn,
                'published_date': '',
                'cover_url': '',
                'price': None,
                'page_count': None
            }
        
        # 表紙画像の取得（OpenBDと国会図書館の両方を試行）
        book_info = self._process_cover_image(book_info)
        
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
            # ISBNの正規化（ハイフン除去）
            clean_isbn = isbn.replace("-", "")
            
            url = f"{self.openbd_api_url}?isbn={clean_isbn}"
            logger.info(f"OpenBD APIリクエスト: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and data[0]:
                    # データ整形
                    book_info = self._extract_openbd_data(data[0])
                    logger.debug(f"OpenBDから抽出された書籍情報: {book_info}")
                    return book_info
            
            logger.warning(f"OpenBDで書籍情報が見つかりませんでした: {isbn}")
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
    
    def _process_cover_image(self, book_info):
        """
        書籍情報に対して表紙画像の処理を行う
        複数のソースから表紙画像を取得し、最初に成功したものを使用
        
        Args:
            book_info: 書籍情報
        
        Returns:
            dict: 表紙画像パスが追加された書籍情報
        """
        if not book_info:
            return None
        
        # ISBNの取得と正規化
        isbn = book_info.get('isbn', '')
        if not isbn:
            logger.warning("ISBNが指定されていません")
            book_info['cover_image_path'] = None
            return book_info
        
        # ハイフンの除去
        clean_isbn = isbn.replace("-", "")
        
        # ISBNの簡易検証
        if len(clean_isbn) != 13 or not clean_isbn.isdigit():
            logger.warning(f"無効なISBN形式: {isbn}")
            book_info['cover_image_path'] = None
            return book_info
        
        # 既存の画像ファイルをチェック（キャッシュ）
        rel_path = os.path.join('covers', f"{clean_isbn}.jpg")
        abs_path = os.path.join(self.abs_cover_folder, f"{clean_isbn}.jpg")
        
        if os.path.exists(abs_path):
            logger.info(f"既存のカバー画像が見つかりました: {abs_path}")
            book_info['cover_image_path'] = rel_path
            return book_info
        
        # 1. OpenBDからカバー画像の取得を試行
        cover_path = None
        if book_info.get('cover_url'):
            logger.info(f"OpenBDから表紙画像を取得します: {book_info.get('cover_url')}")
            cover_path = self._download_openbd_cover(book_info.get('cover_url'), clean_isbn)
        
        # 2. OpenBDで取得できなかった場合、国会図書館APIを試行
        if not cover_path:
            logger.info(f"国会図書館から表紙画像を取得します: {clean_isbn}")
            cover_path = self._download_ndl_cover(clean_isbn)
        
        # 表紙画像パスの設定
        book_info['cover_image_path'] = cover_path
        logger.info(f"最終的な表紙画像パス: {cover_path}")
        
        return book_info
    
    def _download_openbd_cover(self, cover_url, isbn):
        """
        OpenBDの表紙URLから画像をダウンロードして保存
        
        Args:
            cover_url: 表紙画像のURL
            isbn: ISBN番号（正規化済み）
            
        Returns:
            str: 保存された相対ファイルパス、失敗時はNone
        """
        if not cover_url:
            logger.warning("表紙URLが指定されていません")
            return None
            
        try:
            logger.info(f"OpenBD表紙画像のダウンロード: {cover_url}")
            
            # 画像ダウンロード
            response = requests.get(
                cover_url, 
                timeout=10,
                headers={'User-Agent': 'BookManager/1.0'}
            )
            
            if response.status_code != 200:
                logger.warning(f"画像ダウンロード失敗: HTTP {response.status_code}")
                return None
            
            # レスポンスの内容チェック
            if len(response.content) < 100:
                logger.warning(f"画像データが小さすぎます: {len(response.content)} bytes")
                return None
            
            # 画像処理
            return self._process_and_save_image(response.content, isbn)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"リクエスト失敗: {str(e)}")
        except Exception as e:
            logger.error(f"画像処理エラー: {str(e)}")
            
        return None
    
    def _download_ndl_cover(self, isbn):
        """
        国立国会図書館のサムネイルAPIから表紙画像を取得
        
        Args:
            isbn: ISBN番号（正規化済み）
            
        Returns:
            str: 保存された相対ファイルパス、失敗時はNone
        """
        try:
            # ISBNチェックディジットの検証
            if not self._validate_isbn13(isbn):
                logger.warning(f"無効なISBN13: {isbn}")
                return None
            
            # 国会図書館サムネイルURLの構築
            url = f"{self.ndl_thumbnail_base_url}{isbn}.jpg"
            logger.info(f"国会図書館表紙画像のダウンロード: {url}")
            
            # 画像ダウンロード
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
            if response.status_code != 200:
                logger.warning(f"画像ダウンロード失敗: HTTP {response.status_code}")
                return None
            
            # レスポンスの内容チェック
            if len(response.content) < 100:
                logger.warning(f"画像データが小さすぎます: {len(response.content)} bytes")
                return None
            
            # 画像処理
            return self._process_and_save_image(response.content, isbn)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"リクエスト失敗: {str(e)}")
        except Exception as e:
            logger.error(f"画像処理エラー: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        return None
    
    def _process_and_save_image(self, image_data, isbn):
        """
        画像データを処理して保存
        
        Args:
            image_data: 画像バイナリデータ
            isbn: ISBN番号（正規化済み）
            
        Returns:
            str: 保存された相対ファイルパス、失敗時はNone
        """
        try:
            # 画像のロードと検証
            img = Image.open(BytesIO(image_data))
            
            if img.format not in ['JPEG', 'PNG']:
                logger.warning(f"サポートされない画像形式: {img.format}")
                return None
            
            logger.info(f"画像ロード成功: サイズ {img.size}, モード {img.mode}")
            
            # 画像のリサイズ
            img.thumbnail((300, 400))
            logger.info(f"サムネイル作成: サイズ {img.size}")
            
            # 保存ファイル名とパスの設定
            filename = f"{isbn}.jpg"
            filepath = os.path.join(self.abs_cover_folder, filename)
            logger.info(f"保存先絶対パス: {filepath}")
            
            # 画像の保存（RGBモードに変換して保存）
            img.convert('RGB').save(filepath, "JPEG", quality=85)
            logger.info(f"表紙画像を保存しました: {filepath}")
            
            # 相対パスを返す
            # staticディレクトリからの相対パスで返す（Flaskのurl_for('static', filename=...)に合わせる）
            rel_path = os.path.join('covers', filename)
            logger.info(f"返却する相対パス: {rel_path}")
            
            return rel_path
        
        except Exception as e:
            logger.error(f"画像処理・保存中にエラー: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    def _validate_isbn13(isbn):
        """
        ISBN13のチェックディジット検証
        
        Args:
            isbn: 検証するISBN（13桁）
            
        Returns:
            bool: 有効ならTrue
        """
        if len(isbn) != 13 or not isbn.isdigit():
            return False
        
        # チェックディジットの計算
        total = sum(int(isbn[i]) * (1 if i % 2 == 0 else 3) for i in range(12))
        check_digit = (10 - (total % 10)) % 10
        
        return int(isbn[-1]) == check_digit
