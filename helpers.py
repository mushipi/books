import os
from flask import url_for
import glob

def get_cover_url(cover_path):
    """
    表紙画像のURLを生成する
    
    Args:
        cover_path: データベースに保存されている表紙画像パス
        
    Returns:
        str: 表紙画像のURL、または画像がない場合はNone
    """
    if not cover_path:
        return None
    
    # パスの正規化
    cover_path = normalize_cover_path(cover_path)
    
    # ファイルの存在確認
    static_path = os.path.join('static', cover_path)
    if not os.path.isfile(static_path):
        print(f"警告: 表紙画像ファイルが存在しません: {static_path}")
        return None
    
    # ファイル名のみを抽出
    filename = os.path.basename(cover_path)
    
    # 直接アクセス用のURLを生成
    return f"/direct-cover/{filename}"

def cover_image_exists(cover_path):
    """
    表紙画像が実際に存在するか確認する
    
    Args:
        cover_path: データベースに保存されている表紙画像パス
        
    Returns:
        bool: 画像が存在する場合はTrue、存在しない場合はFalse
    """
    if not cover_path:
        return False
    
    # パスの正規化
    cover_path = normalize_cover_path(cover_path)
    
    # ファイルの存在確認
    static_path = os.path.join('static', cover_path)
    return os.path.isfile(static_path)

def find_cover_by_isbn(isbn, static_folder='static'):
    """
    ISBNに基づいて表紙画像ファイルを検索する
    
    Args:
        isbn: 書籍のISBN
        static_folder: 静的ファイルフォルダ
        
    Returns:
        str: 表紙画像の相対パス、見つからない場合はNone
    """
    if not isbn:
        return None
    
    # ISBNからハイフンを除去
    clean_isbn = isbn.replace('-', '')
    
    # 表紙ディレクトリのパス
    covers_dir = os.path.join(static_folder, 'covers')
    
    # 各拡張子でファイルを検索
    for ext in ['jpg', 'jpeg', 'png', 'gif']:
        img_path = os.path.join(covers_dir, f"{clean_isbn}.{ext}")
        if os.path.isfile(img_path):
            # 相対パスを返す
            return os.path.join('covers', f"{clean_isbn}.{ext}")
    
    # 見つからなかった場合
    return None

def normalize_cover_path(cover_path):
    """
    表紙画像のパスを正規化する
    
    Args:
        cover_path: データベースに保存されている表紙画像パス
        
    Returns:
        str: 正規化されたパス
    """
    if not cover_path:
        return None
    
    # パスが "/static/" で始まる場合は除去
    if cover_path.startswith('/static/'):
        cover_path = cover_path[8:]
    # パスが "static/" で始まる場合は除去
    elif cover_path.startswith('static/'):
        cover_path = cover_path[7:]
    
    return cover_path

def get_absolute_cover_path(cover_path):
    """
    ファイルシステム上の表紙画像の絶対パスを生成する
    
    Args:
        cover_path: データベースに保存されている表紙画像パス
        
    Returns:
        str: 絶対パス、または画像がない場合はNone
    """
    if not cover_path:
        return None
    
    # パスの正規化
    cover_path = normalize_cover_path(cover_path)
    
    # ファイルの絶対パスを生成
    # カレントディレクトリの絶対パスを取得
    base_dir = os.path.abspath(os.path.dirname(__file__))
    abs_path = os.path.join(base_dir, 'static', cover_path)
    
    # ファイルの存在確認
    if not os.path.isfile(abs_path):
        print(f"警告: 表紙画像ファイルが存在しません: {abs_path}")
        return None
    
    return abs_path
