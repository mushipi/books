import os
import glob
import webbrowser

def generate_direct_file_paths():
    """表紙画像ファイルへの直接ファイルパスを含むHTMLを生成する"""
    # カレントディレクトリの絶対パス
    base_dir = os.path.abspath(os.path.dirname(__file__))
    covers_dir = os.path.join(base_dir, 'static', 'covers')
    
    # 画像ファイルのリストを取得
    image_files = []
    for ext in ['jpg', 'jpeg', 'png', 'gif']:
        pattern = os.path.join(covers_dir, f"*.{ext}")
        image_files.extend(glob.glob(pattern))
    
    # HTMLを生成
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>表紙画像 - 静的ファイルパス</title>
        <style>
            body { font-family: sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .image-container { display: flex; flex-wrap: wrap; gap: 20px; }
            .image-item { border: 1px solid #ccc; padding: 10px; width: 350px; margin-bottom: 20px; }
            img { max-width: 100%; max-height: 250px; display: block; margin: 0 auto; }
            .file-path { font-family: monospace; word-break: break-all; background: #f5f5f5; padding: 5px; margin: 5px 0; }
            h2 { margin-top: 10px; font-size: 16px; }
            .error { color: red; font-weight: bold; }
            .success { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>表紙画像ファイルへの直接アクセス</h1>
        <p>ファイル数: <b>%d</b> 個</p>
        
        <div>
            <h2>表示方法</h2>
            <ol>
                <li>file:// プロトコル - Windowsのファイルシステムへの直接アクセス</li>
                <li>img タグのsrc属性に直接ファイルパスを指定</li>
            </ol>
        </div>
        
        <div class="image-container">
    """ % len(image_files)
    
    # 各画像の情報を追加
    for img_path in image_files:
        filename = os.path.basename(img_path)
        file_url = img_path.replace('\\', '/')
        
        # Windows形式のパス
        windows_path = img_path
        
        # URLプロトコル形式
        if not file_url.startswith('/'):
            file_url = '/' + file_url
        url_path = f"file://{file_url}"
        
        html += f"""
        <div class="image-item">
            <h2>{filename}</h2>
            
            <div class="file-path">
                Windows: {windows_path}
            </div>
            
            <div class="file-path">
                URL: {url_path}
            </div>
            
            <div>
                <h3>方法1: file://プロトコル</h3>
                <img src="{url_path}" alt="{filename}" 
                     onerror="this.nextElementSibling.style.display='block'; this.style.display='none';">
                <div class="error" style="display:none;">読み込みエラー</div>
            </div>
            
            <div>
                <h3>方法2: 直接パス</h3>
                <img src="{windows_path}" alt="{filename}"
                     onerror="this.nextElementSibling.style.display='block'; this.style.display='none';">
                <div class="error" style="display:none;">読み込みエラー</div>
            </div>
        </div>
        """
    
    # HTMLを完成させる
    html += """
        </div>
        
        <script>
            // 画像の読み込み状態を確認
            window.onload = function() {
                const images = document.querySelectorAll('img');
                let successCount = 0;
                let failureCount = 0;
                
                images.forEach(img => {
                    if (img.complete && img.naturalWidth !== 0) {
                        successCount++;
                    } else {
                        failureCount++;
                    }
                });
                
                // 結果を表示
                const resultElement = document.createElement('p');
                resultElement.innerHTML = `読み込み結果: <span class="success">${successCount}</span> 成功, <span class="error">${failureCount}</span> 失敗`;
                document.body.insertBefore(resultElement, document.querySelector('.image-container'));
            }
        </script>
    </body>
    </html>
    """
    
    # HTMLファイルに保存
    output_file = 'static_file_paths.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTMLファイルを生成しました: {output_file}")
    
    # ブラウザでHTMLファイルを開く
    webbrowser.open(output_file)
    print("ブラウザでHTMLファイルを開きました。")

if __name__ == "__main__":
    print("表紙画像ファイルパステストを実行します...")
    generate_direct_file_paths()
    print("処理が完了しました。")
