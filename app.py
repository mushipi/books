from flask import Flask, render_template, redirect, url_for, Markup, send_from_directory, request, jsonify
from flask_login import current_user, login_required
from models.book import db, Book
from models.genre import Genre
from models.tag import Tag
from models.location import Location
from controllers.book_controller import book_bp
from controllers.settings_controller import settings_bp
from controllers.batch_controller import batch_bp
from controllers.bulk_import_controller_new import bulk_import_bp
from controllers.auth.auth_controller import auth_bp
from auth_helper import init_login_manager, create_admin_user
from helpers import get_cover_url, cover_image_exists, get_absolute_cover_path
from direct_images import add_direct_image_routes
import os
import importlib.util
import sys

def create_app():
    # Flaskアプリケーションの初期化
    app = Flask(__name__)
    
    # 静的ファイルの設定を明示的に追加
    app.static_folder = 'static'
    app.static_url_path = ''
    print(f"静的ファイルフォルダ: {app.static_folder}")
    print(f"静的ファイルURLパス: {app.static_url_path}")
    
    # 設定の読み込み
    # 直接必要な設定を定義
    # データベースパスを絶対パスに変更
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'books.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-local-use'
    
    # アップロードフォルダの設定
    upload_folder = os.path.join('static', 'covers')
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # アップロードフォルダが存在するか確認し、存在しない場合は作成
    upload_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), upload_folder)
    try:
        os.makedirs(upload_path, exist_ok=True)
        print(f"アップロードフォルダを作成/確認しました: {upload_path}")
    except OSError as e:
        print(f"アップロードフォルダの作成に失敗しました: {e}")
    
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    app.config['OPENBD_API_URL'] = 'https://api.openbd.jp/v1/get'
    app.config['NDL_API_URL'] = 'https://iss.ndl.go.jp/api/search'
    app.config['BOOKS_PER_PAGE'] = 12
    
    # Gemini API設定
    app.config['USE_AI_FALLBACK'] = os.environ.get('USE_AI_FALLBACK', 'true').lower() == 'true'
    app.config['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY', 'AIzaSyAM_oZf_yZLe5aR0Ytr0A2UTCp2SIx6kAA')
    app.config['GEMINI_MODEL_NAME'] = os.environ.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash')
    print(f"Gemini APIバックアップ認識: {'\x1b[32m有効\x1b[0m' if app.config.get('USE_AI_FALLBACK') else '\x1b[31m無効\x1b[0m'}")    
    
    # 設定が正しく読み込まれたことを確認
    print(f"SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    
    # インスタンスフォルダの確保
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    try:
        os.makedirs(instance_path, exist_ok=True)
        print(f"インスタンスディレクトリを作成しました: {instance_path}")
    except OSError as e:
        print(f"インスタンスディレクトリの作成に失敗しました: {e}")
    
    # 一時フォルダの作成
    temp_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'temp')
    try:
        os.makedirs(temp_path, exist_ok=True)
        print(f"一時ファイルディレクトリを作成しました: {temp_path}")
    except OSError as e:
        print(f"一時ファイルディレクトリの作成に失敗しました: {e}")
    
    # データベースの初期化
    db.init_app(app)
    app.db = db  # アプリオブジェクトにdbを保存（コントローラでアクセス可能に）
    
    # Blueprintの登録
    app.register_blueprint(book_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(batch_bp)
    app.register_blueprint(bulk_import_bp)
    app.register_blueprint(auth_bp)
    
    # LoginManagerの初期化
    login_manager = init_login_manager(app)
    
    # バーコード機能のオプション化
    # 環境変数で強制無効化されているか確認
    if os.environ.get('DISABLE_BARCODE', '').lower() == 'true':
        app.config['BARCODE_ENABLED'] = False
        print('バーコードスキャン機能は強制無効化されています')
    else:
        try:
            # 代替バーコードサービスを使用
            import cv2
            # OpenCVが利用可能かチェック
            cv2_spec = importlib.util.find_spec('cv2')
            
            if cv2_spec is not None:
                # OpenCVが利用可能な場合は代替バーコードサービスを使用
                app.config['USE_ALTERNATIVE_BARCODE'] = True
                from controllers.barcode_controller import barcode_bp
                app.register_blueprint(barcode_bp)
                app.config['BARCODE_ENABLED'] = True
                print('代替バーコードスキャン機能が有効化されました')
            else:
                app.config['BARCODE_ENABLED'] = False
                app.config['USE_ALTERNATIVE_BARCODE'] = False
                print('バーコードスキャン機能に必要なライブラリが見つかりません')
        except Exception as e:
            app.config['BARCODE_ENABLED'] = False
            app.config['USE_ALTERNATIVE_BARCODE'] = False
            print(f'バーコードスキャン機能の初期化エラー: {str(e)}')
    
    # Gemini APIライブラリの確認
    try:
        import google.generativeai
        app.config['GEMINI_API_AVAILABLE'] = True
        print('Gemini API ライブラリが利用可能です')
    except ImportError:
        app.config['GEMINI_API_AVAILABLE'] = False
        print('Gemini API ライブラリがインストールされていません')
        print('一括取り込みの高度な認識機能を使用するには、次のコマンドを実行してください：')
        print('pip install google-generativeai')
        
    # 直接表紙画像アクセス機能を追加
    add_direct_image_routes(app)
    
    # 表紙画像の絶対パスルート
    @app.route('/absolute-cover/<path:filename>')
    def absolute_cover(filename):
        """絶対パスで表紙画像を提供する"""
        covers_dir = os.path.join(app.root_path, 'static', 'covers')
        return send_from_directory(covers_dir, filename)
    
    # 参照された表紙画像の情報を取得するAPI
    @app.route('/api/cover-info/<path:filename>')
    def cover_info(filename):
        """表紙画像の情報をJSONで返す"""
        covers_dir = os.path.join(app.root_path, 'static', 'covers')
        file_path = os.path.join(covers_dir, filename)
        
        if os.path.isfile(file_path):
            # ファイルが存在する場合
            # WindowsパスをURL形式に変換
            url_path = file_path.replace("\\", "/")
            return jsonify({
                "filename": filename,
                "exists": True,
                "size": os.path.getsize(file_path),
                "file_url": f"file:///{url_path}",
                "direct_url": f"/direct-cover/{filename}",
                "absolute_url": f"/absolute-cover/{filename}"
            })
        else:
            # ファイルが存在しない場合
            return jsonify({"filename": filename, "exists": False})
    
    # ルートルートの設定
    @app.route('/')
    def index():
        return redirect(url_for('books.index'))
        
    # ホームルートに認証を追加
    @app.route('/home')
    @login_required
    def home():
        return redirect(url_for('books.index'))
    
    # 静的ファイルルーティングの確認
    @app.route('/covers/<path:filename>')
    def custom_static_covers(filename):
        """coversディレクトリのファイルを直接提供する"""
        print(f"アクセスされたカバー画像: {filename}")
        return app.send_static_file(os.path.join('covers', filename))
    
    # エラーハンドラの設定
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error/500.html'), 500
    
    # コンテキストプロセッサの追加
    @app.context_processor
    def inject_common_data():
        """共通データをテンプレートに注入"""
        # 書籍の総数
        book_count = Book.query.count()
        
        # ジャンルの一覧
        genres = Genre.query.order_by(Genre.name).all()
        
        # タグの一覧（使用頻度順）
        tags = Tag.query.all()
        tag_usage = {}
        for tag in tags:
            tag_usage[tag.id] = len(tag.books.all())
        
        # 使用頻度でソート
        sorted_tags = sorted(tags, key=lambda t: tag_usage.get(t.id, 0), reverse=True)
        
        # 収納場所の一覧
        locations = Location.query.order_by(Location.name).all()
        
        # ヘルパー関数をテンプレートにエクスポート
        return {
            'book_count': book_count,
            'genres': genres,
            'tags': sorted_tags[:10],  # 上位10件のみ
            'locations': locations,
            'get_cover_url': get_cover_url,
            'cover_image_exists': cover_image_exists,
            'get_absolute_cover_path': get_absolute_cover_path,
            'current_user': current_user  # current_userをテンプレートに注入
        }
    
    # nl2brフィルタの登録
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """改行を<br>タグに変換するフィルタ"""
        if text:
            return Markup(text.replace('\n', '<br>'))
        return ""
    
    # データベースの初期化コマンドの追加
    @app.cli.command('init-db')
    def init_db_command():
        """データベースを初期化するコマンド"""
        db.create_all()
        print('データベースを初期化しました')
    
    @app.cli.command('seed-db')
    def seed_db_command():
        """初期データを投入するコマンド"""
        # ジャンルの作成
        genres = [
            Genre(name="小説"),
            Genre(name="技術書"),
            Genre(name="ビジネス"),
            Genre(name="自己啓発"),
            Genre(name="歴史"),
            Genre(name="科学"),
            Genre(name="芸術"),
            Genre(name="趣味")
        ]
        
        for genre in genres:
            existing = Genre.query.filter_by(name=genre.name).first()
            if not existing:
                db.session.add(genre)
        
        # 収納場所の作成
        locations = [
            Location(name="本棚A - 上段", description="リビングの大きい本棚"),
            Location(name="本棚A - 中段", description="リビングの大きい本棚"),
            Location(name="本棚B", description="書斎の本棚"),
            Location(name="収納ボックス", description="クローゼット内の箱")
        ]
        
        for location in locations:
            existing = Location.query.filter_by(name=location.name).first()
            if not existing:
                db.session.add(location)
        
        db.session.commit()
        print('初期データの投入が完了しました')
    
    return app

# アプリケーションのエントリーポイント
if __name__ == '__main__':
    app = create_app()
    
    # 環境変数を確認し、ホストIPとポートを設定（デフォルトは127.0.0.1:5000）
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    # 初期管理者ユーザーの作成
    try:
        admin_user = create_admin_user(app, 'admin', 'admin@example.com', 'password')
        if admin_user:
            print('初期管理者ユーザーが利用可能です')
    except Exception as e:
        print(f'管理者ユーザー作成エラー: {str(e)}')
    
    # アプリケーションの状態を表示
    print('='*50)
    print('本管理アプリケーションを起動します')
    print(f'ホスト: {host}, ポート: {port}')
    
    if app.config.get('BARCODE_ENABLED', False):
        print('バーコードスキャン機能: 有効')
    else:
        print('バーコードスキャン機能: 無効 (ライブラリの互換性問題のため)')
        print('バーコード機能を有効化するには、fix_dependencies.batを実行してください')
    
    if app.config.get('GEMINI_API_AVAILABLE', False):
        print('Gemini API 一括取り込み機能: 有効')
    else:
        print('Gemini API 一括取り込み機能: 制限付き (ライブラリがインストールされていません)')
        print('高度な認識機能を有効化するには、install_gemini_api.batを実行してください')
    print('='*50)
    
    # 開発サーバーの実行 - デバッグモードはプロダクションでは無効化
    debug_mode = os.environ.get('FLASK_ENV', '') != 'production'
    app.run(host=host, port=port, debug=debug_mode)
