@echo off
echo ===============================================
echo 本管理アプリケーション - 完全セットアップ版
echo ===============================================

REM 仮想環境のアクティベート
call venv\Scripts\activate

REM バーコード機能を無効化する環境変数を設定
set DISABLE_BARCODE=true

REM インスタンスディレクトリの作成（存在確認付き）
if not exist instance (
    echo インスタンスディレクトリを作成しています...
    mkdir instance
    echo 作成完了!
) else (
    echo インスタンスディレクトリは既に存在します。
)

REM データベースの存在確認
if not exist instance\books.db (
    echo データベースが存在しません。初期化を行います...

    REM 初期化メニューを表示
    echo.
    echo =============================================
    echo データベース初期化オプション:
    echo =============================================
    echo 1: データベーススキーマのみ作成
    echo 2: データベーススキーマ作成 + 初期データ投入
    echo =============================================
    echo.
    
    REM ユーザー入力の取得
    set /p option="オプションを選択してください (1-2): "
    
    REM 選択に応じた処理
    if "%option%"=="1" (
        python -c "from db_init import init_db; init_db()"
        echo データベーススキーマを作成しました。
    ) else if "%option%"=="2" (
        python -c "from db_init import init_db, seed_db; init_db(); seed_db()"
        echo データベーススキーマを作成し、初期データを投入しました。
    ) else (
        echo 無効な選択です。デフォルトでデータベーススキーマのみ作成します。
        python -c "from db_init import init_db; init_db()"
    )
) else (
    echo データベースは既に存在します。
)

REM 権限の確認と修正（Windows環境向け）
echo データベースとインスタンスディレクトリの権限を確認しています...
icacls instance /grant Everyone:(OI)(CI)F /T

REM アプリケーションの実行
echo.
echo アプリケーションを起動しています...
echo ブラウザで http://localhost:5000 にアクセスしてください。
echo Ctrl+C で終了できます。
echo.
python app.py

REM 終了時に一時停止
pause
