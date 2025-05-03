import os
import sqlite3

def fix_cover_paths():
    """データベース内の表紙画像パスを修正する"""
    # データベースファイルのパス
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'books.db')
    
    print(f"データベースに接続: {db_path}")
    
    # SQLiteデータベースに接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 書籍テーブルからカバー画像のあるレコードを取得
        cursor.execute("SELECT id, title, isbn, cover_image_path FROM book WHERE cover_image_path IS NOT NULL")
        books = cursor.fetchall()
        
        print(f"カバー画像のある書籍: {len(books)}冊")
        
        updated_count = 0
        
        # 各書籍のカバー画像パスを確認・修正
        for book_id, title, isbn, cover_path in books:
            print(f"\n書籍ID: {book_id}")
            print(f"タイトル: {title}")
            print(f"ISBN: {isbn}")
            print(f"現在のパス: {cover_path}")
            
            # ISBNをクリーニング
            if isbn:
                clean_isbn = isbn.replace("-", "")
                
                # 修正するパス形式を設定 - パス区切り文字をスラッシュに統一
                expected_rel_path = f"covers/{clean_isbn}.jpg"
                
                # 物理ファイルの存在チェック
                static_file_path = os.path.join('static', 'covers', f"{clean_isbn}.jpg")
                
                if os.path.exists(static_file_path):
                    print(f"画像ファイルが存在します: {static_file_path}")
                    
                    # パスが正しくない場合は修正
                    if cover_path != expected_rel_path:
                        print(f"パスを修正します: {cover_path} -> {expected_rel_path}")
                        
                        # データベースを更新
                        cursor.execute(
                            "UPDATE book SET cover_image_path = ? WHERE id = ?",
                            (expected_rel_path, book_id)
                        )
                        updated_count += 1
                    else:
                        print("パスは正しいフォーマットです")
                        
                # 画像ファイルがcovers直下に存在しない場合は、別のパスパターンを試す
                elif os.path.exists(os.path.join('static', cover_path)):
                    print(f"画像ファイルが別の場所に存在します: static/{cover_path}")
                    
                    # 今のパスが正常に動作している場合はそのままに
                    print("既存のパスを維持します")
                else:
                    print(f"警告: 画像ファイルが見つかりません: {static_file_path}")
                    
                    # 正しいISBN命名規則でファイルを探す
                    possible_files = []
                    covers_folder = os.path.join('static', 'covers')
                    
                    if os.path.exists(covers_folder):
                        for file in os.listdir(covers_folder):
                            if file.startswith(clean_isbn):
                                possible_files.append(file)
                    
                    if possible_files:
                        print(f"ISBNに一致するファイルを発見: {possible_files}")
                        new_path = f"covers/{possible_files[0]}"
                        print(f"パスを修正します: {cover_path} -> {new_path}")
                        
                        cursor.execute(
                            "UPDATE book SET cover_image_path = ? WHERE id = ?",
                            (new_path, book_id)
                        )
                        updated_count += 1
                    else:
                        print("一致するファイルが見つからないため、パスをクリアします")
                        
                        cursor.execute(
                            "UPDATE book SET cover_image_path = NULL WHERE id = ?",
                            (book_id,)
                        )
                        updated_count += 1
        
        # 変更をコミット
        if updated_count > 0:
            conn.commit()
            print(f"\n{updated_count}冊の書籍のパスを修正しました")
        else:
            print("\n修正が必要な書籍はありませんでした")
        
        # 全ての書籍のカバー画像パスを確認
        cursor.execute("SELECT id, title, isbn, cover_image_path FROM book WHERE cover_image_path IS NOT NULL")
        updated_books = cursor.fetchall()
        
        print("\n修正後のパス一覧:")
        for book_id, title, isbn, cover_path in updated_books:
            print(f"{book_id}: {title} - {cover_path}")
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        conn.rollback()
    
    finally:
        # 接続を閉じる
        conn.close()

if __name__ == '__main__':
    fix_cover_paths()
    print("\n実行完了！")
