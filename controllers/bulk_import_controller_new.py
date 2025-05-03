from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
import os
import time
from models.genre import Genre
from services.book_service import BookService
from services.api_service import ApiService
from services.bulk_import_service import BulkImportService
from services.book_code_extractor import BookCodeExtractor

# Blueprintの作成
bulk_import_bp = Blueprint('bulk_import', __name__, url_prefix='/bulk-import')

@bulk_import_bp.route('/', methods=['GET'])
def index():
    """一括取り込みフォーム"""
    genres = Genre.query.order_by(Genre.name).all()
    return render_template('bulk_import/form.html', genres=genres)

@bulk_import_bp.route('/scan', methods=['POST'])
def scan():
    """フォルダのスキャン処理"""
    folder_path = request.form.get('folder_path')
    default_genre_id = request.form.get('default_genre_id')
    
    if not folder_path or not os.path.isdir(folder_path):
        flash('有効なフォルダパスを指定してください', 'danger')
        return redirect(url_for('bulk_import.index'))
    
    # サービスの初期化
    api_service = ApiService(
        current_app.config['OPENBD_API_URL'],
        current_app.config['NDL_API_URL'],
        os.path.join(current_app.static_folder, 'covers')
    )
    book_service = BookService(current_app.db, api_service)
    
    # 一括取り込みサービスの初期化
    extractor = BookCodeExtractor()
    bulk_import_service = BulkImportService(current_app.db, book_service, extractor)
    
    # フォルダスキャン
    try:
        results = bulk_import_service.scan_folder(folder_path, default_genre_id)
        
        # IDを振って一時保存
        for i, result in enumerate(results):
            result['id'] = i + 1
        
        # セッションに保存
        session['scan_results'] = results
        session['folder_path'] = folder_path
        session['default_genre_id'] = default_genre_id
        
        return render_template('bulk_import/scan_results.html', 
                              results=results, 
                              folder_path=folder_path)
    
    except Exception as e:
        flash(f'スキャン中にエラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('bulk_import.index'))

@bulk_import_bp.route('/import', methods=['POST'])
def import_books():
    """選択された書籍のインポート実行"""
    # セッションからスキャン結果を取得
    results = session.get('scan_results')
    folder_path = session.get('folder_path')
    default_genre_id = session.get('default_genre_id')
    
    if not results:
        flash('スキャン結果が見つかりません。再度スキャンしてください', 'warning')
        return redirect(url_for('bulk_import.index'))
    
    # 選択されたIDのリスト取得
    selected_ids = [int(id) for id in request.form.getlist('selected_books')]
    
    if not selected_ids:
        flash('インポートする書籍が選択されていません', 'warning')
        return render_template('bulk_import/scan_results.html', 
                              results=results, 
                              folder_path=folder_path)
    
    # サービスの初期化
    api_service = ApiService(
        current_app.config['OPENBD_API_URL'],
        current_app.config['NDL_API_URL'],
        os.path.join(current_app.static_folder, 'covers')
    )
    book_service = BookService(current_app.db, api_service)
    
    # 一括取り込みサービスの初期化
    bulk_import_service = BulkImportService(current_app.db, book_service)
    
    # インポート実行
    try:
        import_result = bulk_import_service.import_books(results, selected_ids)
        
        # セッション情報をクリア
        session.pop('scan_results', None)
        session.pop('folder_path', None)
        session.pop('default_genre_id', None)
        
        return render_template('bulk_import/import_results.html', 
                              import_result=import_result)
    
    except Exception as e:
        flash(f'インポート中にエラーが発生しました: {str(e)}', 'danger')
        return render_template('bulk_import/scan_results.html', 
                              results=results, 
                              folder_path=folder_path)

@bulk_import_bp.route('/status', methods=['GET'])
def get_status():
    """処理状況を取得するAPIエンドポイント"""
    # 進捗状況をJSONで返す
    session_id = request.args.get('session_id')
    
    # TODO: セッション管理機能の実装
    
    return jsonify({
        'status': 'progress',
        'processed': 5,
        'total': 10,
        'current_file': 'book_cover_005.jpg',
        'message': '処理中...'
    })

@bulk_import_bp.route('/cancel', methods=['POST'])
def cancel():
    """処理をキャンセルするAPIエンドポイント"""
    # TODO: セッション管理機能の実装
    
    return jsonify({
        'success': True,
        'message': '処理をキャンセルしました'
    })
