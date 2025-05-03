@echo off
echo ===============================================
echo データベース初期化ユーティリティ
echo ===============================================

REM 仮想環境のアクティベート
call venv\Scripts\activate

REM バーコード機能を無効化する環境変数を設定
set DISABLE_BARCODE=true

REM インスタンスディレクトリの作成（存在確認付き）
if not exist instance mkdir instance

REM データベースの初期化
python db_init.py

echo.
echo ===============================================
echo 初期化が完了しました
echo ===============================================

pause
