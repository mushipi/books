import threading
import time
import uuid
import os
from datetime import datetime

# 簡易的なキャッシュ（本番環境ではRedisなどを検討）
cache = {}

class BackgroundProcessor:
    @staticmethod
    def process_images(directory_path, default_genre_id, use_ai, app_context):
        """
        バックグラウンドで画像処理を実行
        
        Args:
            directory_path: 画像フォルダパス
            default_genre_id: デフォルトジャンルID
            use_ai: AI処理を使用するかどうか
            app_context: Flaskアプリケーションコンテキスト
        
        Returns:
            str: セッションID（進捗確認用）
        """
        # セッションIDの生成
        session_id = str(uuid.uuid4())
        
        # 初期ステータスの設定
        cache[f'import_status_{session_id}'] = {
            'status': 'initializing',
            'current': 0,
            'total': 0,
            'processed_files': [],
            'errors': []
        }
        
        # バックグラウンドスレッドの開始
        thread = threading.Thread(
            target=BackgroundProcessor._process_images_thread,
            args=(session_id, directory_path, default_genre_id, use_ai, app_context)
        )
        thread.daemon = True
        thread.start()
        
        return session_id
    
    @staticmethod
    def _process_images_thread(session_id, directory_path, default_genre_id, use_ai, app_context):
        """スレッド内で実行される画像処理"""
        with app_context:
            from services.book_code_extractor import BookCodeExtractor
            from services.api_service import ApiService
            from models.book import Book, db
            from models.genre import Genre
            
            # 必要なサービスの初期化
            try:
                extractor = BookCodeExtractor(
                    use_ai_fallback=use_ai,
                    gemini_api_key=app_context._get_current_object().config.get('GEMINI_API_KEY')
                )
                
                api_service = ApiService(
                    app_context._get_current_object().config['OPENBD_API_URL'],
                    app_context._get_current_object().config['NDL_API_URL'],
                    os.path.join(app_context._get_current_object().static_folder, 'covers')
                )
                
                # 対象画像ファイルのリスト作成
                image_files = []
                for file in os.listdir(directory_path):
                    if file.lower().endswith(('.jpg', '.jpeg')):
                        image_path = os.path.join(directory_path, file)
                        if os.path.isfile(image_path) and os.access(image_path, os.R_OK):
                            image_files.append(image_path)
                
                # ステータス更新
                cache[f'import_status_{session_id}'].update({
                    'status': 'processing',
                    'total': len(image_files),
                    'current': 0
                })
                
                # 画像を1つずつ処理
                for idx, image_path in enumerate(image_files):
                    # キャンセルされたかチェック
                    if cache[f'import_status_{session_id}'].get('status') == 'cancelled':
                        cache[f'import_status_{session_id}'].update({
                            'status': 'cancelled',
                            'message': 'ユーザーによって処理がキャンセルされました'
                        })
                        break
                    
                    try:
                        # ステータス更新
                        cache[f'import_status_{session_id}'].update({
                            'current': idx + 1,
                            'current_file': os.path.basename(image_path)
                        })
                        
                        # 画像処理
                        extracted_codes = extractor.extract_codes_from_image(image_path)
                        
                        # ISBNコードの取得
                        isbn_code = extracted_codes.get('isbn_barcode') or extracted_codes.get('isbn_text')
                        if isbn_code:
                            # ハイフンやスペースを除去
                            isbn_code = ''.join(c for c in isbn_code if c.isdigit() or c.upper() == 'X')
                            # ISBNコードが13桁でない場合はISBN-10からISBN-13に変換
                            if len(isbn_code) == 10:
                                # ISBN-10の先頭に978を追加してチェックディジットを除去
                                isbn_code = '978' + isbn_code[:-1]
                                # チェックディジットの計算
                                sum = 0
                                for i in range(12):
                                    digit = int(isbn_code[i])
                                    sum += digit if i % 2 == 0 else digit * 3
                                check_digit = (10 - (sum % 10)) % 10
                                isbn_code = isbn_code + str(check_digit)
                            
                            # 書籍情報の検索
                            book_info = api_service.lookup_isbn(isbn_code)
                            
                            if book_info:
                                # 既存チェック
                                existing_book = Book.query.filter_by(isbn=isbn_code).first()
                                if existing_book:
                                    raise ValueError(f"ISBN {isbn_code} の書籍は既に登録されています")
                                
                                # 新規書籍の登録
                                new_book = Book(
                                    title=book_info.get('title', '不明なタイトル'),
                                    author=book_info.get('author', ''),
                                    publisher=book_info.get('publisher', ''),
                                    published_date=book_info.get('published_date', ''),
                                    isbn=isbn_code,
                                    jan_code=extracted_codes.get('jan_barcode', ''),
                                    price=0,  # 後で価格情報から設定
                                    page_count=book_info.get('page_count', 0),
                                    added_date=datetime.now().strftime('%Y-%m-%d'),
                                    memo=f"Cコード: {extracted_codes.get('c_code', '')}" if extracted_codes.get('c_code') else ""
                                )
                                
                                # 価格情報の設定
                                price_code = extracted_codes.get('price_code', '')
                                if price_code and '¥' in price_code:
                                    # 価格コードから数字のみを抽出
                                    price_digits = ''.join(c for c in price_code if c.isdigit())
                                    if price_digits:
                                        new_book.price = int(price_digits)
                                
                                # ジャンル設定
                                if default_genre_id:
                                    genre = Genre.query.get(default_genre_id)
                                    if genre:
                                        new_book.genres.append(genre)
                                
                                # カバー画像の取得と保存
                                if book_info.get('cover_url'):
                                    new_book.cover_image_path = api_service.download_cover(isbn_code, book_info.get('cover_url'))
                                
                                # データベースに保存
                                db.session.add(new_book)
                                db.session.commit()
                                
                                # 処理結果の記録
                                cache[f'import_status_{session_id}']['processed_files'].append({
                                    'file': os.path.basename(image_path),
                                    'isbn': isbn_code,
                                    'title': book_info.get('title'),
                                    'author': book_info.get('author', ''),
                                    'publisher': book_info.get('publisher', ''),
                                    'success': True
                                })
                            else:
                                raise ValueError(f"ISBN {isbn_code} の書籍情報が見つかりませんでした")
                        else:
                            raise ValueError("ISBNコードが抽出できませんでした")
                        
                    except Exception as e:
                        # エラー情報の記録
                        cache[f'import_status_{session_id}']['errors'].append({
                            'file': os.path.basename(image_path),
                            'error': str(e)
                        })
                
                # 処理完了
                cache[f'import_status_{session_id}']['status'] = 'completed'
                
            except Exception as e:
                # 全体的なエラー
                cache[f'import_status_{session_id}'].update({
                    'status': 'error',
                    'message': f'処理中にエラーが発生しました: {str(e)}'
                })
            
            # キャッシュの有効期限設定（3時間）
            threading.Timer(10800, lambda: cache.pop(f'import_status_{session_id}', None)).start()
    
    @staticmethod
    def cancel_process(session_id):
        """
        実行中の処理をキャンセルする
        
        Args:
            session_id: キャンセルするセッションID
            
        Returns:
            bool: キャンセル成功時はTrue
        """
        status = cache.get(f'import_status_{session_id}')
        
        if not status:
            return False
        
        # 処理中の場合のみキャンセル可能
        if status.get('status') == 'processing':
            status['status'] = 'cancelling'
            cache[f'import_status_{session_id}'] = status
            return True
        
        return False
    
    @staticmethod
    def get_status(session_id):
        """
        処理状況を取得する
        
        Args:
            session_id: 取得するセッションID
            
        Returns:
            dict: 処理状況情報
        """
        return cache.get(f'import_status_{session_id}', {
            'status': 'not_found',
            'message': '指定されたセッションが見つかりません'
        })
