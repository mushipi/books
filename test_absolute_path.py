from flask import Flask
import os
import glob
from html import escape

def scan_cover_images():
    """表紙画像ファイルをスキャンして絶対パスを取得する"""
    current_dir = os.path.abspath(os.path.dirname(__file__))
    covers_dir = os.path.join(current_dir, 'static', 'covers')
    
    # 画像ファイルリストの取得
    image_files = []
    for ext in ['jpg', 'jpeg', 'png', 'gif']:
        pattern = os.path.join(covers_dir, f"*.{ext}")
        image_files.extend(glob.glob(pattern))
    
    # ファイル情報の整形
    file_info = []
    for img_path in image_files:
        filename = os.path.basename(img_path)
        isbn = os.path.splitext(filename)[0]
        size = os.path.getsize(img_path)
        file_info.append({
            'filename': filename,
            'isbn': isbn,
            'size': size,
            'absolute_path': img_path,
            'url_path': f"file://{img_path.replace('\\', '/')}",
        })
    
    return file_info

def generate_file_path_test():
    """異なるファイルパス表現のテストページを生成する"""
    files = scan_cover_images()
    
    # HTMLの生成
    html = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>絶対パス表紙テスト</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .file-item { margin-bottom: 30px; padding: 15px; border: 1px solid #ccc; }
            .path { font-family: monospace; background-color: #f5f5f5; padding: 5px; margin: 5px 0; }
            img { max-height: 200px; border: 1px solid #ddd; }
            .img-container { display: flex; gap: 20px; }
            .img-test { margin-top: 10px; padding: 10px; border: 1px solid #eee; }
            h1, h2, h3 { color: #333; }
            .success { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>表紙画像パステスト</h1>
        <p>表紙画像ファイル数: {count}個</p>
        <div id="results"></div>
    """
    
    html = html.format(count=len(files))
    
    # 各ファイルのテスト情報
    for i, file in enumerate(files):
        html += f"""
        <div class="file-item">
            <h2>{i+1}. {file['filename']}</h2>
            <div>
                <p>ISBN: {file['isbn']}</p>
                <p>サイズ: {file['size']/1024:.1f} KB</p>
                <div class="path">絶対パス: {escape(file['absolute_path'])}</div>
                <div class="path">URLパス: {escape(file['url_path'])}</div>
            </div>
            
            <h3>テスト表示</h3>
            <div class="img-container">
                <div class="img-test">
                    <p>方法1: 絶対URLパス (file://)</p>
                    <img src="{file['url_path']}" alt="{file['filename']}" onerror="this.onerror=null; this.parentElement.innerHTML += '<div class=\\'error\\'>読み込みエラー</div>'">
                </div>
                
                <div class="img-test">
                    <p>方法2: 相対パス（参考）</p>
                    <img src="static/covers/{file['filename']}" alt="{file['filename']}" onerror="this.onerror=null; this.parentElement.innerHTML += '<div class=\\'error\\'>読み込みエラー</div>'">
                </div>
            </div>
        </div>
        """
    
    html += """
    <script>
        // 画像の読み込み状態をチェック
        window.onload = function() {
            const images = document.querySelectorAll('img');
            let loadedCount = 0;
            
            images.forEach(img => {
                if (img.complete && img.naturalHeight !== 0) {
                    loadedCount++;
                    img.parentElement.innerHTML += '<div class="success">読み込み成功</div>';
                }
            });
            
            document.getElementById('results').innerHTML = 
                `<p>読み込み結果: ${loadedCount}/${images.length} 画像が正常に読み込まれました</p>`;
        }
    </script>
    </body>
    </html>
    """
    
    # HTMLファイルに保存
    with open('absolute_path_test.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"テストページを生成しました: absolute_path_test.html")
    print(f"このファイルをブラウザで開いて、表示テストを行ってください。")

if __name__ == "__main__":
    # ファイルスキャン
    files = scan_cover_images()
    
    # 結果の表示
    print(f"表紙画像ファイル数: {len(files)}個")
    for i, file in enumerate(files[:5]):  # 最初の5件のみ表示
        print(f"{i+1}. {file['filename']} - {file['absolute_path']}")
    
    if len(files) > 5:
        print(f"... 他 {len(files)-5} ファイル")
    
    # テストページの生成
    generate_file_path_test()
