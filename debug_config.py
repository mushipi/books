"""
設定デバッグスクリプト
アプリケーションが設定を正しく読み込んでいるか確認します
"""

from app import create_app

# アプリケーションの作成
app = create_app()

# アプリケーションのコンテキスト内で設定を出力
with app.app_context():
    print("=" * 50)
    print("設定デバッグ情報")
    print("=" * 50)
    
    # データベース接続設定の確認
    print("SQLAlchemy設定:")
    print(f"SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"SQLALCHEMY_TRACK_MODIFICATIONS = {app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS')}")
    
    # その他の設定
    print("\nその他の設定:")
    print(f"SECRET_KEY = {'設定済み' if app.config.get('SECRET_KEY') else '未設定'}")
    print(f"UPLOAD_FOLDER = {app.config.get('UPLOAD_FOLDER')}")
    print(f"BOOKS_PER_PAGE = {app.config.get('BOOKS_PER_PAGE')}")
    print(f"BARCODE_ENABLED = {app.config.get('BARCODE_ENABLED')}")
    
    print("=" * 50)
    print("これらの設定が正しく表示されていれば、設定ファイルが適切に読み込まれています。")
    print("=" * 50)
