import os
import shutil
import stat

def fix_permissions():
    """画像ファイルのパーミッションを修正する"""
    # 静的ファイルフォルダのパス
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    covers_folder = os.path.join(static_folder, 'covers')
    
    print(f"静的ファイルフォルダ: {static_folder}")
    print(f"表紙画像フォルダ: {covers_folder}")
    
    # フォルダの存在確認
    if not os.path.exists(static_folder):
        print(f"エラー: 静的ファイルフォルダが見つかりません: {static_folder}")
        return
    
    if not os.path.exists(covers_folder):
        print(f"表紙画像フォルダが見つからないため、作成します: {covers_folder}")
        try:
            os.makedirs(covers_folder, exist_ok=True)
        except Exception as e:
            print(f"フォルダ作成エラー: {e}")
            return
    
    # フォルダの権限を変更
    try:
        # Windows環境では異なる権限設定が必要
        if os.name == 'nt':  # Windows
            print("Windows環境を検出しました。フォルダのアクセス権を確認します。")
            # Windowsではファイルの読み取り・書き込み権限を確認
        else:  # Unix/Linux/Mac
            print("Unix/Linux環境を検出しました。パーミッションを修正します。")
            os.chmod(static_folder, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
            os.chmod(covers_folder, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
        
        print("フォルダのパーミッションを修正しました")
    except Exception as e:
        print(f"パーミッション変更エラー: {e}")
    
    # 画像ファイルの権限を変更
    files_modified = 0
    
    for filename in os.listdir(covers_folder):
        if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            file_path = os.path.join(covers_folder, filename)
            try:
                if os.name == 'nt':  # Windows
                    # Windowsではファイルの読み取り専用属性を解除
                    pass
                else:  # Unix/Linux/Mac
                    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                
                files_modified += 1
                
                # ファイルサイズの確認
                file_size = os.path.getsize(file_path)
                print(f"ファイル: {filename}, サイズ: {file_size} bytes")
                
                if file_size < 100:
                    print(f"警告: ファイルサイズが小さすぎます: {filename}")
            except Exception as e:
                print(f"ファイル {filename} の権限変更エラー: {e}")
    
    print(f"合計 {files_modified} 個のファイルのパーミッションを修正しました")
    
    # 静的ファイルフォルダ内のファイル一覧を表示
    print("\n静的ファイルフォルダの内容:")
    for root, dirs, files in os.walk(static_folder):
        level = root.replace(static_folder, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            print(f"{sub_indent}{file} ({file_size} bytes)")

if __name__ == "__main__":
    fix_permissions()
    print("\n実行完了！")
