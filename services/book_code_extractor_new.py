import cv2
import re
import os
import numpy as np
import base64
import json
import ctypes
import sys
import time
import hashlib
import tempfile
from werkzeug.utils import secure_filename

# Gemini APIクライアントのインポート
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("google.generativeaiライブラリを正常にロードしました")
except ImportError:
    print("警告: google.generativeaiライブラリがインストールされていません。Gemini機能は制限されます。")
    GEMINI_AVAILABLE = False

# pyzbarライブラリのロードを試行
try:
    # DLLファイルのパスを明示的に指定
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    libzbar_path = os.path.join(project_root, 'libzbar-64.dll')
    
    if os.path.exists(libzbar_path):
        # DLLを直接ロード
        try:
            zbar_lib = ctypes.CDLL(libzbar_path)
            print(f"libzbar-64.dllを直接ロードしました: {libzbar_path}")
            os.environ['PATH'] = project_root + os.pathsep + os.environ.get('PATH', '')
        except Exception as e:
            print(f"libzbar-64.dllのロードに失敗しました: {e}")
    
    # pyzbarをインポート
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
    print("pyzbarを正常にロードしました")
except Exception as e:
    print(f"警告: pyzbarライブラリのロード中にエラーが発生しました: {e}")
    PYZBAR_AVAILABLE = False

# pytesseractライブラリをインポート
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    print("警告: pytesseractライブラリがインストールされていません。テキスト認識が制限されます。")
    TESSERACT_AVAILABLE = False

class BookCodeExtractor:
    def __init__(self, use_ai_fallback=True, gemini_api_key="AIzaSyAM_oZf_yZLe5aR0Ytr0A2UTCp2SIx6kAA"):
        """
        書籍コード抽出クラスの初期化
        
        Args:
            use_ai_fallback: AIによるバックアップ認識を使用するかどうか
            gemini_api_key: Gemini APIのAPIキー
        """
        self.use_ai_fallback = use_ai_fallback
        self.gemini_api_key = gemini_api_key
        self.last_api_call = 0
        
        # キャッシュディレクトリの初期化
        self.cache_dir = os.path.join(project_root, 'cache', 'gemini')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Geminiモデルの初期化
        if use_ai_fallback and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro-vision')
                print("Gemini Visionモデルを初期化しました")
            except Exception as e:
                print(f"Gemini APIの初期化に失敗しました: {e}")
                self.use_ai_fallback = False
        else:
            # APIキーが提供されていないか、ライブラリが利用できない場合
            print("警告: Gemini APIが利用できないため、AIバックアップ認識は無効です。")
            self.use_ai_fallback = False
    
    def extract_codes_from_image(self, image_path):
        """
        画像から書籍コードを抽出する
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            dict: 抽出されたコード情報（ISBN, JAN, Cコード）
        """
        print(f"[情報] 画像の処理開始: {image_path}")
        
        # 画像の読み込み
        try:
            image = cv2.imread(image_path)
            if image is None:
                print(f"[エラー] 画像の読み込みに失敗しました: {image_path}")
                return {}
            
            # グレースケール変換
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
        except Exception as e:
            print(f"[エラー] 画像処理中に例外が発生しました: {e}")
            return {}
        
        # 結果を格納する辞書
        results = {
            "isbn_barcode": None,    # ISBNバーコード (978から始まるEAN)
            "jan_barcode": None,     # JANコード (一般的なEAN)
            "isbn_text": None,       # ISBN文字列 (ISBN978-x-xx-xxxxxx-x形式)
            "c_code": None,          # Cコード (Cxxxx形式)
            "price_code": None       # 価格表示 (¥xxxE形式)
        }
        
        # バーコード検出処理（OpenCVのみを使用した代替実装）
        if PYZBAR_AVAILABLE:
            self._process_barcodes_with_pyzbar(image, results)
        else:
            # pyzbarが利用できない場合はOpenCVのQRコード検出機能を試す
            self._process_barcodes_with_opencv(gray, results)
        
        # テキスト検出処理
        confidence = 0.0
        if TESSERACT_AVAILABLE:
            confidence = self._process_text_with_ocr(gray, results)
        
        # OCRの信頼度が低く、AIバックアップが有効な場合
        if (confidence < 0.7 or not results["isbn_barcode"] or not results["c_code"]) and self.use_ai_fallback and GEMINI_AVAILABLE:
            print("OCRの信頼度が低いため、Gemini APIを使用します")
            self._process_with_gemini_api(image_path, results)
        
        return results
    
    def _optimize_image_for_gemini(self, image_path):
        """
        Gemini APIに送信する画像を最適化する
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("画像の読み込みに失敗しました")
            
            # 元の画像サイズ
            original_h, original_w = image.shape[:2]
            
            # サイズが大きすぎる場合はリサイズ（APIの制限内に）
            max_dimension = 1024
            if max(original_h, original_w) > max_dimension:
                scale_factor = max_dimension / max(original_h, original_w)
                new_size = (int(original_w * scale_factor), int(original_h * scale_factor))
                image = cv2.resize(image, new_size)
            
            # 画像の前処理（裏表紙のISBN部分が読みやすくなるように）
            # コントラスト調整
            alpha = 1.3  # コントラスト向上
            beta = 10    # 明るさ調整
            enhanced = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            
            # ノイズ除去
            denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
            
            # 一時ファイルとして保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_path = temp_file.name
            
            # 画像を高品質JPEGとして保存
            cv2.imwrite(temp_path, denoised, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            return temp_path
        
        except Exception as e:
            print(f"画像最適化エラー: {e}")
            return image_path
    
    def _process_barcodes_with_pyzbar(self, image, results):
        """
        pyzbarを使用してバーコードを処理する
        """
        try:
            # バーコードの検出
            barcodes = pyzbar_decode(image)
            
            for barcode in barcodes:
                # バーコードデータをデコード
                barcode_data = barcode.data.decode('utf-8')
                barcode_type = barcode.type
                
                # バーコードタイプを正規化
                if barcode_type.lower() in ['ean13', 'ean_13']:
                    # ISBN-13は通常EAN-13として検出される（978で始まる）
                    if len(barcode_data) == 13 and barcode_data.startswith('978'):
                        results["isbn_barcode"] = barcode_data
                    else:
                        results["jan_barcode"] = barcode_data
        except Exception as e:
            print(f"pyzbarによるバーコード処理エラー: {e}")
    
    def _process_barcodes_with_opencv(self, gray_image, results):
        """
        OpenCVを使用してQRコード/バーコードを検出する
        
        Args:
            gray_image: グレースケール画像
            results: 結果を格納する辞書
        """
        try:
            # QRコード検出器を初期化
            qr_detector = cv2.QRCodeDetector()
            
            # QRコード検出を試みる
            retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(gray_image)
            
            if retval and decoded_info:
                for info in decoded_info:
                    if info:  # 空でない情報がある場合
                        # 情報を分析
                        if len(info) == 13 and info.startswith('978'):
                            results["isbn_barcode"] = info
                        elif len(info) == 13:
                            results["jan_barcode"] = info
        except Exception as e:
            print(f"OpenCVによるQRコード検出エラー: {e}")
    
    def _process_text_with_ocr(self, gray_image, results):
        """
        OCRを使用してテキストを抽出する
        
        Returns:
            float: 認識の信頼度（0-1）
        """
        confidence = 0.0
        try:
            # 複数の前処理パターンを試行
            processing_methods = [
                # 基本的な前処理
                {
                    'denoise': lambda img: cv2.fastNlMeansDenoising(img, None, 10, 7, 21),
                    'enhance': lambda img: cv2.convertScaleAbs(img, alpha=1.5, beta=10),
                    'binary': lambda img: cv2.adaptiveThreshold(
                        img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                    )
                },
                # コントラスト強調
                {
                    'denoise': lambda img: cv2.fastNlMeansDenoising(img, None, 10, 7, 21),
                    'enhance': lambda img: cv2.convertScaleAbs(img, alpha=2.0, beta=5),
                    'binary': lambda img: cv2.threshold(
                        img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                    )[1]
                },
                # エッジ強調
                {
                    'denoise': lambda img: cv2.GaussianBlur(img, (5, 5), 0),
                    'enhance': lambda img: cv2.Canny(img, 100, 200),
                    'binary': lambda img: img  # エッジ検出済みなので二値化は不要
                }
            ]
            
            # 結果の候補
            ocr_results = []
            
            # 各処理方法で試行
            for method in processing_methods:
                try:
                    # 前処理
                    processed = method['denoise'](gray_image)
                    processed = method['enhance'](processed)
                    
                    if 'binary' in method and callable(method['binary']):
                        processed = method['binary'](processed)
                    
                    # モルフォロジー処理
                    if len(processed.shape) == 2:  # グレースケールまたは二値画像の場合
                        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
                    
                    # OCRでテキスト抽出
                    # Tesseractの設定を最適化
                    custom_config = r'--oem 3 --psm 11 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-¥E'
                    text = pytesseract.image_to_string(processed, config=custom_config)
                    ocr_results.append(text)
                    
                except Exception as e:
                    print(f"OCR処理方法エラー: {e}")
            
            # 複数の結果から最適なものを選択
            for text in ocr_results:
                # ISBN文字列を探す
                isbn_pattern = re.compile(r'ISBN[\s-]?978[\s-]?[0-9][\s-]?[0-9]{1,2}[\s-]?[0-9]{5,6}[\s-]?[0-9X]')
                isbn_matches = isbn_pattern.findall(text)
                if isbn_matches and not results["isbn_text"]:
                    results["isbn_text"] = isbn_matches[0].replace(' ', '')
                    confidence += 0.4
                
                # Cコードを探す
                c_code_pattern = re.compile(r'C[0-9]{4}')
                c_code_matches = c_code_pattern.findall(text)
                if c_code_matches and not results["c_code"]:
                    results["c_code"] = c_code_matches[0]
                    confidence += 0.3
                
                # 価格コードを探す
                price_pattern = re.compile(r'¥[0-9]{2,5}E')
                price_matches = price_pattern.findall(text)
                if price_matches and not results["price_code"]:
                    results["price_code"] = price_matches[0]
                    confidence += 0.3
            
        except Exception as e:
            print(f"OCR処理エラー: {e}")
        
        return confidence
    
    def _process_with_gemini_api(self, image_path, results):
        """
        Gemini APIを使用して画像を処理する（キャッシュと制限対策付き）
        """
        try:
            # 画像のハッシュ計算（同じ画像なら同じ結果を返すように）
            with open(image_path, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()
            
            # キャッシュをチェック
            cache_file = os.path.join(self.cache_dir, f'gemini_cache_{image_hash}.json')
            
            # キャッシュがあればそれを使用
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_results = json.load(f)
                        
                    # 結果を更新
                    for key, value in cached_results.items():
                        if key in results and (results[key] is None and value is not None and value != "null"):
                            results[key] = value
                            
                    print(f"[情報] キャッシュから結果を読み込みました: {image_path}")
                    return
                except Exception as e:
                    print(f"[警告] キャッシュ読み込みエラー: {e}")
            
            # APIレート制限対策
            if hasattr(self, 'last_api_call') and time.time() - self.last_api_call < 2:
                # 最小2秒間隔を空ける
                time.sleep(2 - (time.time() - self.last_api_call))
            
            # 画像の最適化
            optimized_image_path = self._optimize_image_for_gemini(image_path)
            
            try:
                # Google Generative AIライブラリを使用
                prompt_text = """
                この画像は書籍の裏表紙です。以下の情報を正確に抽出してください：
                
                1. ISBNコード: 通常「ISBN」で始まり、「978」や「979」から始まる13桁の数字（例：ISBN978-4-00-112233-4）
                2. JANコード: バーコード下に印刷された13桁の数字（通常ISBN-13と同じ）
                3. Cコード: 「C」で始まる5文字のコード（例：C0095）
                4. 価格表示: 「¥」で始まり、「E」で終わる表記（例：¥700E）
                
                画像が不鮮明な場合も可能な限り識別してください。桁数や形式が合わない場合は無視してください。
                以下のJSON形式のみで回答してください：
                {
                    "isbn_text": "ISBNコード（形式：ISBN978-x-xx-xxxxxx-x）",
                    "jan_barcode": "JANコード（13桁の数字）",
                    "c_code": "Cコード（形式：Cxxxx）",
                    "price_code": "価格表示（形式：¥xxxE）"
                }
                
                抽出できない情報はnullとしてください。JSONのみを返してください。
                """
                
                # 画像を読み込む
                img_data = open(optimized_image_path, 'rb').read()
                
                # Gemini APIにリクエスト
                response = self.gemini_model.generate_content(
                    [prompt_text, genai.types.Blob(data=img_data, mime_type="image/jpeg")],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        top_p=0.95,
                        max_output_tokens=1024
                    )
                )
                
                # 最終API呼び出し時間を記録
                self.last_api_call = time.time()
                
                # レスポンスの解析
                response_text = response.text
                
                # JSON部分を抽出
                try:
                    # { } の間のテキストを抽出
                    json_text = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_text:
                        extracted_data = json.loads(json_text.group(0))
                        
                        # 結果を更新（既存の値がある場合は上書きしない）
                        for key, value in extracted_data.items():
                            if key in results and (results[key] is None and value is not None and value != "null"):
                                results[key] = value
                        
                        # キャッシュに保存
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(extracted_data, f)
                
                except json.JSONDecodeError as e:
                    print(f"JSON解析エラー: {e}")
                
            finally:
                # 一時ファイルの削除
                if os.path.exists(optimized_image_path) and optimized_image_path != image_path:
                    try:
                        os.remove(optimized_image_path)
                    except:
                        pass
            
        except Exception as e:
            print(f"API処理エラー: {e}")
    
    def process_image_file(self, image_file, upload_folder=None):
        """
        アップロードされた画像ファイルを処理する
        
        Args:
            image_file: アップロードされたファイルオブジェクト
            upload_folder: 保存先フォルダ（指定がない場合は一時ファイルを使用）
            
        Returns:
            dict: 抽出されたコード情報
        """
        import tempfile
        
        if upload_folder:
            # 指定フォルダに保存
            filename = secure_filename(image_file.filename)
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)
            
            # 処理後にファイルを削除しない
            results = self.extract_codes_from_image(file_path)
            return results
        else:
            # 一時ファイルとして保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_path = temp_file.name
                image_file.save(temp_path)
            
            try:
                # 処理
                results = self.extract_codes_from_image(temp_path)
                return results
            finally:
                # 一時ファイルの削除
                try:
                    os.unlink(temp_path)
                except:
                    pass
