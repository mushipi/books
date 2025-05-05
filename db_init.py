"""
データベース初期化スクリプト
初回実行時にデータベースを作成し、初期データを登録します
"""

import os
import sys
import argparse

# バーコード機能を無効化する環境変数を設定
os.environ['DISABLE_BARCODE'] = 'true'

# アプリ作成前にバーコードコントローラのインポートを回避
sys.modules['controllers.barcode_controller'] = object()

from models.book import db
from models.genre import Genre
from models.tag import Tag
from models.location import Location
from models.users.user import User
from app import create_app

# アプリケーションのコンテキストを作成
app = create_app()

def init_db():
    """データベースを初期化する"""
    with app.app_context():
        # インスタンスディレクトリの確認
        instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
        try:
            os.makedirs(instance_path, exist_ok=True)
            print(f"インスタンスディレクトリを作成しました: {instance_path}")
        except OSError as e:
            print(f"インスタンスディレクトリの作成に失敗しました: {e}")
        
        # データベースの作成
        db.create_all()
        print("データベースの初期化が完了しました")

def seed_db():
    """初期データを投入する"""
    with app.app_context():
        # ジャンル
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
        
        # 収納場所
        locations = [
            Location(name="本棚A - 上段", description="リビングの大きい本棚"),
            Location(name="本棚A - 中段", description="リビングの大きい本棚"),
            Location(name="本棚A - 下段", description="リビングの大きい本棚"),
            Location(name="本棚B", description="書斎の本棚"),
            Location(name="収納ボックス", description="クローゼット内の箱")
        ]
        
        for location in locations:
            existing = Location.query.filter_by(name=location.name).first()
            if not existing:
                db.session.add(location)
        
        # タグ
        tags = [
            Tag(name="お気に入り"),
            Tag(name="未読"),
            Tag(name="貸出中"),
            Tag(name="読書中"),
            Tag(name="読了"),
            Tag(name="重要"),
            Tag(name="参考資料")
        ]
        
        for tag in tags:
            existing = Tag.query.filter_by(name=tag.name).first()
            if not existing:
                db.session.add(tag)
        
        # ユーザー
        users = [
            User(username="admin", email="admin@example.com", password="password", is_admin=True),
            User(username="user1", email="user1@example.com", password="password")
        ]
        
        for user in users:
            existing = User.query.filter_by(username=user.username).first()
            if not existing:
                db.session.add(user)
        
        # 変更をコミット
        db.session.commit()
        print("初期データの投入が完了しました")

def parse_args():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description='データベース初期化ユーティリティ')
    parser.add_argument('--init', action='store_true', help='データベースの初期化')
    parser.add_argument('--seed', action='store_true', help='初期データの投入')
    parser.add_argument('--init-with-seed', action='store_true', help='データベースの初期化と初期データの投入')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # コマンドライン引数がある場合はそれに従って処理
    if args.init_with_seed:
        init_db()
        seed_db()
    elif args.init:
        init_db()
    elif args.seed:
        seed_db()
    else:
        # 引数がない場合は対話モードで実行
        print("=" * 50)
        print("データベース管理ユーティリティ")
        print("=" * 50)
        print("1: データベースの初期化")
        print("2: 初期データの投入")
        print("3: 両方実行（初期化+初期データ投入）")
        print("=" * 50)
        
        choice = input("操作を選択してください (1-3): ")
        
        if choice == "1":
            init_db()
        elif choice == "2":
            seed_db()
        elif choice == "3":
            init_db()
            seed_db()
        else:
            print("無効な選択です。プログラムを終了します。")
