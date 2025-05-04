from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from models.book import db, Book
from models.genre import Genre
from models.tag import Tag
from models.location import Location
from datetime import datetime
import os

book_bp = Blueprint('books', __name__, url_prefix='/books')

@book_bp.route('/')
def index():
    """書籍一覧ページ"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    # 検索・フィルター条件の取得
    search_query = request.args.get('search', '')
    genre_id = request.args.get('genre', None, type=int)
    tag_id = request.args.get('tag', None, type=int)
    location_id = request.args.get('location', None, type=int)
    sort_by = request.args.get('sort', 'added_date')
    sort_order = request.args.get('order', 'desc')
    
    # クエリの構築
    query = Book.query
    
    # 検索条件の適用
    if search_query:
        query = query.filter(
            (Book.title.contains(search_query)) |
            (Book.author.contains(search_query)) |
            (Book.publisher.contains(search_query))
        )
    
    # ジャンルフィルター
    if genre_id:
        genre = Genre.query.get(genre_id)
        if genre:
            query = query.filter(Book.genres.contains(genre))
    
    # タグフィルター
    if tag_id:
        tag = Tag.query.get(tag_id)
        if tag:
            query = query.filter(Book.tags.contains(tag))
    
    # 収納場所フィルター
    if location_id:
        query = query.filter_by(location_id=location_id)
    
    # ソート順の適用
    if sort_by == 'title':
        if sort_order == 'asc':
            query = query.order_by(Book.title.asc())
        else:
            query = query.order_by(Book.title.desc())
    elif sort_by == 'author':
        if sort_order == 'asc':
            query = query.order_by(Book.author.asc())
        else:
            query = query.order_by(Book.author.desc())
    elif sort_by == 'published_date':
        if sort_order == 'asc':
            query = query.order_by(Book.published_date.asc())
        else:
            query = query.order_by(Book.published_date.desc())
    else:  # デフォルトは追加日順
        if sort_order == 'asc':
            query = query.order_by(Book.added_date.asc())
        else:
            query = query.order_by(Book.added_date.desc())
    
    # ページネーション
    pagination = query.paginate(page=page, per_page=per_page)
    books = pagination.items
    
    # フィルター用のデータ取得
    genres = Genre.query.all()
    tags = Tag.query.all()
    locations = Location.query.all()
    
    return render_template(
        'book/index.html',
        books=books,
        pagination=pagination,
        genres=genres,
        tags=tags,
        locations=locations,
        search_query=search_query,
        genre_id=genre_id,
        tag_id=tag_id,
        location_id=location_id,
        sort_by=sort_by,
        sort_order=sort_order
    )

@book_bp.route('/<int:book_id>')
def detail(book_id):
    """書籍詳細ページ"""
    book = Book.query.get_or_404(book_id)
    return render_template('book/detail.html', book=book)

@book_bp.route('/new', methods=['GET', 'POST'])
def new():
    """書籍新規登録ページ"""
    # バーコード機能の状態を取得
    barcode_enabled = current_app.config.get('BARCODE_ENABLED', False)
    
    if request.method == 'POST':
        # フォームデータの取得
        title = request.form.get('title', '')
        author = request.form.get('author', '')
        publisher = request.form.get('publisher', '')
        isbn = request.form.get('isbn', '')
        jan_code = request.form.get('jan_code', '')
        # JANコードが'NON'の場合は空文字列に置き換える
        if jan_code == 'NON':
            jan_code = ''
        c_code = request.form.get('c_code', '')
        published_date = request.form.get('published_date', '')
        price = request.form.get('price', None)
        page_count = request.form.get('page_count', None)
        memo = request.form.get('memo', '')
        location_id = request.form.get('location_id', None)
        genre_ids = request.form.getlist('genres')
        tag_names = request.form.get('tags', '').split(',')
        cover_image_path = request.form.get('cover_image_path', '')
        
        # 数値変換
        if price:
            try:
                price = int(price)
            except ValueError:
                # 空の文字列や数値に変換できない場合は0として扱う
                price = 0
        else:
            # 価格が指定されていない場合は0として扱う
            price = 0
        
        if page_count:
            try:
                page_count = int(page_count)
            except ValueError:
                page_count = None
        
        if location_id:
            try:
                location_id = int(location_id)
            except ValueError:
                location_id = None
        
        # 書籍オブジェクトの作成
        book = Book(
            title=title,
            author=author,
            publisher=publisher,
            isbn=isbn,
            jan_code=jan_code,
            c_code=c_code,
            published_date=published_date,
            price=price,
            page_count=page_count,
            cover_image_path=cover_image_path,
            added_date=datetime.now().strftime('%Y-%m-%d'),
            memo=memo,
            location_id=location_id
        )
        
        # ジャンルの関連付け
        for genre_id in genre_ids:
            try:
                genre = Genre.query.get(int(genre_id))
                if genre:
                    book.genres.append(genre)
            except ValueError:
                pass
        
        # タグの処理
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if tag_name:
                # 既存タグの検索または新規作成
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                book.tags.append(tag)
        
        # データベースへの保存
        db.session.add(book)
        db.session.commit()
        
        flash('書籍が正常に登録されました', 'success')
        return redirect(url_for('books.detail', book_id=book.id))
    
    # GETリクエスト処理
    genres = Genre.query.all()
    locations = Location.query.all()
    
    # バーコードからの情報がある場合
    isbn = request.args.get('isbn', '')
    title = request.args.get('title', '')
    author = request.args.get('author', '')
    publisher = request.args.get('publisher', '')
    published_date = request.args.get('published_date', '')
    price = request.args.get('price', '')
    page_count = request.args.get('page_count', '')
    cover_image_path = request.args.get('cover_image_path', '')
    jan_code = request.args.get('jan_code', '')
    c_code = request.args.get('c_code', '')
    
    return render_template(
        'book/form.html',
        action='new',
        genres=genres,
        locations=locations,
        isbn=isbn,
        title=title,
        author=author,
        publisher=publisher,
        published_date=published_date,
        price=price,
        page_count=page_count,
        cover_image_path=cover_image_path,
        jan_code=jan_code,
        c_code=c_code,
        barcode_enabled=barcode_enabled
    )

@book_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
def edit(book_id):
    """書籍編集ページ"""
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        # フォームデータの取得と更新
        book.title = request.form.get('title', '')
        book.author = request.form.get('author', '')
        book.publisher = request.form.get('publisher', '')
        book.isbn = request.form.get('isbn', '')
        jan_code = request.form.get('jan_code', '')
        # JANコードが'NON'の場合は空文字列に置き換える
        if jan_code == 'NON':
            jan_code = ''
        book.jan_code = jan_code
        book.c_code = request.form.get('c_code', '')
        book.published_date = request.form.get('published_date', '')
        book.memo = request.form.get('memo', '')
        
        # 数値変換
        price = request.form.get('price', None)
        if price:
            try:
                book.price = int(price)
            except ValueError:
                # 空の文字列や数値に変換できない場合は0として扱う
                book.price = 0
        else:
            # 価格が指定されていない場合は0として扱う
            book.price = 0
        
        page_count = request.form.get('page_count', None)
        if page_count:
            try:
                book.page_count = int(page_count)
            except ValueError:
                pass
        else:
            book.page_count = None
        
        location_id = request.form.get('location_id', None)
        if location_id:
            try:
                book.location_id = int(location_id)
            except ValueError:
                book.location_id = None
        else:
            book.location_id = None
        
        # 表紙画像パスの更新（変更がある場合のみ）
        new_cover = request.form.get('cover_image_path', '')
        if new_cover:
            # 空文字列の場合はNoneに変換する
            if new_cover.strip() == '':
                book.cover_image_path = None
            elif new_cover != book.cover_image_path:
                book.cover_image_path = new_cover
        # フォームで明示的に削除された場合
        elif 'cover_image_path' in request.form:
            book.cover_image_path = None
        
        # ジャンルの更新
        book.genres = []  # 一旦リセット
        genre_ids = request.form.getlist('genres')
        for genre_id in genre_ids:
            try:
                genre = Genre.query.get(int(genre_id))
                if genre:
                    book.genres.append(genre)
            except ValueError:
                pass
        
        # タグの更新
        book.tags = []  # 一旦リセット
        tag_names = request.form.get('tags', '').split(',')
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if tag_name:
                # 既存タグの検索または新規作成
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                book.tags.append(tag)
        
        # データベースの更新
        db.session.commit()
        
        flash('書籍情報が更新されました', 'success')
        return redirect(url_for('books.detail', book_id=book.id))
    
    # GETリクエスト処理
    genres = Genre.query.all()
    locations = Location.query.all()
    
    # 現在のタグをカンマ区切りの文字列に変換
    current_tags = ','.join([tag.name for tag in book.tags])
    
    return render_template(
        'book/form.html',
        action='edit',
        book=book,
        genres=genres,
        locations=locations,
        current_tags=current_tags
    )

@book_bp.route('/<int:book_id>/delete', methods=['POST'])
def delete(book_id):
    """書籍削除処理"""
    book = Book.query.get_or_404(book_id)
    
    # 関連データのクリーンアップ（必要に応じて）
    
    # 表紙画像の削除（ファイルが存在する場合）
    if book.cover_image_path:
        try:
            file_path = os.path.join('static', book.cover_image_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"画像削除エラー: {e}")
    
    # データベースから削除
    db.session.delete(book)
    db.session.commit()
    
    flash('書籍が削除されました', 'info')
    return redirect(url_for('books.index'))

@book_bp.route('/bulk-delete', methods=['POST'])
def bulk_delete():
    """複数書籍の一括削除処理"""
    book_ids = request.form.get('book_ids', '')
    if not book_ids:
        flash('削除する書籍が選択されていません', 'danger')
        return redirect(url_for('books.index'))
    
    # カンマ区切りのIDリストを変換
    ids = [int(id) for id in book_ids.split(',') if id.isdigit()]
    deleted_count = 0
    
    for book_id in ids:
        book = Book.query.get(book_id)
        if book:
            # 表紙画像の削除（ファイルが存在する場合）
            if book.cover_image_path:
                try:
                    file_path = os.path.join('static', book.cover_image_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"画像削除エラー: {e}")
            
            # データベースから削除
            db.session.delete(book)
            deleted_count += 1
    
    # 変更を保存
    db.session.commit()
    
    flash(f'{deleted_count}冊の書籍が削除されました', 'info')
    return redirect(url_for('books.index'))

@book_bp.route('/api/search')
def api_search():
    """書籍検索API（JSONレスポンス）"""
    search_query = request.args.get('q', '')
    
    # 検索実行
    results = Book.query.filter(
        (Book.title.contains(search_query)) |
        (Book.author.contains(search_query)) |
        (Book.publisher.contains(search_query))
    ).limit(10).all()
    
    # レスポンスデータの作成
    books_data = []
    for book in results:
        books_data.append({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'publisher': book.publisher,
            'isbn': book.isbn,
            'cover_image': book.cover_image_path
        })
    
    return jsonify(books_data)

@book_bp.route('/test-image/<isbn>')
def test_image(isbn):
    """画像表示テストページ"""
    # ISBNから書籍を検索
    book = Book.query.filter_by(isbn=isbn).first()
    
    if not book:
        # ISBNが一致する書籍が見つからない場合は、最初の書籍を使用
        book = Book.query.first()
    
    # ハイフンの削除
    clean_isbn = isbn.replace('-', '')
    
    return render_template('test_image.html', isbn=clean_isbn, book=book)

@book_bp.route('/debug-covers')
def debug_covers():
    """表紙画像デバッグページ"""
    # 表紙画像がある書籍を優先的に取得
    books_with_covers = Book.query.filter(Book.cover_image_path.isnot(None)).all()
    books_without_covers = Book.query.filter(Book.cover_image_path.is_(None)).limit(5).all()
    
    # 両方を結合
    books = books_with_covers + books_without_covers
    
    return render_template('debug_covers.html', books=books)
