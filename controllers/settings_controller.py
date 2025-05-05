from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from models.book import db, Book
from models.genre import Genre
from models.tag import Tag
from models.location import Location
import csv
import json
import os
from datetime import datetime

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
def index():
    """設定メインページ"""
    return render_template('settings/index.html')

# ジャンル管理
@settings_bp.route('/genres', methods=['GET', 'POST'])
@login_required
def genres():
    """ジャンル管理ページ"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            # 新規ジャンル追加
            name = request.form.get('name', '').strip()
            
            if name:
                # 先頭と末尾の空白を削除し、連続する空白を1つに置換
                name = ' '.join(name.split())
                
                # 既存チェック
                existing = Genre.query.filter_by(name=name).first()
                if existing:
                    flash('同名のジャンルが既に存在します', 'warning')
                else:
                    # 新規追加
                    genre = Genre(name=name)
                    db.session.add(genre)
                    db.session.commit()
                    flash('ジャンルを追加しました', 'success')
            else:
                flash('ジャンル名を入力してください', 'danger')
                
        elif action == 'edit':
            # ジャンル編集
            genre_id = request.form.get('genre_id')
            new_name = request.form.get('name', '').strip()
            
            if genre_id and new_name:
                genre = Genre.query.get(genre_id)
                if genre:
                    # 先頭と末尾の空白を削除し、連続する空白を1つに置換
                    new_name = ' '.join(new_name.split())
                    
                    # 既存チェック（自分以外）
                    existing = Genre.query.filter(Genre.name == new_name, Genre.id != genre.id).first()
                    if existing:
                        flash('同名のジャンルが既に存在します', 'warning')
                    else:
                        # 更新
                        genre.name = new_name
                        db.session.commit()
                        flash('ジャンルを更新しました', 'success')
                else:
                    flash('指定されたジャンルが見つかりません', 'danger')
            else:
                flash('必要な情報が不足しています', 'danger')
                
        elif action == 'delete':
            # ジャンル削除
            genre_id = request.form.get('genre_id')
            
            if genre_id:
                genre = Genre.query.get(genre_id)
                if genre:
                    # 関連書籍の確認 - count()メソッドを使用
                    book_count = genre.books.count()
                    if book_count > 0:
                        flash(f'このジャンルは{book_count}冊の書籍で使用されています。削除できません。', 'warning')
                    else:
                        # 削除
                        db.session.delete(genre)
                        db.session.commit()
                        flash('ジャンルを削除しました', 'success')
                else:
                    flash('指定されたジャンルが見つかりません', 'danger')
            else:
                flash('ジャンルIDが指定されていません', 'danger')
        
        return redirect(url_for('settings.genres'))
    
    # ジャンル一覧取得
    genres = Genre.query.order_by(Genre.name).all()
    
    # 各ジャンルの書籍数をカウント
    genre_counts = {}
    for genre in genres:
        # lazy='dynamic'の設定でも正確にカウントできる方法
        genre_counts[genre.id] = genre.books.count()
    
    return render_template('settings/genres.html', genres=genres, genre_counts=genre_counts)

# タグ管理
@settings_bp.route('/tags', methods=['GET', 'POST'])
@login_required
def tags():
    """タグ管理ページ"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            # 新規タグ追加
            name = request.form.get('name', '').strip()
            
            if name:
                # 既存チェック
                existing = Tag.query.filter_by(name=name).first()
                if existing:
                    flash('同名のタグが既に存在します', 'warning')
                else:
                    # 新規追加
                    tag = Tag(name=name)
                    db.session.add(tag)
                    db.session.commit()
                    flash('タグを追加しました', 'success')
            else:
                flash('タグ名を入力してください', 'danger')
                
        elif action == 'edit':
            # タグ編集
            tag_id = request.form.get('tag_id')
            new_name = request.form.get('name', '').strip()
            
            if tag_id and new_name:
                tag = Tag.query.get(tag_id)
                if tag:
                    # 既存チェック（自分以外）
                    existing = Tag.query.filter(Tag.name == new_name, Tag.id != tag.id).first()
                    if existing:
                        flash('同名のタグが既に存在します', 'warning')
                    else:
                        # 更新
                        tag.name = new_name
                        db.session.commit()
                        flash('タグを更新しました', 'success')
                else:
                    flash('指定されたタグが見つかりません', 'danger')
            else:
                flash('必要な情報が不足しています', 'danger')
                
        elif action == 'delete':
            # タグ削除
            tag_id = request.form.get('tag_id')
            
            if tag_id:
                tag = Tag.query.get(tag_id)
                if tag:
                    # 関連削除（中間テーブルは自動的に削除される）
                    db.session.delete(tag)
                    db.session.commit()
                    flash('タグを削除しました', 'success')
                else:
                    flash('指定されたタグが見つかりません', 'danger')
            else:
                flash('タグIDが指定されていません', 'danger')
        
        return redirect(url_for('settings.tags'))
    
    # タグ一覧取得
    tags = Tag.query.order_by(Tag.name).all()
    
    # タグの使用数をカウント
    tag_counts = {}
    for tag in tags:
        tag_counts[tag.id] = len(tag.books.all())
    
    return render_template('settings/tags.html', tags=tags, tag_counts=tag_counts)

# 収納場所管理
@settings_bp.route('/locations', methods=['GET', 'POST'])
@login_required
def locations():
    """収納場所管理ページ"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            # 新規収納場所追加
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            
            if name:
                # 既存チェック
                existing = Location.query.filter_by(name=name).first()
                if existing:
                    flash('同名の収納場所が既に存在します', 'warning')
                else:
                    # 新規追加
                    location = Location(name=name, description=description)
                    db.session.add(location)
                    db.session.commit()
                    flash('収納場所を追加しました', 'success')
            else:
                flash('収納場所名を入力してください', 'danger')
                
        elif action == 'edit':
            # 収納場所編集
            location_id = request.form.get('location_id')
            new_name = request.form.get('name', '').strip()
            new_description = request.form.get('description', '').strip()
            
            if location_id and new_name:
                location = Location.query.get(location_id)
                if location:
                    # 既存チェック（自分以外）
                    existing = Location.query.filter(Location.name == new_name, Location.id != location.id).first()
                    if existing:
                        flash('同名の収納場所が既に存在します', 'warning')
                    else:
                        # 更新
                        location.name = new_name
                        location.description = new_description
                        db.session.commit()
                        flash('収納場所を更新しました', 'success')
                else:
                    flash('指定された収納場所が見つかりません', 'danger')
            else:
                flash('必要な情報が不足しています', 'danger')
                
        elif action == 'delete':
            # 収納場所削除
            location_id = request.form.get('location_id')
            
            if location_id:
                location = Location.query.get(location_id)
                if location:
                    # 関連書籍の確認
                    book_count = Book.query.filter_by(location_id=location.id).count()
                    if book_count > 0:
                        flash(f'この収納場所は{book_count}冊の書籍で使用されています。削除できません。', 'warning')
                    else:
                        # 削除
                        db.session.delete(location)
                        db.session.commit()
                        flash('収納場所を削除しました', 'success')
                else:
                    flash('指定された収納場所が見つかりません', 'danger')
            else:
                flash('収納場所IDが指定されていません', 'danger')
        
        return redirect(url_for('settings.locations'))
    
    # 収納場所一覧取得
    locations = Location.query.order_by(Location.name).all()
    
    # 各収納場所の書籍数をカウント
    location_counts = {}
    for location in locations:
        location_counts[location.id] = Book.query.filter_by(location_id=location.id).count()
    
    return render_template('settings/locations.html', locations=locations, location_counts=location_counts)

# データエクスポート
@settings_bp.route('/export', methods=['GET', 'POST'])
@login_required
def export():
    """データエクスポートページ"""
    if request.method == 'POST':
        export_format = request.form.get('format', 'csv')
        
        if export_format == 'csv':
            # CSVエクスポート
            return _export_csv()
        elif export_format == 'json':
            # JSONエクスポート
            return _export_json()
        else:
            flash('不正なフォーマットが指定されました', 'danger')
            return redirect(url_for('settings.export'))
    
    return render_template('settings/export.html')

def _export_csv():
    """CSVフォーマットでのエクスポート"""
    books = Book.query.all()
    
    # 一時ファイルを作成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"books_export_{timestamp}.csv"
    filepath = os.path.join(current_app.static_folder, filename)
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # ヘッダー行
            writer.writerow([
                'ID', 'タイトル', '著者', '出版社', 'ISBN', 'JANコード',
                '出版日', '価格', 'ページ数', '表紙画像', '追加日', 'メモ',
                '収納場所', 'ジャンル', 'タグ'
            ])
            
            # データ行
            for book in books:
                # 収納場所名の取得
                location_name = book.location.name if book.location else ''
                
                # ジャンル名のリスト
                genres = ','.join([genre.name for genre in book.genres])
                
                # タグ名のリスト
                tags = ','.join([tag.name for tag in book.tags])
                
                writer.writerow([
                    book.id, book.title, book.author, book.publisher,
                    book.isbn, book.jan_code, book.published_date,
                    book.price, book.page_count, book.cover_image_path,
                    book.added_date, book.memo, location_name, genres, tags
                ])
        
        # ファイルをクライアントに送信
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
    
    except Exception as e:
        flash(f'エクスポート中にエラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('settings.export'))

def _export_json():
    """JSONフォーマットでのエクスポート"""
    books = Book.query.all()
    
    # JSONデータの作成
    data = []
    
    for book in books:
        # 収納場所
        location = {
            'id': book.location.id,
            'name': book.location.name,
            'description': book.location.description
        } if book.location else None
        
        # ジャンル
        genres = [{'id': genre.id, 'name': genre.name} for genre in book.genres]
        
        # タグ
        tags = [{'id': tag.id, 'name': tag.name} for tag in book.tags]
        
        # 書籍データ
        book_data = {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'publisher': book.publisher,
            'isbn': book.isbn,
            'jan_code': book.jan_code,
            'published_date': book.published_date,
            'price': book.price,
            'page_count': book.page_count,
            'cover_image_path': book.cover_image_path,
            'added_date': book.added_date,
            'memo': book.memo,
            'location': location,
            'genres': genres,
            'tags': tags
        }
        
        data.append(book_data)
    
    # 一時ファイルを作成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"books_export_{timestamp}.json"
    filepath = os.path.join(current_app.static_folder, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # ファイルをクライアントに送信
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
    
    except Exception as e:
        flash(f'エクスポート中にエラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('settings.export'))
