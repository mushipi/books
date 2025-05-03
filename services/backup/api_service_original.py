import requests
import os
import re
from PIL import Image
from io import BytesIO

class ApiService:
    def __init__(self, openbd_api_url, ndl_api_url, cover_folder):
        self.openbd_api_url = openbd_api_url
        self.ndl_api_url = ndl_api_url
        self.cover_folder = cover_folder
        
        # カバー画像保存フォルダの作成
        if not os.path.exists(cover_folder):
            os.makedirs(cover_folder)
    
    def lookup_isbn(self, isbn):
        """
        ISBNから書籍情報を検索する
        
        Args:
            isbn: ISBN番号
            
        Returns:
            dict: 書籍情報
        """
        # OpenBD APIでの検索
        url = f"{self.openbd_api_url}?isbn={isbn}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data and data[0]:
                # データ整形
                book_info = self._extract_openbd_data(data[0])
                
                # 表紙画像の保存
                if book_info.get('cover_url'):
                    cover_path = self._save_cover_image(book_info['cover_url'], isbn)
                    book_info['cover_image_path'] = cover_path
                    # デバッグ用出力
                    print(f"DEBUG: cover_image_path = {cover_path}")
                
                # デバッグ用出力
                print(f"DEBUG: book_info = {book_info}")
                return book_info
        
        # OpenBDで見つからない場合、国会図書館APIで検索
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
        except:
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
        try:
            # 画像ダウンロード
            response = requests.get(cover_url)
            
            if response.status_code == 200:
                # 画像処理
                img = Image.open(BytesIO(response.content))
                
                # サムネイルの作成
                img.thumbnail((300, 400))
                
                # 保存ファイル名の設定
                filename = f"{isbn}.jpg"
                filepath = os.path.join(self.cover_folder, filename)
                
                # 画像の保存
                img.save(filepath, "JPEG")
                
                # 相対パスを返す
                return os.path.join('covers', filename)
            
            return None
        except Exception as e:
            print(f"表紙画像の保存に失敗しました: {e}")
            return None
