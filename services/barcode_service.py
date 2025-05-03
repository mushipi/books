import cv2
from pyzbar import pyzbar
import os
from werkzeug.utils import secure_filename

class BarcodeService:
    @staticmethod
    def process_barcode_image(image_file):
        """
        画像からバーコード情報を読み取る
        
        Args:
            image_file: 画像ファイルのパス
            
        Returns:
            list: 検出されたバーコード情報のリスト
        """
        # OpenCVで画像読み込み
        image = cv2.imread(image_file)
        
        # グレースケール変換
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # バーコード検出
        barcodes = pyzbar.decode(gray)
        
        results = []
        for barcode in barcodes:
            # バーコードデータ取得
            barcode_text = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            
            results.append({
                'text': barcode_text,
                'type': barcode_type
            })
        
        return results
    
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
