from flask import Flask, send_from_directory
import os
import glob

app = Flask(__name__)

# 静的ファイルの設定
app.static_folder = 'static'
app.static_url_path = ''

@app.route('/')
def index():
    # coversディレクトリ内の画像ファイルを一覧表示
    covers_dir = os.path.join(app.static_folder, 'covers')
    image_files = []
    
    for ext in ['jpg', 'jpeg', 'png', 'gif']:
        image_files.extend(glob.glob(os.path.join(covers_dir, f"*.{ext}")))
    
    html = '<html><body><h1>表紙画像テスト</h1>'
    
    # 各画像へのリンクと表示
    for i, img_path in enumerate(image_files):
        filename = os.path.basename(img_path)
        rel_path = os.path.join('covers', filename)
        
        html += f'''
        <div style="margin: 20px; padding: 10px; border: 1px solid #ccc;">
            <h3>画像 {i+1}: {filename}</h3>
            <p>パス1: <code>/static/{rel_path}</code></p>
            <p>パス2: <code>/{rel_path}</code></p>
            <p>パス3: <code>/covers/{filename}</code></p>
            
            <div style="display: flex; flex-wrap: wrap;">
                <div style="margin: 10px;">
                    <h4>方法1: static_url</h4>
                    <img src="/static/{rel_path}" style="max-height: 200px; border: 1px solid blue;">
                </div>
                
                <div style="margin: 10px;">
                    <h4>方法2: ルートパス</h4>
                    <img src="/{rel_path}" style="max-height: 200px; border: 1px solid green;">
                </div>
                
                <div style="margin: 10px;">
                    <h4>方法3: カスタムルート</h4>
                    <img src="/covers/{filename}" style="max-height: 200px; border: 1px solid red;">
                </div>
            </div>
        </div>
        '''
    
    html += '</body></html>'
    return html

# カスタム静的ファイルルート
@app.route('/covers/<path:filename>')
def custom_static(filename):
    """coversディレクトリのファイルを直接提供する"""
    return send_from_directory(os.path.join(app.static_folder, 'covers'), filename)

if __name__ == '__main__':
    print(f"静的ファイルフォルダ: {app.static_folder}")
    print(f"静的ファイルURLパス: {app.static_url_path}")
    
    covers_dir = os.path.join(app.static_folder, 'covers')
    if os.path.exists(covers_dir):
        print(f"covers ディレクトリが見つかりました: {covers_dir}")
        files = os.listdir(covers_dir)
        print(f"covers ディレクトリ内のファイル数: {len(files)}")
        if files:
            print("最初の10ファイル:")
            for f in files[:10]:
                print(f" - {f}")
    else:
        print(f"covers ディレクトリが見つかりません: {covers_dir}")
    
    # アプリの実行
    app.run(debug=True, port=5050)
