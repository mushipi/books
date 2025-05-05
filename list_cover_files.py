import os
import glob

def list_cover_files():
    """表紙画像ディレクトリをスキャンして内容を一覧表示"""
    covers_dir = os.path.join("static", "covers")
    
    print("\n📂 表紙画像ディレクトリの内容を表示します")
    
    # ディレクトリが存在するか確認
    if not os.path.exists(covers_dir):
        print(f"❌ ディレクトリが見つかりません: {covers_dir}")
        return
    
    # ファイル一覧を取得
    files = []
    for ext in ["jpg", "jpeg", "png", "gif"]:
        pattern = os.path.join(covers_dir, f"*.{ext}")
        files.extend(glob.glob(pattern))
    
    # 結果表示
    if files:
        print(f"✅ {len(files)}個の画像ファイルが見つかりました\n")
        files.sort()  # アルファベット順にソート
        
        print(f"{'ファイル名':<20} {'サイズ':<10} {'パス':<50}")
        print("-" * 80)
        
        for file_path in files:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            size_str = f"{file_size/1024:.1f} KB" if file_size >= 1024 else f"{file_size} B"
            rel_path = os.path.join("covers", filename)
            
            print(f"{filename:<20} {size_str:<10} {rel_path:<50}")
    else:
        print("❌ 画像ファイルが見つかりませんでした")

if __name__ == "__main__":
    list_cover_files()
    print("\n実行完了！")
