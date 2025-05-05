from flask import Flask, render_template, jsonify, send_from_directory
import os
import glob
from models.location import Location
from models.genre import Genre 
from models.tag import Tag
from models.book import db, Book

def create_app():
    """テスト用アプリケーションの作成"""
    app = Flask(__name__)
    
    # 設定の読み込み
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'books.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 静的ファイルの設定
    app.static_folder = 'static'
    app.static_url_path = ''
    
    # データベースの初期化
    db.init_app(app)
    
    return app

# この部分はグローバルスコープで使用せず、add_direct_image_routes関数内で定義する
# 以下の関数はcreate_app()で作成されたappにバインドされる必要がある

# 表紙画像URLを生成
def generate_direct_cover_url(filename, request=None):
    """直接アクセス用の表紙画像URLを生成"""
    if not filename:
        return None
        
    # ファイル名のみを抽出
    base_filename = os.path.basename(filename)
    
    # サーバーURLを取得（リクエストがあればホスト情報を使用）
    if request:
        # ホストとスキーマを使ってURLを生成
        base_url = f"{request.scheme}://{request.host}"
        return f"{base_url}/direct-cover/{base_filename}"
    else:
        # ローカルのファイルURLを生成
        base_dir = os.path.abspath(os.path.dirname(__file__))
        covers_dir = os.path.join(base_dir, 'static', 'covers')
        file_path = os.path.join(covers_dir, base_filename)
        
        # ファイルが存在するか確認
        if not os.path.isfile(file_path):
            return None
            
        # ファイルURLを生成（スラッシュに変換）
        url_path = file_path.replace('\\', '/')
        return f"file:///{url_path}"

# アプリケーションに組み込むための関数
def add_direct_image_routes(app):
    """直接表紙画像を提供するルートをアプリケーションに追加"""
    
    @app.route('/direct-cover/<path:filename>')
    def direct_cover(filename):
        """表紙画像を直接提供する"""
        covers_dir = os.path.join(app.root_path, 'static', 'covers')
        return send_from_directory(covers_dir, filename)
    
    @app.route('/api/covers')
    def list_covers():
        """表紙画像の一覧をJSONで提供"""
        covers_dir = os.path.join(app.root_path, 'static', 'covers')
        
        # ディレクトリの存在確認
        if not os.path.exists(covers_dir):
            return jsonify({"error": "Covers directory not found"}), 404
        
        # 画像ファイルを検索
        image_files = []
        for ext in ['jpg', 'jpeg', 'png', 'gif']:
            pattern = os.path.join(covers_dir, f"*.{ext}")
            found = glob.glob(pattern)
            for img_path in found:
                filename = os.path.basename(img_path)
                isbn = os.path.splitext(filename)[0]
                image_files.append({
                    "filename": filename,
                    "isbn": isbn,
                    "url": f"/direct-cover/{filename}"
                })
        
        return jsonify({"covers": image_files})
    
    # コンテキストプロセッサにヘルパー関数を追加
    @app.context_processor
    def inject_direct_image_helpers():
        """直接表紙画像アクセス用のヘルパー関数を注入"""
        
        def get_direct_cover_url(cover_path):
            """表紙画像の直接アクセスURLを生成"""
            if not cover_path:
                return None
                
            # パスからファイル名のみを抽出
            if '/' in cover_path:
                filename = cover_path.split('/')[-1]
            elif '\\' in cover_path:
                filename = cover_path.split('\\')[-1]
            else:
                filename = cover_path
                
            # 直接アクセス用のURLを返す
            return f"/direct-cover/{filename}"
        
        return {
            'get_direct_cover_url': get_direct_cover_url
        }
    
    # デバッグ用のルート
    if app.debug:
        @app.route('/test-covers')
        def test_covers():
            """表紙画像テスト用ページ"""
            covers_dir = os.path.join(app.root_path, 'static', 'covers')
            
            # 画像ファイルの検索
            images = []
            for ext in ['jpg', 'jpeg', 'png', 'gif']:
                pattern = os.path.join(covers_dir, f"*.{ext}")
                found = glob.glob(pattern)
                for img_path in found:
                    filename = os.path.basename(img_path)
                    isbn = os.path.splitext(filename)[0]
                    images.append({
                        "filename": filename,
                        "isbn": isbn,
                        "url": f"/direct-cover/{filename}"
                    })
            
            return render_template('test_covers.html', images=images)
            
    print(f"表紙画像の直接アクセス機能が有効化されました")

# メインで実行された場合はテスト用サーバーを起動
if __name__ == "__main__":
    app = create_app()
    
    # テスト用ルートを追加
    @app.route('/')
    def index():
        """テスト用トップページ"""
        return """
        <html>
            <head><title>表紙画像直接アクセステスト</title></head>
            <body>
                <h1>表紙画像直接アクセステスト</h1>
                <p><a href="/api/covers">表紙画像一覧 (JSON)</a></p>
                <p><a href="/test-covers">表紙画像テスト</a></p>
            </body>
        </html>
        """
    
    # 直接アクセス用ルートを追加
    add_direct_image_routes(app)
    
    # アプリケーションの実行
    print("表紙画像直接アクセステストサーバーを起動します...")
    print("http://localhost:5050/ にアクセスしてください")
    app.run(debug=True, port=5050)
