# 本管理アプリケーション開発プロジェクト概要

## Gemini APIを活用した一括取り込み機能の実装（2025-05-03）

### 機能概要

カメラ機能がうまく動作しない問題に対応するため、JPEG画像からISBNバーコード、Cコード、価格情報を抽出して一括取り込みする代替機能を実装しました。Google Gemini APIを使用して高精度な画像認識を実現しています。

### 実装した機能

1. **BookCodeExtractorクラス**:
   - ISBNバーコード（JANコード）、ISBN文字列、Cコード、価格表示を抽出
   - 段階的処理方式（バーコード検出 → OCR → 必要に応じてAI処理）
   - コスト効率のために基本はローカル処理、難しい場合のみGemini APIを利用

2. **一括取り込み機能**：
   - フォルダ内のJPEG画像をスキャンして書籍情報を抽出
   - 抽出した情報を元に書籍データを一括でデータベースに登録
   - デフォルトのジャンルを設定可能
   - 既に登録済みの書籍は自動的に除外

3. **インターフェース**：
   - Webインターフェースでの一括取り込み機能
   - コマンドラインバッチ処理ツール
   - GUIバッチ処理ツール

### 問題点と対応

実装時に発生した問題とその対応策をテストするためのツールを開発しました。

#### テストツール

1. **test_gemini_api.py**:
   - Gemini APIの単体テスト用スクリプト
   - API呼び出しと画像処理の部分を分離してテスト

2. **test_folder_images.py**:
   - フォルダ内のすべての画像をテスト
   - 結果とエラーを詳細にログ記録

3. **test_book_extraction.py**:
   - BookCodeExtractorクラスの単体テスト
   - 画像からの書籍コード抽出機能のテスト

#### 想定される問題点と解決策

1. **Gemini API接続エラー**:
   - APIキーの確認
   - ネットワーク接続の問題を確認
   - APIリクエスト制限に達していないか確認

2. **画像処理エラー**:
   - 画像形式や解像度の問題
   - 画像サイズが大きすぎる場合は前処理で圧縮
   - ファイルパスに特殊文字が含まれていないか確認

3. **コード抽出精度の問題**:
   - プロンプトの改良
   - 画像の前処理の改善（明るさ、コントラスト調整など）
   - 複数の認識結果の組み合わせ

4. **一括取り込みのUIエラー**:
   - フォルダパスの取り扱いの問題
   - 非同期処理のタイミング問題
   - ユーザーフィードバックの不足

### 今後の計画

1. **BookCodeExtractorクラスの改善**:
   - エラーハンドリングの強化
   - 抽出精度を向上させるための調整

2. **一括取り込み機能の改善**:
   - UI/UXのフィードバック強化
   - 処理状況の視覚化を改善

3. **ローカル認識精度の向上**:
   - pyzbar代替の他のバーコード認識ライブラリの調査
   - OCR認識の改善

### 実行方法

1. **一括取り込み機能の使用**:
   - ブラウザで `http://localhost:5000/bulk-import/` にアクセス
   - JPEG画像が入ったフォルダを指定
   - デフォルトジャンルを選択してスキャン実行
   - 取り込む書籍を選択してインポート

2. **テストツールの使用**:
   - 個別画像のテスト: `python test_gemini_api.py <画像パス>`
   - フォルダテスト: `python test_folder_images.py <フォルダパス>`

### 技術的なポイント

1. **ハイブリッド認識アプローチ**:
   - 基本はローカル処理で高速、難しいケースのみ五Gemini APIを使用
   - コスト効率が良く、高精度な認識が可能

2. **複数のインターフェース**:
   - Webブラウザ、コマンドライン、GUIの3種類のインターフェースを提供
   - 様々な使用シーンに対応可能

3. **エラーハンドリングの強化**:
   - 詳細なエラー情報の収集と表示
   - ユーザーへのわかりやすいフィードバック# 本管理アプリケーション開発プロジェクト概要

## プロジェクト概要

自宅の蔵書を効率的に管理するためのウェブベースアプリケーションを開発しました。本のバーコード（JANコード/ISBN）から情報を取得し、データベースで一元管理する機能を実装しています。

## 技術スタック

- **バックエンド**: Flask (Python)
- **データベース**: SQLite (Flask-SQLAlchemy)
- **フロントエンド**: Bootstrap 5
- **バーコード処理**: pyzbar/OpenCV (サーバーサイド), QuaggaJS (クライアントサイド)
- **API連携**: OpenBD API, 国立国会図書館API

## 主要機能

1. **書籍管理**
   - 基本情報管理（追加・編集・削除）
   - 書籍情報表示（タイトル、著者、出版社、ISBN等）
   - 表紙画像の表示

2. **バーコードスキャン**
   - カメラ入力からのISBN/JANコード読取り
   - 外部APIからの書籍情報自動取得

3. **検索・分類**
   - 検索・ソート機能
   - ジャンル/タグ管理
   - 収納場所管理

4. **データエクスポート**
   - CSV/JSON形式でのエクスポート

## アプリケーション構造

```
book_manager/
├── app.py                  # メインアプリケーション
├── config.py               # 設定ファイル
├── db_init.py              # データベース初期化スクリプト
├── models/                 # データモデル
│   ├── book.py
│   ├── genre.py
│   ├── tag.py
│   └── location.py
├── controllers/            # コントローラー
│   ├── book_controller.py
│   ├── barcode_controller.py
│   └── settings_controller.py
├── services/               # ビジネスロジック
│   ├── barcode_service.py
│   ├── api_service.py
│   └── image_service.py
├── static/                 # 静的ファイル
│   ├── css/
│   ├── js/
│   └── img/
├── templates/              # HTMLテンプレート
└── instance/               # SQLiteデータベース
```

## 環境設定の問題

現在発生している課題:
- NumPyバージョンの互換性問題 (NumPy 2.2.5とOpenCVの互換性がない)
- Anaconda環境と標準Python環境の混在による問題

## 解決策

1. **NumPyのダウングレード**:
   ```
   pip uninstall numpy
   pip install numpy==1.26.0
   ```

2. **OpenCVの再インストール**:
   ```
   pip uninstall opencv-python
   pip install opencv-python==4.7.0.72
   ```

3. **代替案**: バーコードスキャン機能を無効化し、基本機能のみで運用

## 今後の拡張計画

1. **PWA対応** (オフライン動作)
2. **ユーザー認証** (家族での共有)
3. **QRコード生成機能** (自作ラベル発行)
4. **読書状況管理機能** (未読・読書中・読了等の状態管理)
5. **貸出管理機能** (貸出先や貸出日の記録)

## 参考資料

- Flask公式ドキュメント
- Bootstrap 5ドキュメント
- OpenBD API仕様
- 国立国会図書館API仕様
- ZBar/OpenCV ドキュメント
- QuaggaJS ドキュメント

## ジャンル管理の問題と修正（2025-05-02）

### 問題点

1. **ジャンルの書籍数カウントの問題**:
   - `settings_controller.py` の `genres` 関数で、ジャンル削除時にジャンルに関連づけられた書籍数を確認する際に `len(genre.books.all())` を使用していたが、これが正しく動作していなかった。
   - SQLAlchemy の `lazy='dynamic'` の設定により、`genres.html` テンプレート内で `genre.books|length` を使用する際に、実際の書籍数が正しく表示されない問題があった。

2. **ジャンル選択UIの問題**:
   - `book/form.html` で、ジャンル選択がシンプルなチェックボックスのリストになっており、ジャンル数が多くなると使いづらくなる問題があった。

3. **ジャンル追加・編集時のバリデーション不足**:
   - 空白を含むジャンル名が許可されており、ユーザーインターフェースに関わる問題が発生する可能性があった。

### 修正内容

1. **ジャンル書籍数カウントの修正**:
   - `settings_controller.py` の `genres` 関数を修正し、書籍数のカウントを正確にするために `genre_counts` 辞書を利用し、`genre.books.count()` メソッドを使用するように変更。
   - `templates/settings/genres.html` の表示部分も修正し、`genre_counts[genre.id]` を使って書籍数を表示するように変更。

2. **ジャンル削除処理の修正**:
   - ジャンル削除時のチェックも修正し、`len(genre.books.all())` から `genre.books.count()` メソッドを使用するように変更。

3. **ジャンル名のバリデーション強化**:
   - `settings_controller.py` のジャンル追加・編集時のバリデーションを強化し、先頭と末尾の空白を削除し、連続する空白を1つに置換する処理を追加。

4. **ジャンル選択UIの改善**:
   - `book/form.html` のジャンル選択部分を改善し、スクロール可能なコンテナにジャンル選択チェックボックスを配置。
   - ジャンル管理ページへのリンクボタンを追加し、ユーザーが簡単にジャンルを管理できるように対応。

### 修正コード

1. **settings_controller.py の修正**:
   ```python
   # ジャンル一覧取得
   genres = Genre.query.order_by(Genre.name).all()
   
   # 各ジャンルの書籍数をカウント
   genre_counts = {}
   for genre in genres:
       # lazy='dynamic'の設定でも正確にカウントできる方法
       genre_counts[genre.id] = genre.books.count()
   
   return render_template('settings/genres.html', genres=genres, genre_counts=genre_counts)
   ```

2. **ジャンル名のバリデーション**:
   ```python
   # 先頭と末尾の空白を削除し、連続する空白を1つに置換
   name = ' '.join(name.split())
   ```

3. **genres.html の修正**:
   ```html
   {% if genre_counts[genre.id] > 0 %}
   <a href="{{ url_for('books.index', genre=genre.id) }}" class="text-decoration-none">
       <span class="badge bg-primary">{{ genre_counts[genre.id] }}冊</span>
   </a>
   {% else %}
   <span class="badge bg-secondary">0冊</span>
   {% endif %}
   ```

4. **book/form.html のジャンル選択UI改善**:
   ```html
   <div class="genres-container" style="max-height: 200px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 4px; padding: 10px;">
       {% for genre in genres %}
       <div class="form-check">
           <input class="form-check-input" type="checkbox" name="genres" id="genre-{{ genre.id }}" value="{{ genre.id }}"
           {% if action == 'edit' and genre in book.genres %}checked{% endif %}>
           <label class="form-check-label" for="genre-{{ genre.id }}">
               {{ genre.name }}
           </label>
       </div>
       {% endfor %}
   </div>
   <div class="mt-2">
       <a href="{{ url_for('settings.genres') }}" target="_blank" class="btn btn-sm btn-outline-secondary">
           <i class="fas fa-plus me-1"></i> ジャンル管理
       </a>
   </div>
   ```

## バーコードスキャン機能の修正（2025-05-02）

### 問題点

1. **カメラ機能の初期化エラー**:
   - エラーメッセージ: `カメラの起動に失敗しました: Ut[e] is not a constructor`
   - GUIにカメラ映像は表示されるが、初期化プロセスで問題が発生
   - PCのUSBカメラだけでなく、スマートフォンでもカメラ選択ができない問題

2. **モバイル対応の不足**:
   - スマートフォンでのカメラ使用に特化した機能が不足
   - スマートフォンのフロント/バックカメラ切り替え機能がない

3. **エラーハンドリングの不足**:
   - カメラ初期化時の例外処理が不十分
   - ブラウザ間の互換性問題への対応が不足

### 修正内容

1. **QuaggaJSライブラリの変更**:
   - `@ericblade/quagga2@1.8.2` から元の `quagga@0.12.1` に変更
   - より安定したオリジナルバージョンを使用することでエラーを軽減

2. **スキャナー設定の簡略化**:
   - 初期化設定をシンプルにし、不要なオプションを削除
   - デバイス指定方法の最適化

3. **モバイル向け機能の追加**:
   - モバイルデバイス自動検出機能を追加
   - フロント/バックカメラ切り替えボタンの実装
   - バイブレーション機能の追加（バーコード検出時）

4. **レスポンシブデザインの強化**:
   - モバイル画面に最適化したスタイルを適用
   - 画面サイズに応じたUIの自動調整

5. **デバッグ機能の強化**:
   - 詳細なログ記録機能を追加
   - ブラウザAPI対応状況の確認コードを追加

### 修正コードのポイント

1. **モバイルデバイス検出**:
   ```javascript
   let isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
   ```

2. **カメラ設定の最適化**:
   ```javascript
   // モバイルとPC用で異なる設定
   if (isMobile) {
       constraints = {
           width: { min: 640, ideal: 1280, max: 1920 },
           height: { min: 480, ideal: 720, max: 1080 },
           facingMode: currentFacingMode
       };
   } else {
       constraints = {
           width: { min: 640, ideal: 1280, max: 1920 },
           height: { min: 480, ideal: 720, max: 1080 },
           deviceId: deviceId ? { exact: deviceId } : undefined
       };
   }
   ```

3. **モバイル向けUIコンポーネント**:
   ```html
   <!-- モバイル向けカメラ切り替えボタン -->
   <div class="camera-selection-mobile d-md-none mb-3">
       <button id="camera-front" class="btn btn-outline-primary">
           <i class="fas fa-user me-1"></i> フロントカメラ
       </button>
       <button id="camera-back" class="btn btn-outline-primary">
           <i class="fas fa-camera me-1"></i> バックカメラ
       </button>
   </div>
   ```

4. **エラーハンドリングの強化**:
   ```javascript
   try {
       Quagga.init(config, function(err) {
           if (err) {
               logError('Quagga初期化エラー:', err);
               showStatus(`カメラの起動に失敗しました: ${err.message || 'エラーが発生しました'}`, 'error');
               // エラーUI更新
               return;
           }
           // 成功処理
       });
   } catch (error) {
       logError('Quagga初期化例外:', error);
       showStatus(`カメラの初期化中にエラーが発生しました: ${error.message || 'エラーが発生しました'}`, 'error');
       // 例外UI更新
   }
   ```

5. **デバッグ情報の追加**:
   ```javascript
   // デバッグ情報 - ブラウザのAPIサポート状況確認
   console.log("ブラウザ情報：", navigator.userAgent);
   console.log("navigator.mediaDevices サポート: ", !!navigator.mediaDevices);
   console.log("navigator.mediaDevices.getUserMedia サポート: ", !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia));
   console.log("navigator.getUserMedia サポート（レガシー）: ", !!(navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia));
   ```

### 今後の検討事項

1. **ブラウザ互換性の問題**:
   - `getUserMedia` APIの実装がブラウザによって異なる
   - セキュリティポリシーの影響（HTTPS接続の必要性）

2. **代替バーコードライブラリの検討**:
   - ZXingやhtml5-qrcodeなど別のライブラリの検討
   - バーコードスキャン機能が問題を起こし続ける場合の代替策

3. **フォールバック対策**:
   - カメラアクセスが利用できない環境でのフォールバック処理
   - 手動入力機能のさらなる強化
