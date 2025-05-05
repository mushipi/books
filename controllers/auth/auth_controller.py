from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.users.user import User, db
from werkzeug.urls import url_parse
import datetime

# Blueprintの作成
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン処理"""
    # すでにログインしている場合はホームページにリダイレクト
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # POSTリクエスト（ログインフォーム送信）の場合
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = 'remember_me' in request.form
        
        # ユーザーが存在するか確認
        user = User.query.filter_by(username=username).first()
        
        # ユーザーが存在しないかパスワードが一致しない場合
        if user is None or not user.check_password(password):
            flash('ユーザー名またはパスワードが正しくありません', 'danger')
            return redirect(url_for('auth.login'))
        
        # ログイン成功
        login_user(user, remember=remember_me)
        user.update_last_login()
        flash(f'ようこそ、{user.username}さん！', 'success')
        
        # ログイン後のリダイレクト先を決定
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        
        return redirect(next_page)
    
    # GETリクエスト（ログインページ表示）の場合
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """ログアウト処理"""
    logout_user()
    flash('ログアウトしました', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """ユーザープロフィール表示"""
    return render_template('auth/profile.html')

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """パスワード変更処理"""
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    # 現在のパスワードが正しいか確認
    if not current_user.check_password(current_password):
        flash('現在のパスワードが正しくありません', 'danger')
        return redirect(url_for('auth.profile'))
    
    # 新しいパスワードと確認用パスワードが一致するか確認
    if new_password != confirm_password:
        flash('新しいパスワードと確認用パスワードが一致しません', 'danger')
        return redirect(url_for('auth.profile'))
    
    # パスワード変更処理
    current_user.set_password(new_password)
    db.session.commit()
    flash('パスワードを変更しました', 'success')
    return redirect(url_for('auth.profile'))
