from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, flash, session
import os
import time
from datetime import datetime
import json
from werkzeug.utils import secure_filename
from io import StringIO
import csv

from models.book import db, Book
from models.genre import Genre
from services.book_code_extractor import BookCodeExtractor
from services.api_service import ApiService
from services.background_processor import BackgroundProcessor, cache

# Blueprintの作成
bulk_import_bp = Blueprint('bulk_import', __name__, url_prefix='/bulk-import')

@bulk_import_bp.route('/')
def index():
    """
    一括取り込み画面を表示
    """
    # ジャンルの取得（選択肢として表示）
    genres = Genre.query.order_by(Genre.name).all()
    return render_template('bulk_import/index.html', genres=genres)

@bulk_import_bp.route('/start-process', methods=['POST'])
def start_process():
    """
    バックグラウンド処理を開始するエンドポイント
    """
    directory_path = request.form.get('directory_path', '').strip()
    default_genre_id = request.form.get('default_genre_id')
    use_ai = request.form.get('use_ai', 'true').lower() == 'true'
    
    # 入力チェック
    if not directory_path or not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        return jsonify({
            'success': False,
            'message': f'指定されたディレクトリが存在しません: {directory_path}'
        })
    
    # 画像ファイルの存在確認
    image_files = []
    for file in os.listdir(directory_path):
        if file.lower().endswith(('.jpg', '.jpeg')):
            image_path = os.path.join(directory_path, file)
            if os.path.isfile(image_path) and os.access(image_path, os.R_OK):
                image_files.append(image_path)
    
    if not image_files:
        return jsonify({
            'success': False,
            'message': '指定されたディレクトリにJPEG画像が見つかりませんでした'
        })
    
    # バックグラウンド処理の開始
    try:
        session_id = BackgroundProcessor.process_images(
            directory_path=directory_path,
            default_genre_id=default_genre_id,
            use_ai=use_ai,
            app_context=current_app.app_context()
        )
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f'{len(image_files)}枚の画像の処理を開始しました'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'処理の開始に失敗しました: {str(e)}'
        })

@bulk_import_bp.route('/ajax-progress', methods=['GET'])
def get_processing_status():
    """
    処理状況をAJAXで取得するエンドポイント
    """
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({
            'success': False,
            'message': 'セッションIDが指定されていません'
        })
    
    # セッションから処理状況を取得
    status = BackgroundProcessor.get_status(session_id)
    
    return jsonify(status)

@bulk_import_bp.route('/cancel-process', methods=['POST'])
def cancel_process():
    """
    実行中の処理をキャンセルするエンドポイント
    """
    session_id = request.form.get('session_id')
    
    if not session_id:
        return jsonify({
            'success': False,
            'message': 'セッションIDが指定されていません'
        })
    
    success = BackgroundProcessor.cancel_process(session_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': '処理をキャンセルしました'
        })
    else:
        return jsonify({
            'success': False,
            'message': '処理のキャンセルに失敗しました。既に完了しているか、存在しないセッションです'
        })

@bulk_import_bp.route('/export-result', methods=['GET'])
def export_result():
    """
    処理結果をCSVファイルとしてエクスポート
    """
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({
            'success': False,
            'message': 'セッションIDが指定されていません'
        })
    
    # セッションデータの取得
    status = BackgroundProcessor.get_status(session_id)
    
    if not status or status.get('status') == 'not_found':
        return jsonify({
            'success': False,
            'message': '指定されたセッションのデータが見つかりません'
        })
    
    # CSVデータの生成
    output = StringIO()
    writer = csv.writer(output)
    
    # ヘッダー行
    writer.writerow(['ファイル名', 'ISBN', 'タイトル', '著者', '出版社', '結果'])
    
    # 処理成功した書籍
    for book in status.get('processed_files', []):
        writer.writerow([
            book.get('file', ''),
            book.get('isbn', ''),
            book.get('title', ''),
            book.get('author', ''),
            book.get('publisher', ''),
            '成功'
        ])
    
    # エラーがあった書籍
    for error in status.get('errors', []):
        writer.writerow([
            error.get('file', ''),
            '',
            '',
            '',
            '',
            f'エラー: {error.get("error", "")}'
        ])
    
    # レスポンスの作成
    output_string = output.getvalue()
    output.close()
    
    # CSVファイルとして返す
    response = current_app.response_class(
        output_string,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=import_result_{session_id}.csv'}
    )
    
    return response

@bulk_import_bp.route('/scan-directory', methods=['POST'])
def scan_directory():
    """
    指定されたディレクトリ内の画像をスキャンして書籍情報を抽出（従来のエンドポイント - 互換性のために維持）
    """
    directory_path = request.form.get('directory_path', '')
    # パスの正規化
    directory_path = os.path.normpath(directory_path.strip())
    print(f"[情報] ディレクトリパス: {directory_path}")
    
    default_genre_id = request.form.get('default_genre_id')
    use_ai = request.form.get('use_ai', 'true').lower() == 'true'
    
    # 入力チェック
    if not directory_path or not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        print(f"[エラー] 指定されたディレクトリが存在しません: {directory_path}")
        return jsonify({
            'success': False,
            'message': f'指定されたディレクトリが存在しません - {directory_path}'
        })
    
    # 指定されたディレクトリ内のJPEG画像を取得
    image_files = []
    try:
        for file in os.listdir(directory_path):
            lower_file = file.lower()
            if lower_file.endswith('.jpg') or lower_file.endswith('.jpeg'):
                image_path = os.path.join(directory_path, file)
                # ファイルが読み取り可能か確認
                if os.path.isfile(image_path) and os.access(image_path, os.R_OK):
                    image_files.append(image_path)
                else:
                    print(f"[警告] ファイルへのアクセス権がありません: {image_path}")
    except Exception as e:
        print(f"[エラー] ディレクトリの読み込み中にエラーが発生しました: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ディレクトリの読み込み中にエラーが発生しました: {str(e)}'
        })
    
    # 見つかった画像ファイルの数を表示
    print(f"[情報] {directory_path} 内で {len(image_files)} 個のJPEG画像が見つかりました")
    
    if not image_files:
        return jsonify({
            'success': False,
            'message': '指定されたディレクトリにJPEG画像が見つかりませんでした'
        })
    
    # BookCodeExtractorの初期化
    try:
        extractor = BookCodeExtractor(
            use_ai_fallback=use_ai,
            gemini_api_key=current_app.config.get('GEMINI_API_KEY')
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'バーコード抽出機能の初期化に失敗しました: {str(e)}'
        })
    
    # APIサービスの初期化
    api_service = ApiService(
        current_app.config['OPENBD_API_URL'],
        current_app.config['NDL_API_URL'],
        os.path.join(current_app.static_folder, 'covers')
    )
    
    # 各画像を処理
    results = []
    for image_path in image_files:
        file_name = os.path.basename(image_path)
        
        try:
            # 処理開始時間
            start_time = time.time()
            
            # 画像からコードを抽出
            extracted_codes = extractor.extract_codes_from_image(image_path)
            
            # ISBNコードを取得（バーコードまたはテキスト形式）
            isbn_code = None
            if extracted_codes.get('isbn_barcode'):
                isbn_code = extracted_codes['isbn_barcode']
            elif extracted_codes.get('isbn_text'):
                # ISBN文字列からハイフンと空白を削除し、数字のみを抽出
                isbn_text = extracted_codes['isbn_text']
                isbn_code = ''.join(c for c in isbn_text if c.isdigit() or c.upper() == 'X')
            
            # 書籍情報の検索
            book_info = None
            if isbn_code:
                book_info = api_service.lookup_isbn(isbn_code)
            
            # 処理時間
            processing_time = time.time() - start_time
            
            # 既存の書籍を確認（既に登録されているかチェック）
            existing_book = None
            if isbn_code:
                existing_book = Book.query.filter_by(isbn=isbn_code).first()
            
            # 結果を追加
            result = {
                'file_name': file_name,
                'path': image_path,
                'codes': extracted_codes,
                'isbn': isbn_code,
                'book_info': book_info,
                'processing_time': f"{processing_time:.2f}秒",
                'existing': True if existing_book else False
            }
            results.append(result)
            
        except Exception as e:
            # エラーが発生した場合も結果に追加
            results.append({
                'file_name': file_name,
                'path': image_path,
                'error': str(e)
            })
    
    # 処理結果を返す
    return jsonify({
        'success': True,
        'results': results,
        'total': len(image_files),
        'processed': len(results),
        'default_genre_id': default_genre_id
    })

@bulk_import_bp.route('/import', methods=['POST'])
def import_books():
    """
    選択された書籍を一括インポート
    """
    data = request.json
    books_to_import = data.get('books', [])
    default_genre_id = data.get('default_genre_id')
    
    if not books_to_import:
        return jsonify({
            'success': False,
            'message': 'インポートする書籍が選択されていません'
        })
    
    # APIサービスの初期化（カバー画像の取得に使用）
    api_service = ApiService(
        current_app.config['OPENBD_API_URL'],
        current_app.config['NDL_API_URL'],
        os.path.join(current_app.static_folder, 'covers')
    )
    
    # インポート処理
    imported_count = 0
    for book_data in books_to_import:
        try:
            # 既存の書籍をチェック
            isbn = book_data.get('isbn')
            existing_book = Book.query.filter_by(isbn=isbn).first() if isbn else None
            
            if existing_book:
                # 既存の書籍の場合はスキップ
                continue
            
            # 新しい書籍を作成
            book_info = book_data.get('book_info', {})
            
            # 必要な情報が揃っているか確認
            if not book_info or not isbn:
                continue
            
            # 書籍モデルの作成
            new_book = Book(
                title=book_info.get('title', '不明なタイトル'),
                author=book_info.get('author', ''),
                publisher=book_info.get('publisher', ''),
                published_date=book_info.get('published_date', ''),
                isbn=isbn,
                jan_code=book_data.get('codes', {}).get('jan_barcode', ''),
                price=0,  # 後で価格情報から設定
                page_count=book_info.get('page_count', 0),
                added_date=datetime.now().strftime('%Y-%m-%d'),
                memo=f"Cコード: {book_data.get('codes', {}).get('c_code', '')}"
            )
            
            # 価格情報の設定
            price_code = book_data.get('codes', {}).get('price_code', '')
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
                new_book.cover_image_path = api_service.download_cover(isbn, book_info.get('cover_url'))
            
            # データベースに保存
            db.session.add(new_book)
            db.session.commit()
            
            imported_count += 1
            
        except Exception as e:
            # エラーが発生した場合は次の書籍に進む
            print(f"書籍のインポート中にエラーが発生しました: {str(e)}")
            continue
    
    # 処理結果を返す
    return jsonify({
        'success': True,
        'imported_count': imported_count,
        'message': f'{imported_count}冊の書籍を正常にインポートしました'
    })
