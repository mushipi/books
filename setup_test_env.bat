@echo off
echo テスト環境のセットアップを開始します...

rem 仮想環境アクティベーション（既存の仮想環境がある場合）
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo 仮想環境を有効化しました
) else (
    echo 警告: 仮想環境が見つかりません。グローバル環境を使用します。
)

echo 必要なライブラリをインストールしています...

rem テストに必要な最小限のライブラリ
pip install requests
pip install pillow
pip install opencv-python

echo.
echo テスト環境のセットアップが完了しました。

echo.
echo テストの実行方法:
echo.
echo 1. 単一画像のテスト:
echo    python test_book_extraction.py <画像ファイルのパス>
echo.
echo 2. フォルダ内の画像をすべてテスト:
echo    python test_folder_images.py <フォルダパス>
echo.
echo 3. Gemini API単体テスト:
echo    python test_gemini_api.py <画像ファイルのパス>
echo.

pause
