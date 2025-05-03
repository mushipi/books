@echo off
echo ======================================
echo Gemini API モジュールのインストール
echo ======================================

rem 仮想環境が有効かチェック
if not defined VIRTUAL_ENV (
    echo 仮想環境が有効になっていません。venvを有効化してください。
    echo 例: .\venv\Scripts\activate
    exit /b 1
)

echo Gemini API モジュールをインストールしています...
pip install google-generativeai

if %ERRORLEVEL% EQU 0 (
    echo.
    echo インストールが完了しました。
    echo これで一括取り込み機能の高度な認識機能が利用可能になりました。
) else (
    echo.
    echo インストール中にエラーが発生しました。
    echo 仮想環境が有効になっていることを確認してください。
)

echo.
pause
