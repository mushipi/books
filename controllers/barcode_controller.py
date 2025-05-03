from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
import os
import tempfile

# サービスのインポート
from services.book_code_extractor import BookCodeExtractor
from services.api_service import ApiService

barcode_bp = Blueprint('barcode', __name__, url_prefix='/barcode')

@barcode_bp.route('/scan')
def scan():
    """
    バーコードスキャン画面を表示
    """
    return render_template('barcode/scan_improved.html')

@barcode_bp.route('/upload', methods=['POST'])
def upload():
    """
    バーコード画像のアップロード処理
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # 一時ファイルとして保存
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_path = temp_file.name
        image_file.save(temp_path)
    
    try:
        # BookCodeExtractorを使用して書籍コードを抽出
        code_extractor = BookCodeExtractor(
            use_ai_fallback=current_app.config.get('USE_AI_FALLBACK', False),
            gemini_api_key=current_app.config.get('GEMINI_API_KEY')
        )
        
        extracted_codes = code_extractor.extract_codes_from_image(temp_path)
        
        if not extracted_codes or (not extracted_codes.get('isbn_barcode') and not extracted_codes.get('isbn_text')):
            # コードが検出されなかった場合
            return jsonify({
                'success': False,
                'message': 'バーコードやISBNコードを検出できませんでした。別の画像を試すか、手動で入力してください。'
            })
        
        # ISBNコードの抽出（バーコードまたはテキスト形式）
        isbn_code = None
        if extracted_codes.get('isbn_barcode'):
            isbn_code = extracted_codes['isbn_barcode']
        elif extracted_codes.get('isbn_text'):
            # ISBN文字列からハイフンと空白を削除し、数字のみを抽出
            isbn_text = extracted_codes['isbn_text']
            isbn_code = ''.join(c for c in isbn_text if c.isdigit() or c.upper() == 'X')
            # ISBN-10の場合はISBN-13に変換（必要な場合）
            if len(isbn_code) == 10:
                # ISBN-10からISBN-13への変換ロジックを実装（省略）
                pass
        
        # APIサービス初期化
        api_service = ApiService(
            current_app.config['OPENBD_API_URL'],
            current_app.config['NDL_API_URL'],
            os.path.join(current_app.static_folder, 'covers')
        )
        
        # 書籍情報の検索
        book_info = None
        if isbn_code:
            book_info = api_service.lookup_isbn(isbn_code)
        
        if book_info:
            # 抽出したCコードと価格情報を追加
            if extracted_codes.get('c_code'):
                book_info['c_code'] = extracted_codes['c_code']
            if extracted_codes.get('price_code'):
                book_info['price_code'] = extracted_codes['price_code']
            
            return jsonify({
                'success': True,
                'message': '書籍情報が見つかりました',
                'codes': extracted_codes,
                'book': book_info
            })
        else:
            # 書籍情報が見つからないが、コードは抽出できた場合
            return jsonify({
                'success': True,
                'message': 'コードを検出しましたが、書籍情報は見つかりませんでした',
                'codes': extracted_codes
            })
    
    finally:
        # 一時ファイルの削除
        try:
            os.unlink(temp_path)
        except:
            pass

@barcode_bp.route('/lookup', methods=['GET'])
def lookup():
    """
    ISBN/JANコードから書籍情報を検索
    """
    code = request.args.get('code', '')
    
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    # APIサービス初期化
    api_service = ApiService(
        current_app.config['OPENBD_API_URL'],
        current_app.config['NDL_API_URL'],
        os.path.join(current_app.static_folder, 'covers')
    )
    
    # 書籍情報の検索
    book_info = api_service.lookup_isbn(code)
    
    if book_info:
        return jsonify({
            'success': True,
            'message': '書籍情報が見つかりました',
            'book': book_info
        })
    else:
        return jsonify({
            'success': False,
            'message': '書籍情報が見つかりませんでした'
        })
