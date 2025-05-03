import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import time
from datetime import datetime
import csv
import json

# プロジェクトルートを追加
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from services.book_code_extractor import BookCodeExtractor

class BatchExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("書籍コード一括抽出ツール")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # 状態変数
        self.processing = False
        self.input_folder = tk.StringVar()
        self.output_file = tk.StringVar()
        self.use_ai = tk.BooleanVar(value=True)
        self.output_format = tk.StringVar(value="csv")
        
        # 各枠の設定
        self.setup_ui()
    
    def setup_ui(self):
        """UIの構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 入力フォルダ選択
        folder_frame = ttk.LabelFrame(main_frame, text="入力フォルダ", padding="5")
        folder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(folder_frame, textvariable=self.input_folder, width=70).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(folder_frame, text="参照...", command=self.browse_folder).pack(side=tk.RIGHT, padx=5)
        
        # 出力設定
        output_frame = ttk.LabelFrame(main_frame, text="出力設定", padding="5")
        output_frame.pack(fill=tk.X, pady=5)
        
        # 出力フォーマット
        format_frame = ttk.Frame(output_frame)
        format_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(format_frame, text="出力形式:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="CSV", variable=self.output_format, value="csv", 
                        command=self.update_file_extension).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="JSON", variable=self.output_format, value="json", 
                        command=self.update_file_extension).pack(side=tk.LEFT, padx=5)
        
        # 出力ファイル
        file_frame = ttk.Frame(output_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="出力ファイル:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(file_frame, textvariable=self.output_file, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="参照...", command=self.browse_output_file).pack(side=tk.RIGHT, padx=5)
        
        # オプション設定
        option_frame = ttk.LabelFrame(main_frame, text="オプション", padding="5")
        option_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(option_frame, text="Google Gemini APIを使用して認識精度を向上（処理時間が増加します）", 
                         variable=self.use_ai).pack(anchor=tk.W, padx=5, pady=5)
        
        # ログ表示エリア
        log_frame = ttk.LabelFrame(main_frame, text="処理ログ", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(main_frame, text="待機中...")
        self.progress_label.pack(anchor=tk.W, pady=2)
        
        # 実行ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="処理開始", command=self.start_processing)
        self.start_button.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="終了", command=self.root.destroy).pack(side=tk.RIGHT, padx=5)
    
    def update_file_extension(self):
        """出力ファイルの拡張子を更新"""
        output_path = self.output_file.get()
        if output_path:
            # 拡張子を変更
            base_name = os.path.splitext(output_path)[0]
            new_ext = ".csv" if self.output_format.get() == "csv" else ".json"
            self.output_file.set(base_name + new_ext)
    
    def browse_folder(self):
        """入力フォルダの選択ダイアログを表示"""
        folder = filedialog.askdirectory(title="処理する画像が含まれるフォルダを選択")
        if folder:
            self.input_folder.set(folder)
            # 自動的に出力ファイル名を設定
            if not self.output_file.get():
                folder_name = os.path.basename(folder)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                extension = ".csv" if self.output_format.get() == "csv" else ".json"
                self.output_file.set(f"{folder_name}_codes_{timestamp}{extension}")
    
    def browse_output_file(self):
        """出力ファイルの選択ダイアログを表示"""
        file_types = [("CSVファイル", "*.csv")] if self.output_format.get() == "csv" else [("JSONファイル", "*.json")]
        default_ext = ".csv" if self.output_format.get() == "csv" else ".json"
        
        file = filedialog.asksaveasfilename(
            title="出力ファイルを選択",
            filetypes=file_types,
            defaultextension=default_ext
        )
        if file:
            self.output_file.set(file)
    
    def log(self, message):
        """ログメッセージを表示"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_processing(self):
        """処理を開始"""
        if self.processing:
            return
        
        # 入力チェック
        folder_path = self.input_folder.get().strip()
        if not folder_path:
            messagebox.showerror("エラー", "入力フォルダを選択してください。")
            return
        
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            messagebox.showerror("エラー", f"フォルダ '{folder_path}' が存在しないか、ディレクトリではありません。")
            return
        
        output_path = self.output_file.get().strip()
        if not output_path:
            messagebox.showerror("エラー", "出力ファイルを指定してください。")
            return
        
        # JPEGファイルの検索
        image_files = []
        for file in os.listdir(folder_path):
            lower_file = file.lower()
            if lower_file.endswith(".jpg") or lower_file.endswith(".jpeg"):
                image_files.append(os.path.join(folder_path, file))
        
        if not image_files:
            messagebox.showwarning("警告", f"フォルダ '{folder_path}' にJPEG画像が見つかりませんでした。")
            return
        
        # 処理開始
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        
        # 別スレッドで処理を実行
        processing_thread = threading.Thread(target=self.process_images, args=(folder_path, image_files, output_path))
        processing_thread.start()
    
    def process_images(self, folder_path, image_files, output_path):
        """画像ファイルの処理（別スレッドで実行）"""
        try:
            total_images = len(image_files)
            self.log(f"処理開始: {folder_path}")
            self.log(f"処理対象ファイル数: {total_images}")
            self.log(f"AIバックアップ認識: {'有効' if self.use_ai.get() else '無効'}")
            self.log("=" * 50)
            
            # BookCodeExtractorの初期化
            try:
                extractor = BookCodeExtractor(use_ai_fallback=self.use_ai.get())
            except Exception as e:
                error_msg = f"BookCodeExtractorの初期化中にエラーが発生しました: {str(e)}"
                self.log(error_msg)
                messagebox.showerror("エラー", error_msg)
                # 処理状態をリセット
                self.processing = False
                self.start_button.config(state=tk.NORMAL)
                self.progress_label.config(text="エラー: 初期化失敗")
                return
            
            # 出力ファイルの準備
            output_format = self.output_format.get()
            
            if output_format == "csv":
                csv_file = open(output_path, 'w', newline='', encoding='utf-8')
                csv_writer = csv.writer(csv_file)
                # ヘッダーの書き込み
                csv_writer.writerow([
                    "ファイル名", "ISBNバーコード", "JANバーコード", 
                    "ISBN文字列", "Cコード", "価格コード"
                ])
            else:  # JSON
                json_results = []
            
            success_count = 0
            
            # 各画像ファイルを処理
            for index, image_path in enumerate(image_files):
                file_name = os.path.basename(image_path)
                
                # 進捗更新
                progress = (index / total_images) * 100
                self.progress_var.set(progress)
                self.progress_label.config(text=f"処理中... ({index}/{total_images}) {progress:.1f}% - {file_name}")
                
                try:
                    # 画像からコードを抽出
                    start_time = time.time()
                    extracted_codes = extractor.extract_codes_from_image(image_path)
                    processing_time = time.time() - start_time
                    
                    # コードが一つでも抽出できた場合、成功としてカウント
                    if any(extracted_codes.values()):
                        success_count += 1
                    
                    # 出力形式に応じて結果を書き込み
                    if output_format == "csv":
                        csv_writer.writerow([
                            file_name,
                            extracted_codes.get("isbn_barcode", ""),
                            extracted_codes.get("jan_barcode", ""),
                            extracted_codes.get("isbn_text", ""),
                            extracted_codes.get("c_code", ""),
                            extracted_codes.get("price_code", "")
                        ])
                    else:  # JSON
                        json_results.append({
                            "file_name": file_name,
                            "codes": extracted_codes
                        })
                    
                    # ログに表示
                    self.log(f"処理: {file_name} ({processing_time:.2f}秒)")
                    
                    # 抽出結果をログに表示（コンパクトに）
                    codes_found = []
                    if extracted_codes.get("isbn_barcode"):
                        codes_found.append(f"ISBN: {extracted_codes['isbn_barcode']}")
                    if extracted_codes.get("isbn_text"):
                        codes_found.append(f"ISBN文字列: {extracted_codes['isbn_text']}")
                    if extracted_codes.get("c_code"):
                        codes_found.append(f"Cコード: {extracted_codes['c_code']}")
                    if extracted_codes.get("price_code"):
                        codes_found.append(f"価格: {extracted_codes['price_code']}")
                    
                    if codes_found:
                        self.log(f"  検出: {', '.join(codes_found)}")
                    else:
                        self.log(f"  コード検出なし")
                
                except Exception as e:
                    self.log(f"エラー: {file_name} - {str(e)}")
            
            # 処理完了
            self.progress_var.set(100)
            
            # 出力ファイルの保存
            if output_format == "csv":
                csv_file.close()
            else:  # JSON
                with open(output_path, 'w', encoding='utf-8') as json_file:
                    json.dump(json_results, json_file, ensure_ascii=False, indent=2)
            
            # 結果を表示
            self.log("=" * 50)
            self.log(f"処理完了!")
            self.log(f"処理画像数: {total_images}")
            self.log(f"成功数: {success_count} ({success_count/total_images*100:.1f}%)")
            self.log(f"出力ファイル: {os.path.abspath(output_path)}")
            
            # 完了メッセージ
            messagebox.showinfo("処理完了", 
                               f"処理が完了しました。\n\n"
                               f"処理画像数: {total_images}\n"
                               f"成功数: {success_count} ({success_count/total_images*100:.1f}%)\n\n"
                               f"出力ファイル:\n{os.path.abspath(output_path)}")
            
            # UI状態の更新
            self.progress_label.config(text=f"処理完了 - 成功率: {success_count/total_images*100:.1f}%")
        
        except Exception as e:
            self.log(f"処理エラー: {str(e)}")
            messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{str(e)}")
        
        finally:
            # 処理状態をリセット
            self.processing = False
            self.start_button.config(state=tk.NORMAL)

def main():
    """アプリケーションのエントリーポイント"""
    root = tk.Tk()
    app = BatchExtractorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
