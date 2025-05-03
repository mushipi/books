import os
import glob
import time
import shutil
from services.book_code_extractor import BookCodeExtractor

class BulkImportService:
    def __init__(self, db, book_service, extractor=None):
        """
        一括取り込みサービスの初期化
        
        Args:
            db: データベースインスタンス
            book_service: 書籍サービスインスタンス
            extractor: 書籍コード抽出器（Noneの場合は内部で生成）
        """
        self.db = db
        self.book_service = book_service
        self.extractor = extractor or BookCodeExtractor()
        
    def scan_folder(self, folder_path, default_genre=None):
        """
        フォルダ内の画像をスキャンして書籍情報を抽出
        
        Args:
            folder_path: スキャンするフォルダパス
            default_genre: デフォルトのジャンルID
            
        Returns:
            抽出結果のリスト
        """
        # 画像ファイル一覧取得
        image_files = glob.glob(os.path.join(folder_path, "*.jpg")) + glob.glob(os.path.join(folder_path, "*.jpeg"))
        
        results = []
        for image_path in image_files:
            # 画像から書籍情報を抽出
            info = self.extractor.extract_from_image(image_path)
            
            # 結果に画像パスを追加
            info["image_path"] = image_path
            info["filename"] = os.path.basename(image_path)
            
            # 追加情報の設定
            info["default_genre_id"] = default_genre
            
            # JANコードが抽出できた場合、重複チェック
            if info.get("jan_barcode"):
                info["is_duplicate"] = self._check_duplicate(info.get("jan_barcode"))
            else:
                info["is_duplicate"] = False
            
            results.append(info)
            
            # 一時ディレクトリに画像をコピー（Web UI表示用）
            self._copy_to_temp(image_path)
            
            # API制限対策で少し待機
            time.sleep(1)
            
        return results
    
    def _copy_to_temp(self, image_path):
        """画像を一時ディレクトリにコピー"""
        # 一時ディレクトリの作成
        temp_dir = os.path.join("static", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 画像をコピー
        filename = os.path.basename(image_path)
        dest_path = os.path.join(temp_dir, filename)
        try:
            shutil.copy2(image_path, dest_path)
        except Exception as e:
            print(f"警告: 画像のコピーに失敗しました: {str(e)}")
    
    def _check_duplicate(self, jan_code):
        """既存の書籍との重複をチェック"""
        if not jan_code:
            return False
        
        # 書籍サービスを使用して重複チェック
        return self.book_service.check_exists_by_jan(jan_code)
    
    def import_books(self, book_info_list, selected_ids=None):
        """
        選択された書籍情報をデータベースにインポート
        
        Args:
            book_info_list: 書籍情報のリスト
            selected_ids: インポートする書籍のID（リスト）
            
        Returns:
            インポート結果の辞書
        """
        if selected_ids is None:
            # 重複していない書籍をすべて選択
            selected_books = [info for info in book_info_list if not info.get("is_duplicate")]
        else:
            # 選択された書籍のみ取得
            selected_books = [info for info in book_info_list if info.get("id") in selected_ids]
        
        imported = []
        errors = []
        
        for book_info in selected_books:
            try:
                # 書籍情報をAPIから取得して登録
                jan_code = book_info.get("jan_barcode")
                print(f"DEBUG import_books: 対象JANコード = {jan_code}")
                if jan_code:
                    # 書籍サービスを使用して書籍を登録
                    print(f"DEBUG import_books: book_info = {book_info}")
                    book = self.book_service.register_book_by_jan(
                        jan_code, 
                        default_genre_id=book_info.get("default_genre_id")
                    )
                    
                    if book:
                        print(f"DEBUG import_books: book作成成功 = {book.id}, {book.title}")
                        imported.append({
                            "id": book.id,
                            "title": book.title,
                            "image_path": book_info.get("image_path")
                        })
                    else:
                        print(f"DEBUG import_books: book作成失敗 = APIからの情報取得エラー")
                        errors.append({
                            "image_path": book_info.get("image_path"),
                            "error": "書籍情報の取得に失敗しました"
                        })
                else:
                    print(f"DEBUG import_books: JANコードが見つかりません")
                    errors.append({
                        "image_path": book_info.get("image_path"),
                        "error": "JANコードが見つかりませんでした"
                    })
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"DEBUG import_books: 例外発生 = {str(e)}\n{error_details}")
                errors.append({
                    "image_path": book_info.get("image_path"),
                    "error": str(e)
                })
        
        return {
            "imported": imported,
            "errors": errors,
            "total_imported": len(imported),
            "total_errors": len(errors)
        }
