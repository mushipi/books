@echo off
chcp 65001 > nul
echo ===============================================
echo Gemini API テスト実行スクリプト
echo ===============================================

if "%~1"=="" (
  echo 使用方法: run_api_tests.bat [画像ファイルパス]
  echo 例: run_api_tests.bat test_images\book1.jpg
  exit /b
)

echo 仮想環境を有効化します...
call venv\Scripts\activate

echo ===============================================
echo 1. 現在のAPI実装（リクエスト直接送信）でのテスト
echo ===============================================
python test_gemini_api_current.py %1

echo ===============================================
echo 2. google-generativeaiライブラリを使用したテスト
echo ===============================================
echo ライブラリをインストールしています...
pip install google-generativeai -q

python test_gemini_api_new.py %1

echo ===============================================
echo テスト完了
echo ===============================================

pause
