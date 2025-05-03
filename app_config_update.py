import os

# 環境変数の更新
os.environ['GEMINI_API_KEY'] = 'AIzaSyAM_oZf_yZLe5aR0Ytr0A2UTCp2SIx6kAA'

# アプリケーション設定の読み込み
from app import create_app

# アプリケーションの作成と実行
app = create_app()

# 環境変数を確認し、ホストIPとポートを設定（デフォルトは127.0.0.1:5000）
host = os.environ.get('FLASK_HOST', '0.0.0.0')
port = int(os.environ.get('FLASK_PORT', 5000))

# アプリケーションの状態を表示
print('='*50)
print('本管理アプリケーションを起動します')
print(f'ホスト: {host}, ポート: {port}')
print(f"Gemini APIキー: {os.environ.get('GEMINI_API_KEY', 'なし')}")

if app.config.get('BARCODE_ENABLED', False):
    print('バーコードスキャン機能: 有効')
else:
    print('バーコードスキャン機能: 無効')
print('='*50)

# 開発サーバーの実行
if __name__ == '__main__':
    app.run(host=host, port=port, debug=True)
