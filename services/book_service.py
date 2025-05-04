from models.book import Book
from models.genre import Genre

class BookService:
    def __init__(self, db, api_service):
        """
        書籍サービスの初期化
        
        Args:
            db: データベースインスタンス
            api_service: API検索サービス
        """
        self.db = db
        self.api_service = api_service
    
    def get_all_books(self, page=1, per_page=20, genre_id=None):
        """
        書籍一覧を取得する
        
        Args:
            page: ページ番号
            per_page: 1ページあたりの表示件数
            genre_id: ジャンルIDによるフィルタリング
            
        Returns:
            tuple: (書籍リスト, 総件数, 総ページ数)
        """
        query = Book.query
        
        # ジャンルでフィルタリング
        if genre_id:
            genre = Genre.query.get(genre_id)
            if genre:
                query = query.filter(Book.genres.contains(genre))
        
        # 総件数の取得
        total_count = query.count()
        
        # ページネーション
        books = query.order_by(Book.title).paginate(page=page, per_page=per_page)
        
        # 総ページ数の計算
        total_pages = (total_count + per_page - 1) // per_page
        
        return books.items, total_count, total_pages
    
    def get_book_by_id(self, book_id):
        """
        IDから書籍を取得する
        
        Args:
            book_id: 書籍ID
            
        Returns:
            Book: 書籍エンティティ
        """
        return Book.query.get(book_id)
    
    def get_book_by_jan(self, jan_code):
        """
        JANコードから書籍を取得する
        
        Args:
            jan_code: JANコード/ISBN-13
            
        Returns:
            Book: 書籍エンティティ
        """
        return Book.query.filter_by(isbn=jan_code).first()
    
    def check_exists_by_jan(self, jan_code):
        """
        JANコードから書籍の存在をチェックする
        
        Args:
            jan_code: JANコード/ISBN-13
            
        Returns:
            bool: 書籍が存在するかどうか
        """
        return Book.query.filter_by(isbn=jan_code).count() > 0
    
    def register_book_by_jan(self, jan_code, default_genre_id=None):
        """
        JANコードから書籍情報を取得して登録する
        
        Args:
            jan_code: JANコード/ISBN-13
            default_genre_id: デフォルトのジャンルID
            
        Returns:
            Book: 登録された書籍エンティティ
        """
        # すでに存在する場合は取得して返す
        existing_book = self.get_book_by_jan(jan_code)
        if existing_book:
            return existing_book
        
        # API経由で書籍情報を取得
        book_info = self.api_service.lookup_isbn(jan_code)
        
        if not book_info:
            return None
        
        # 書籍エンティティを作成
        jan_code_clean = '' if jan_code == 'NON' else jan_code
        
        book = Book(
            title=book_info.get('title', ''),
            author=book_info.get('author', ''),
            publisher=book_info.get('publisher', ''),
            isbn=jan_code,
            jan_code=jan_code_clean,
            c_code=book_info.get('c_code', ''),
            published_date=book_info.get('published_date', ''),
            cover_image_path=book_info.get('cover_image_path'),
            price=book_info.get('price'),
            page_count=book_info.get('page_count')
        )
        
        # デフォルトジャンルの設定
        if default_genre_id:
            genre = Genre.query.get(default_genre_id)
            if genre:
                book.genres.append(genre)
        
        # データベースに保存
        self.db.session.add(book)
        self.db.session.commit()
        
        return book
    
    def create_book(self, book_data, genre_ids=None):
        """
        書籍を新規作成する
        
        Args:
            book_data: 書籍データ
            genre_ids: ジャンルIDのリスト
            
        Returns:
            Book: 作成された書籍エンティティ
        """
        book = Book(
            title=book_data.get('title', ''),
            author=book_data.get('author', ''),
            publisher=book_data.get('publisher', ''),
            isbn=book_data.get('isbn', ''),
            published_date=book_data.get('published_date', ''),
            cover_image_path=book_data.get('cover_image_path'),
            price=book_data.get('price'),
            page_count=book_data.get('page_count'),
            memo=book_data.get('memo', '')
        )
        
        # ジャンルの設定
        if genre_ids:
            genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
            for genre in genres:
                book.genres.append(genre)
        
        # データベースに保存
        self.db.session.add(book)
        self.db.session.commit()
        
        return book
    
    def update_book(self, book_id, book_data, genre_ids=None):
        """
        書籍情報を更新する
        
        Args:
            book_id: 書籍ID
            book_data: 更新データ
            genre_ids: ジャンルIDのリスト
            
        Returns:
            Book: 更新された書籍エンティティ
        """
        book = self.get_book_by_id(book_id)
        
        if not book:
            return None
        
        # 書籍情報の更新
        book.title = book_data.get('title', book.title)
        book.author = book_data.get('author', book.author)
        book.publisher = book_data.get('publisher', book.publisher)
        book.isbn = book_data.get('isbn', book.isbn)
        book.published_date = book_data.get('published_date', book.published_date)
        
        if 'cover_image_path' in book_data and book_data['cover_image_path']:
            book.cover_image_path = book_data['cover_image_path']
            
        book.price = book_data.get('price', book.price)
        book.page_count = book_data.get('page_count', book.page_count)
        book.memo = book_data.get('memo', book.memo)
        
        # ジャンルの更新
        if genre_ids is not None:
            # 既存のジャンルをクリア
            book.genres = []
            
            # 新しいジャンルを設定
            genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
            for genre in genres:
                book.genres.append(genre)
        
        # データベースに保存
        self.db.session.commit()
        
        return book
    
    def delete_book(self, book_id):
        """
        書籍を削除する
        
        Args:
            book_id: 書籍ID
            
        Returns:
            bool: 削除が成功したかどうか
        """
        book = self.get_book_by_id(book_id)
        
        if not book:
            return False
        
        # データベースから削除
        self.db.session.delete(book)
        self.db.session.commit()
        
        return True
    
    def search_books(self, keyword, page=1, per_page=20):
        """
        書籍を検索する
        
        Args:
            keyword: 検索キーワード
            page: ページ番号
            per_page: 1ページあたりの表示件数
            
        Returns:
            tuple: (書籍リスト, 総件数, 総ページ数)
        """
        # 検索条件の設定
        conditions = []
        
        # タイトル、著者、出版社、ISBNで検索
        for field in [Book.title, Book.author, Book.publisher, Book.isbn, Book.memo]:
            conditions.append(field.ilike(f'%{keyword}%'))
        
        # OR条件で検索
        query = Book.query.filter(db.or_(*conditions))
        
        # 総件数の取得
        total_count = query.count()
        
        # ページネーション
        books = query.order_by(Book.title).paginate(page=page, per_page=per_page)
        
        # 総ページ数の計算
        total_pages = (total_count + per_page - 1) // per_page
        
        return books.items, total_count, total_pages
