@echo off
echo 書籍管理アプリケーションを起動します

echo 環境変数の設定...
rem Gemini API設定（デフォルトでGemini APIを使用）
set USE_AI_FALLBACK=true
set GEMINI_API_KEY=AIzaSyBa1QVKJWaE0tmVIMeyO-1x4q6Q1-Njmdk

echo アプリケーションを起動しています...
venv\Scripts\python app.py

pause
