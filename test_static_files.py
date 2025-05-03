from flask import Flask, send_from_directory
import os

# テスト用アプリの作成
app = Flask(__name__)

# 静的ファイルの直接サービング用ルート
@app.route('/test-static/<path:filename>')
def test_static(filename):
    """静的ファイルのテスト表示"""
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_folder, filename)

@app.route('/')
def index():
    """テストページ"""
    # 存在するすべての画像ファイルを表示するHTMLを生成
    covers_dir = os.path.join(os.path.dirname(__file__), 'static', 'covers')
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>静的ファイルテスト</title>
        <style>
            .cover-image {
                max-width: 200px;
                max-height: 300px;
                margin: 10px;
                border: 1px solid #ccc;
            }
            .image-container {
                display: inline-block;
                margin: 10px;
                padding: 10px;
                border: 1px solid #eee;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>静的ファイルのテスト</h1>
    """
    
    if os.path.exists(covers_dir):
        html += "<h2>静的ファイルの直接表示</h2>"
        html += "<div>"
        
        files = os.listdir(covers_dir)
        for filename in files:
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                filepath = os.path.join('covers', filename)
                html += f"""
                <div class="image-container">
                    <p>ファイル: {filename}</p>
                    <p>url_for方式:</p>
                    <img src="/static/{filepath}" class="cover-image">
                    <p>直接アクセス方式:</p>
                    <img src="/test-static/{filepath}" class="cover-image">
                </div>
                """
        
        html += "</div>"
    else:
        html += "<p>coversディレクトリが見つかりません</p>"
    
    html += "</body></html>"
    return html

if __name__ == '__main__':
    # アプリケーションの実行
    host = '0.0.0.0'
    port = 5001  # デフォルトとは別のポートを使用
    
    print("="*50)
    print(f"静的ファイルのテストサーバーを起動します: http://{host}:{port}/")
    print("="*50)
    
    app.run(host=host, port=port, debug=True)
