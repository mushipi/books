@echo off
chcp 65001
echo 仮想環境をセットアップします...

:: 仮想環境の作成
python -m venv venv

:: 仮想環境のアクティベート
call venv\Scripts\activate.bat

:: 必要なパッケージのインストール
pip install Flask==2.2.3
pip install Flask-SQLAlchemy==3.0.3
pip install Werkzeug==2.2.3
pip install pyzbar==0.1.9
pip install opencv-python==4.7.0.72
pip install requests==2.28.2
pip install Pillow==9.4.0
pip install gunicorn==20.1.0

echo 依存関係のインストールが完了しました。
echo 仮想環境をアクティベートするには次のコマンドを実行してください：
echo call venv\Scripts\activate.bat

pause
