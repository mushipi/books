@echo off
echo ライブラリの依存関係を修正しています...

echo 1. NumPyのアンインストール
pip uninstall -y numpy

echo 2. NumPy 1.26.0のインストール
pip install numpy==1.26.0

echo 3. OpenCVのアンインストール
pip uninstall -y opencv-python

echo 4. OpenCV 4.7.0.72のインストール
pip install opencv-python==4.7.0.72

echo 5. Pillowのインストール
pip install "pillow>=10.0.0"

echo 6. pyzbarのインストール
pip install pyzbar

echo 7. pytesseractのインストール
pip install pytesseract

echo 8. requestsのインストール
pip install requests

echo 注意: Tesseract OCRエンジン本体のインストールが必要です。
echo https://github.com/UB-Mannheim/tesseract/wiki からインストールしてください。

echo 依存関係の修正が完了しました。
echo アプリケーションを起動するには、以下のコマンドを実行してください:
echo python app.py
pause
