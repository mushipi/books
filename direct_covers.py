import os
import glob
import json
import webbrowser

def scan_covers():
    """表紙画像ファイルをスキャンして情報を取得する"""
    # カレントディレクトリの取得
    base_dir = os.path.abspath(os.path.dirname(__file__))
    covers_dir = os.path.join(base_dir, 'static', 'covers')
    
    print(f"表紙画像ディレクトリ: {covers_dir}")
    
    # ディレクトリの存在確認
    if not os.path.exists(covers_dir):
        print(f"エラー: 表紙画像ディレクトリが存在しません: {covers_dir}")
        return []
    
    # 画像ファイルの検索
    image_files = []
    for ext in ['jpg', 'jpeg', 'png', 'gif']:
        pattern = os.path.join(covers_dir, f"*.{ext}")
        found = glob.glob(pattern)
        print(f"  - {ext}: {len(found)}ファイル")
        image_files.extend(found)
    
    # 結果の整形
    files_info = []
    for img_path in image_files:
        filename = os.path.basename(img_path)
        isbn = os.path.splitext(filename)[0]
        
        # ファイルのサイズ
        try:
            size = os.path.getsize(img_path)
            size_str = f"{size/1024:.1f} KB"
        except:
            size = 0
            size_str = "不明"
            
        # URLエンコードされたパス
        file_url = img_path.replace('\\', '/')
        if not file_url.startswith('/'):
            file_url = '/' + file_url
            
        files_info.append({
            'filename': filename,
            'isbn': isbn,
            'path': img_path,
            'size': size,
            'size_str': size_str,
            'url': f"file://{file_url}",
        })
    
    # 結果の表示
    print(f"\n合計: {len(files_info)}ファイル\n")
    
    return files_info

def generate_html_report(files_info):
    """HTMLレポートを生成する"""
    html_header = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>表紙画像直接アクセス</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .container { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .cover-item { border: 1px solid #ccc; padding: 15px; border-radius: 5px; }
        .cover-img { max-height: 200px; max-width: 100%; display: block; margin: 10px auto; }
        .info { margin-bottom: 10px; }
        .path { font-family: monospace; background: #f5f5f5; padding: 5px; word-break: break-all; margin: 5px 0; }
        h1, h2, h3 { color: #333; }
        button { padding: 5px 10px; background: #f0f0f0; border: 1px solid #ddd; cursor: pointer; }
        button:hover { background: #e0e0e0; }
        .copy-btn { margin-left: 5px; }
        .status { color: green; display: none; }
    </style>
</head>
<body>
    <h1>表紙画像直接アクセス</h1>
    <p>表紙画像ファイル数: <strong>""" + str(len(files_info)) + """</strong> 個</p>
    
    <div class="container">
"""
    
    html_footer = """
    </div>
    
    <script>
    function copyText(elementId) {
        const element = document.getElementById(elementId);
        const text = element.textContent;
        
        navigator.clipboard.writeText(text).then(function() {
            // コピー成功
            const statusId = 'status-' + elementId;
            const status = document.getElementById(statusId);
            status.style.display = 'inline';
            setTimeout(() => {
                status.style.display = 'none';
            }, 2000);
        })
        .catch(function() {
            // エラー処理
            alert('クリップボードへのコピーに失敗しました');
        });
    }
    </script>
</body>
</html>
"""
    
    # 各ファイルの情報を追加
    html_body = ""
    for file in files_info:
        html_body += f"""
        <div class="cover-item">
            <h3>{file['filename']}</h3>
            <div class="info">ISBN: {file['isbn']}</div>
            <div class="info">サイズ: {file['size_str']}</div>
            
            <div class="path">
                絶対パス: 
                <code id="path-{file['isbn']}">{file['path']}</code>
                <button class="copy-btn" onclick="copyText('path-{file['isbn']}')">コピー</button>
                <span class="status" id="status-path-{file['isbn']}">✓</span>
            </div>
            
            <div class="path">
                ファイルURL: 
                <code id="url-{file['isbn']}">{file['url']}</code>
                <button class="copy-btn" onclick="copyText('url-{file['isbn']}')">コピー</button>
                <span class="status" id="status-url-{file['isbn']}">✓</span>
            </div>
            
            <img src="{file['url']}" alt="{file['filename']}" class="cover-img" 
                 onerror="this.onerror=null; this.src=''; this.alt='読み込みエラー'; this.style.height='100px'; this.style.border='1px dashed red';">
        </div>
        """
    
    # HTMLの組み立て
    complete_html = html_header + html_body + html_footer
    
    # HTMLファイルに保存
    output_file = 'direct_covers.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(complete_html)
    
    print(f"HTMLレポートを生成しました: {output_file}")
    return output_file

def list_cover_images():
    """表紙画像ファイルのリストを生成しJSONで保存する"""
    files_info = scan_covers()
    
    if not files_info:
        print("表紙画像ファイルが見つかりませんでした。")
        return
    
    # JSONファイルに保存
    json_file = 'cover_images.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(files_info, f, ensure_ascii=False, indent=2)
    
    print(f"JSONファイルを生成しました: {json_file}")
    
    # HTMLレポートの生成
    html_file = generate_html_report(files_info)
    
    # HTMLファイルを自動的に開く
    print("\nブラウザでHTMLレポートを開きます...")
    webbrowser.open(html_file)

if __name__ == "__main__":
    print("表紙画像ファイルのリストを生成します...\n")
    list_cover_images()
    print("\n処理が完了しました。")
