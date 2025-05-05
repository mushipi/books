from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, send_file
from flask_login import login_required, current_user
import os
import tempfile
import zipfile
import json
import csv
from werkzeug.utils import secure_filename
from datetime import datetime

from services.book_code_extractor import BookCodeExtractor

# Blueprintの作成
batch_bp = Blueprint('batch', __name__, url_prefix='/batch')

@batch_bp.route('/')
@login_required
def index():
    """
    バッチ処理画面を表示
    """
    return render_template('batch/index.html')

@batch_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    """
    複数画像のアップロードとバッチ処理
    """
    if 'images' not in request.files:
        return jsonify({'error': 'No image files provided'}), 400
    
    # アップロードされたファイル
    files = request.files.getlist('images')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400
    
    # 処理オプション
    use_ai = request.form.get('use_ai', 'true').lower() == 'true'
    output_format = request.form.get('output_format', 'json')
    
    # 一時フォルダの作成
    temp_dir = tempfile.mkdtemp()
    
    try:
        # ファイルの保存と処理
        file_paths = []
        for file in files:
            if file and file.filename.lower().endswith(('.jpg', '.jpeg')):
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
                file_paths.append(file_path)
        
        if not file_paths:
            return jsonify({'error': 'No valid JPEG images found'}), 400
        
        # BookCodeExtractorの初期化
        try:
            extractor = BookCodeExtractor(
                use_ai_fallback=use_ai,
                gemini_api_key=current_app.config.get('GEMINI_API_KEY')
            )
        except Exception as e:
            return jsonify({
                'error': f'BookCodeExtractorの初期化中にエラーが発生しました: {str(e)}'
            }), 500
        
        # 処理結果の保存先
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file_name = f"book_codes_{timestamp}.{output_format}"
        results_file_path = os.path.join(temp_dir, results_file_name)
        
        # 各画像ファイルの処理
        if output_format == 'csv':
            with open(results_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                # ヘッダーの書き込み
                csv_writer.writerow([
                    "ファイル名", "ISBNバーコード", "JANバーコード", 
                    "ISBN文字列", "Cコード", "価格コード"
                ])
                
                results = []
                for file_path in file_paths:
                    file_name = os.path.basename(file_path)
                    try:
                        # 画像からコードを抽出
                        extracted_codes = extractor.extract_codes_from_image(file_path)
                        
                        # CSVに結果を書き込み
                        csv_writer.writerow([
                            file_name,
                            extracted_codes.get("isbn_barcode", ""),
                            extracted_codes.get("jan_barcode", ""),
                            extracted_codes.get("isbn_text", ""),
                            extracted_codes.get("c_code", ""),
                            extracted_codes.get("price_code", "")
                        ])
                        
                        # 結果を保存
                        result = {
                            'file_name': file_name,
                            'codes': extracted_codes
                        }
                        results.append(result)
                    except Exception as e:
                        results.append({
                            'file_name': file_name,
                            'error': str(e)
                        })
        else:  # JSON
            results = []
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                try:
                    # 画像からコードを抽出
                    extracted_codes = extractor.extract_codes_from_image(file_path)
                    
                    # 結果を保存
                    result = {
                        'file_name': file_name,
                        'codes': extracted_codes
                    }
                    results.append(result)
                except Exception as e:
                    results.append({
                        'file_name': file_name,
                        'error': str(e)
                    })
            
            # JSONファイルに結果を保存
            with open(results_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(results, json_file, ensure_ascii=False, indent=2)
        
        # ZIPファイルの作成
        zip_file_path = os.path.join(temp_dir, f"book_codes_{timestamp}.zip")
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            zipf.write(results_file_path, arcname=results_file_name)
        
        # ZIPファイルをダウンロード
        return send_file(
            zip_file_path,
            as_attachment=True,
            download_name=f"book_codes_{timestamp}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # 一時ファイルの削除は省略（send_file後に削除すると問題が発生する可能性があるため）
        # 定期的なクリーンアップタスクで削除することを推奨
        pass

@batch_bp.route('/api/process', methods=['POST'])
@login_required
def api_process():
    """
    APIとしてのバッチ処理（JSON形式のレスポンスを返す）
    """
    if 'images' not in request.files:
        return jsonify({'error': 'No image files provided'}), 400
    
    # アップロードされたファイル
    files = request.files.getlist('images')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400
    
    # 処理オプション
    use_ai = request.form.get('use_ai', 'true').lower() == 'true'
    
    # 一時フォルダの作成
    temp_dir = tempfile.mkdtemp()
    
    try:
        # ファイルの保存
        file_paths = []
        for file in files:
            if file and file.filename.lower().endswith(('.jpg', '.jpeg')):
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
                file_paths.append((filename, file_path))
        
        if not file_paths:
            return jsonify({'error': 'No valid JPEG images found'}), 400
        
        # BookCodeExtractorの初期化
        try:
            extractor = BookCodeExtractor(
                use_ai_fallback=use_ai,
                gemini_api_key=current_app.config.get('GEMINI_API_KEY')
            )
        except Exception as e:
            return jsonify({
                'error': f'BookCodeExtractorの初期化中にエラーが発生しました: {str(e)}',
                'success': False
            }), 500
        
        # 各画像ファイルの処理
        results = []
        for file_name, file_path in file_paths:
            try:
                # 画像からコードを抽出
                extracted_codes = extractor.extract_codes_from_image(file_path)
                
                # 結果を保存
                results.append({
                    'file_name': file_name,
                    'codes': extracted_codes,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'file_name': file_name,
                    'error': str(e),
                    'success': False
                })
        
        # 結果の返却
        return jsonify({
            'success': True,
            'results': results,
            'total': len(file_paths),
            'processed': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
    
    finally:
        # 一時ファイルの削除（実際の実装では、より堅牢なクリーンアップ処理が必要）
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
