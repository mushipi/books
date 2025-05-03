@echo off
chcp 65001 > nul
echo ===============================================
echo ライブラリの依存関係を修正しています...
echo ===============================================

echo 1. NumPyのアンインストール
pip uninstall -y numpy

echo 2. NumPy 1.26.0のインストール
pip install numpy==1.26.0

echo 3. OpenCVのアンインストール
pip uninstall -y opencv-python

echo 4. OpenCV 4.7.0.72のインストール
pip install opencv-python==4.7.0.72

echo 5. pyzbarの確認とインストール
pip show pyzbar > nul 2>&1
if %errorlevel% neq 0 (
    echo pyzbarをインストールします...
    pip install pyzbar==0.1.9
) else (
    echo pyzbarは既にインストールされています。
)

echo 6. Pillowのインストール
pip install pillow>=10.0.0

echo ===============================================
echo 依存関係の修正が完了しました。
echo アプリケーションを起動するには、以下のコマンドを実行してください:
echo python app.py
echo ===============================================

pause
