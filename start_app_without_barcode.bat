@echo off
echo ===============================================
echo 本管理アプリケーション（バーコード機能無効モード）
echo ===============================================

REM 仮想環境のアクティベート
call venv\Scripts\activate

REM バーコード機能を無効化する環境変数を設定
set DISABLE_BARCODE=true

REM アプリケーションの実行
python app.py

REM 終了時に一時停止
pause
