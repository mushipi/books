from flask_login import LoginManager
from models.users.user import User

def init_login_manager(app):
    """LoginManagerの初期化とセットアップ

    Args:
        app: Flaskアプリケーションインスタンス
    """
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    # ログインページの設定
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'この機能を利用するにはログインが必要です。'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        """ユーザーIDからユーザーオブジェクトを取得"""
        return User.query.get(int(user_id))
    
    return login_manager

def create_admin_user(app, username, email, password):
    """管理者ユーザーの作成

    Args:
        app: Flaskアプリケーションインスタンス
        username: 管理者ユーザー名
        email: 管理者のメールアドレス
        password: 管理者のパスワード

    Returns:
        作成されたユーザーオブジェクト
    """
    from models.users.user import User, db
    
    with app.app_context():
        # 既存の管理者ユーザーを確認
        existing_admin = User.query.filter_by(is_admin=True).first()
        if existing_admin:
            print(f"管理者ユーザーが既に存在します: {existing_admin.username}")
            return existing_admin
        
        # 既存のユーザー名をチェック
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"ユーザー名 '{username}' は既に使用されています")
            return None
        
        # 既存のメールアドレスをチェック
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            print(f"メールアドレス '{email}' は既に使用されています")
            return None
        
        # 管理者ユーザーを作成
        admin = User(username=username, email=email, password=password, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print(f"管理者ユーザーを作成しました: {admin.username}")
        return admin
