import cv2
import os
import re
from werkzeug.utils import secure_filename

# 必要なライブラリをインポート（インストールが必要）
# pyzbar - バーコード認識用
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
except ImportError:
    print("警告: pyzbarライブラリがインストールされていません。バーコード認識が制限されます。")
    PYZBAR_AVAILABLE = False

# pytesseract - OCR認識用
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    print("警告: pytesseractライブラリがインストールされていません。Cコード認識が制限されます。")
    TESSERACT_AVAILABLE = False

class AlternativeBarcodeService:
    @staticmethod
    def process_barcode_image(image_file):
        """
        画像からバーコード/QRコード/Cコードを検出する
        
        Args:
            image_file: 画像ファイルのパス
            
        Returns:
            list: 検出されたバーコード情報のリスト
        """
        # OpenCVで画像読み込み
        image = cv2.imread(image_file)
        if image is None:
            print(f"画像の読み込みに失敗しました: {image_file}")
            return []
        
        # グレースケール変換
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        results = []
        
        # 1. pyzbarを使用してバーコード検出（利用可能な場合）
        if PYZBAR_AVAILABLE:
            try:
                # pyzbarでバーコードを検出
                barcodes = pyzbar_decode(image)
                
                for barcode in barcodes:
                    # バーコードデータをデコード
                    barcode_data = barcode.data.decode('utf-8')
                    barcode_type = barcode.type
                    
                    # バーコードタイプを正規化
                    if barcode_type.lower() in ['ean13', 'ean_13']:
                        # ISBN-13は通常EAN-13として検出される
                        if len(barcode_data) == 13 and barcode_data.startswith('978'):
                            barcode_type = 'ISBN13'
                        else:
                            barcode_type = 'EAN13'
                    
                    results.append({
                        'text': barcode_data,
                        'type': barcode_type,
                        'rect': {
                            'x': barcode.rect.left,
                            'y': barcode.rect.top,
                            'width': barcode.rect.width,
                            'height': barcode.rect.height
                        }
                    })
            except Exception as e:
                print(f"pyzbarによるバーコード検出エラー: {e}")
        
        # 2. OpenCVを使用してQRコード検出
        if not results:  # pyzbarで検出できなかった場合のフォールバック
            try:
                qr_detector = cv2.QRCodeDetector()
                retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(gray)
                
                if retval and len(decoded_info) > 0:
                    for info in decoded_info:
                        if info:  # 空でない情報がある場合
                            results.append({
                                'text': info,
                                'type': 'qrcode'  # QRコードとして報告
                            })
            except Exception as e:
                print(f"QRコード検出エラー: {e}")
        
        # 3. Cコードの検出を試みる（テキスト認識による方法）
        c_code = AlternativeBarcodeService.extract_c_code_from_image(gray)
        if c_code:
            results.append({
                'text': c_code,
                'type': 'c_code'
            })
        
        return results
        
    @staticmethod
    def extract_c_code_from_image(gray_image):
        """
        画像からCコードを抽出する
        Cコードは通常「C○○○○」の形式
        
        Args:
            gray_image: グレースケール画像
            
        Returns:
            str: 検出されたCコード、または空文字列
        """
        try:
            # 画像を二値化して処理しやすくする
            _, binary = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCRの代わりに、Cコードを検出するためのカスタム処理を行う
            # この部分は実際にはより高度なOCRライブラリ（例：Tesseract OCR）を使用するとよい
            
            # 今回は簡易的なアプローチとして、Cコードパターンを持つ領域のみを特定する
            # 実際の実装ではOCRライブラリを使用して、より正確なテキスト抽出を行うべき
            
            # この簡易実装では検出できないため、空文字列を返す
            return ""
            
        except Exception as e:
            print(f"Cコード抽出エラー: {e}")
            return ""
    
    @staticmethod
    def save_uploaded_image(file, upload_folder):
        """
        アップロードされた画像を保存する
        
        Args:
            file: アップロードされたファイルオブジェクト
            upload_folder: 保存先フォルダのパス
            
        Returns:
            str: 保存されたファイルのパス
        """
        filename = secure_filename(file.filename)
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        return file_path
