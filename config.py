import os

class Config:
    # Flask設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-local-use'
    
    # データベース設定
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/books.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # アプリケーション設定
    UPLOAD_FOLDER = os.path.join('static', 'covers')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 外部API設定
    OPENBD_API_URL = 'https://api.openbd.jp/v1/get'
    NDL_API_URL = 'https://iss.ndl.go.jp/api/search'
    
    # ページネーション設定
    BOOKS_PER_PAGE = 12
    
    # Gemini API設定
    GEMINI_API_KEY = "AIzaSyAM_oZf_yZLe5aR0Ytr0A2UTCp2SIx6kAA"  # 本番環境では環境変数から取得することを推奨
    GEMINI_MODEL_NAME = "gemini-1.5-flash"

# クラスの属性をモジュールレベルで直接使えるようにエクスポート
SECRET_KEY = Config.SECRET_KEY
SQLALCHEMY_DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = Config.SQLALCHEMY_TRACK_MODIFICATIONS
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
OPENBD_API_URL = Config.OPENBD_API_URL
NDL_API_URL = Config.NDL_API_URL
BOOKS_PER_PAGE = Config.BOOKS_PER_PAGE
GEMINI_API_KEY = Config.GEMINI_API_KEY
GEMINI_MODEL_NAME = Config.GEMINI_MODEL_NAME
