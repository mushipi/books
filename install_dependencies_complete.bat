@echo off
echo ======================================
echo 本管理アプリケーション 依存ライブラリ一括インストール
echo ======================================

rem 仮想環境が有効かチェック
if not defined VIRTUAL_ENV (
    echo 仮想環境を有効化しています...
    call .\venv\Scripts\activate
    
    if %ERRORLEVEL% NEQ 0 (
        echo 仮想環境が見つかりません。新規作成します...
        python -m venv venv
        call .\venv\Scripts\activate
    )
)

echo Flaskと基本ライブラリをインストールしています...
pip install flask==2.0.1 flask-sqlalchemy==2.5.1 werkzeug==2.0.1 jinja2==3.0.1

echo Web APIライブラリをインストールしています...
pip install requests==2.28.1

rem Python 3.12環境では事前ビルド済みのPillowを使用
echo 画像処理ライブラリをインストールしています...
pip install pillow

rem OpenCVとNumpyをインストール（バージョン指定）
echo OpenCVをインストールしています...
pip install opencv-python==4.7.0.72

rem バーコードスキャンライブラリをインストール
echo バーコード認識ライブラリをインストールしています...
pip install pyzbar

rem Gemini APIをインストール
echo Gemini APIライブラリをインストールしています...
pip install google-generativeai

echo.
echo インストールされたライブラリのバージョン:
pip list | findstr "flask flask-sqlalchemy werkzeug jinja2 pillow opencv-python numpy pyzbar google-generativeai requests"

echo.
echo 依存ライブラリのインストールが完了しました。
echo アプリケーションを起動するには start_app_gemini_new.bat を実行してください。
echo.
pause
