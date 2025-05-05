from flask import Flask, send_from_directory, render_template
import os
import glob
import json

app = Flask(__name__)

# 絶対パスで直接画像ファイルを提供
@app.route('/absolute-cover/<path:filename>')
def absolute_cover(filename):
    """絶対パスで表紙画像ファイルを提供する"""
    covers_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'covers')
    print(f"絶対パスでのアクセス: {os.path.join(covers_dir, filename)}")
    return send_from_directory(covers_dir, filename)

# リスト表示用のルート
@app.route('/')
def index():
    """利用可能な表紙画像の一覧を表示する"""
    covers_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'covers')
    
    # 画像ファイルを検索
    image_files = []
    for ext in ['jpg', 'jpeg', 'png', 'gif']:
        image_files.extend(glob.glob(os.path.join(covers_dir, f"*.{ext}")))
    
    # HTMLを生成
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>絶対パス画像テスト</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .cover-item { margin-bottom: 20px; padding: 10px; border: 1px solid #ccc; }
            img { max-height: 300px; border: 1px solid #ddd; }
            .path { font-family: monospace; background-color: #f5f5f5; padding: 5px; }
        </style>
    </head>
    <body>
        <h1>表紙画像テスト（絶対パス）</h1>
        <p>利用可能な画像ファイル数: {count}</p>
    """
    
    html = html.format(count=len(image_files))
    
    # 各画像の情報とリンク
    for i, img_path in enumerate(image_files):
        filename = os.path.basename(img_path)
        file_size = os.path.getsize(img_path)
        
        # 絶対パスリンク
        abs_url = f"/absolute-cover/{filename}"
        
        html += f"""
        <div class="cover-item">
            <h3>画像 {i+1}: {filename}</h3>
            <p>サイズ: {file_size/1024:.1f} KB</p>
            <p>URL: <span class="path">{abs_url}</span></p>
            <div>
                <img src="{abs_url}" alt="{filename}">
            </div>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    return html

# API形式で画像リストを提供
@app.route('/api/covers')
def list_covers():
    """画像ファイルの一覧をJSON形式で返す"""
    covers_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'covers')
    
    # 画像ファイルを検索
    image_files = []
    for ext in ['jpg', 'jpeg', 'png', 'gif']:
        image_files.extend(glob.glob(os.path.join(covers_dir, f"*.{ext}")))
    
    # 結果を整形
    result = []
    for img_path in image_files:
        filename = os.path.basename(img_path)
        result.append({
            'filename': filename,
            'size': os.path.getsize(img_path),
            'absolute_url': f"/absolute-cover/{filename}"
        })
    
    return json.dumps(result)

if __name__ == "__main__":
    # 設定の出力
    print("絶対パス表紙画像サーバーを起動します...")
    covers_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'covers')
    print(f"表紙画像ディレクトリ: {covers_dir}")
    
    # 画像ファイル数の確認
    image_count = 0
    for ext in ['jpg', 'jpeg', 'png', 'gif']:
        pattern = os.path.join(covers_dir, f"*.{ext}")
        count = len(glob.glob(pattern))
        print(f"  - {ext}: {count}ファイル")
        image_count += count
    
    print(f"合計: {image_count}ファイル")
    print("")
    
    # サーバーの起動
    print("サーバーを起動しています...")
    print("アクセス: http://localhost:5555/")
    app.run(debug=True, port=5555)
