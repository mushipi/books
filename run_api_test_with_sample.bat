@echo off
echo ===============================================
echo Gemini API テスト実行スクリプト
echo ===============================================

set TEST_IMAGE="pic\bunkobon-urabyousi_2-1024x683.jpg"

echo 使用する画像: %TEST_IMAGE%

if not exist venv\Scripts\activate (
    echo 仮想環境が見つかりません
    pause
    exit /b
)

call venv\Scripts\activate

echo ===============================================
echo 1. 現在のAPI実装（リクエスト直接送信）でのテスト
echo ===============================================
python test_gemini_api_current.py %TEST_IMAGE%

echo ===============================================
echo 2. google-generativeaiライブラリを使用したテスト
echo ===============================================
echo ライブラリをインストールしています...
pip install google-generativeai -q

python test_gemini_api_new.py %TEST_IMAGE%

echo ===============================================
echo テスト完了
echo ===============================================

pause
