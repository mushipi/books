@echo off
echo ======================================
echo 本管理アプリケーション起動 (Gemini API 新機能付き)
echo ======================================

rem 仮想環境が有効かチェック
if not defined VIRTUAL_ENV (
    echo 仮想環境を有効化しています...
    call .\venv\Scripts\activate
)

rem Gemini APIライブラリがインストールされているか確認
python -c "import google.generativeai" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Gemini APIライブラリがインストールされていません。
    echo インストールしますか？ (Y/N)
    set /p INSTALL_API=
    if /i "%INSTALL_API%"=="Y" (
        echo Gemini APIモジュールをインストールしています...
        pip install google-generativeai
    ) else (
        echo 一括取り込み機能の高度な認識機能は制限されます。
    )
)

echo アプリケーションを起動しています...
echo.
echo ブラウザで http://localhost:5000 にアクセスしてください
echo.
python app.py

pause
