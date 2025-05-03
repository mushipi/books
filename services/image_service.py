from PIL import Image
from io import BytesIO
import os

class ImageService:
    @staticmethod
    def create_thumbnail(image_path, max_size=(300, 400)):
        """
        画像のサムネイルを作成する
        
        Args:
            image_path: 元画像のファイルパス
            max_size: サムネイルの最大サイズ（幅、高さ）
            
        Returns:
            bytes: サムネイル画像のバイナリデータ
        """
        try:
            with Image.open(image_path) as img:
                img.thumbnail(max_size)
                buffer = BytesIO()
                img.save(buffer, format="JPEG")
                return buffer.getvalue()
        except Exception as e:
            print(f"サムネイル作成エラー: {e}")
            return None
    
    @staticmethod
    def save_thumbnail(image_path, save_path, max_size=(300, 400)):
        """
        サムネイルを作成して保存する
        
        Args:
            image_path: 元画像のファイルパス
            save_path: 保存先のファイルパス
            max_size: サムネイルの最大サイズ（幅、高さ）
            
        Returns:
            bool: 成功した場合はTrue、それ以外はFalse
        """
        try:
            # 保存先ディレクトリの確認
            save_dir = os.path.dirname(save_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                
            with Image.open(image_path) as img:
                img.thumbnail(max_size)
                img.save(save_path, "JPEG")
                return True
        except Exception as e:
            print(f"サムネイル保存エラー: {e}")
            return False
