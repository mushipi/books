@echo off
echo ===============================================
echo 本管理アプリケーション - 設定修正版
echo ===============================================

REM 仮想環境のアクティベート
call venv\Scripts\activate

REM SQLAlchemyの設定を環境変数として設定
set SQLALCHEMY_DATABASE_URI=sqlite:///instance/books.db
set SQLALCHEMY_TRACK_MODIFICATIONS=False

REM インスタンスディレクトリの作成
mkdir instance

REM データベースファイルの存在確認
IF NOT EXIST instance\books.db (
    echo データベースを初期化しています...
    python db_init.py
)

REM アプリケーションの実行
echo アプリケーションを起動しています...
python app.py

REM 終了時に一時停止
pause
