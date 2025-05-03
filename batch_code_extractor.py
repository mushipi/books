import os
import sys
import argparse
import json
import csv
import time
from datetime import datetime
from services.book_code_extractor import BookCodeExtractor

def process_folder(folder_path, use_ai=True, output_format="csv", output_path=None, verbose=False):
    """
    指定されたフォルダ内のすべてのJPEG画像を処理して書籍コードを抽出する
    
    Args:
        folder_path: 処理対象のフォルダパス
        use_ai: AIバックアップ認識を使用するかどうか
        output_format: 出力形式（csv, json, console）
        output_path: 出力ファイルパス（None の場合は自動生成）
        verbose: 詳細な出力を表示するかどうか
    
    Returns:
        tuple: (処理された画像数, 成功数, 出力ファイルパス)
    """
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"エラー: フォルダ '{folder_path}' が存在しないか、ディレクトリではありません。")
        return 0, 0, None
    
    # 出力ファイルパスの自動生成
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_format == "csv":
            output_path = f"book_codes_{timestamp}.csv"
        elif output_format == "json":
            output_path = f"book_codes_{timestamp}.json"
    
    # BookCodeExtractorの初期化
    try:
        extractor = BookCodeExtractor(use_ai_fallback=use_ai)
    except Exception as e:
        print(f"エラー: BookCodeExtractorの初期化に失敗しました: {e}")
        return 0, 0, None
    
    # JPEG/JPGファイルのみをフィルタリング
    image_files = []
    for file in os.listdir(folder_path):
        lower_file = file.lower()
        if lower_file.endswith(".jpg") or lower_file.endswith(".jpeg"):
            image_files.append(os.path.join(folder_path, file))
    
    if not image_files:
        print(f"警告: フォルダ '{folder_path}' にJPEG画像が見つかりませんでした。")
        return 0, 0, None
    
    total_images = len(image_files)
    print(f"処理対象の画像ファイル: {total_images}件")
    
    # 結果を格納するリスト
    results = []
    success_count = 0
    
    # CSVまたはJSONファイルの準備
    if output_format == "csv" and output_path:
        csv_file = open(output_path, 'w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        # ヘッダーの書き込み
        csv_writer.writerow([
            "ファイル名", "ISBNバーコード", "JANバーコード", 
            "ISBN文字列", "Cコード", "価格コード"
        ])
    elif output_format == "json" and output_path:
        json_results = []
    
    # 各画像ファイルを処理
    for index, image_path in enumerate(image_files):
        file_name = os.path.basename(image_path)
        if verbose:
            print(f"\n処理中 ({index+1}/{total_images}): {file_name}")
        else:
            progress = (index + 1) / total_images * 100
            sys.stdout.write(f"\r処理進捗: {progress:.1f}% ({index+1}/{total_images})")
            sys.stdout.flush()
        
        try:
            # 画像からコードを抽出
            start_time = time.time()
            extracted_codes = extractor.extract_codes_from_image(image_path)
            processing_time = time.time() - start_time
            
            # 結果の整形
            result = {
                "file_name": file_name,
                "isbn_barcode": extracted_codes.get("isbn_barcode"),
                "jan_barcode": extracted_codes.get("jan_barcode"),
                "isbn_text": extracted_codes.get("isbn_text"),
                "c_code": extracted_codes.get("c_code"),
                "price_code": extracted_codes.get("price_code"),
                "processing_time": f"{processing_time:.2f}秒"
            }
            results.append(result)
            
            # コードが一つでも抽出できた場合、成功としてカウント
            if any(extracted_codes.values()):
                success_count += 1
            
            # 出力形式に応じて結果を書き込み
            if output_format == "csv" and output_path:
                csv_writer.writerow([
                    file_name,
                    extracted_codes.get("isbn_barcode", ""),
                    extracted_codes.get("jan_barcode", ""),
                    extracted_codes.get("isbn_text", ""),
                    extracted_codes.get("c_code", ""),
                    extracted_codes.get("price_code", "")
                ])
            elif output_format == "json" and output_path:
                json_results.append({
                    "file_name": file_name,
                    "codes": extracted_codes
                })
            
            # 詳細モードの場合、処理結果を表示
            if verbose:
                print(f"  処理時間: {processing_time:.2f}秒")
                print(f"  ISBNバーコード: {extracted_codes.get('isbn_barcode')}")
                print(f"  JANバーコード: {extracted_codes.get('jan_barcode')}")
                print(f"  ISBN文字列: {extracted_codes.get('isbn_text')}")
                print(f"  Cコード: {extracted_codes.get('c_code')}")
                print(f"  価格コード: {extracted_codes.get('price_code')}")
        
        except Exception as e:
            print(f"\nエラー: ファイル '{file_name}' の処理中にエラーが発生しました: {str(e)}")
    
    # ファイルのクローズと出力
    if output_format == "csv" and output_path:
        csv_file.close()
    elif output_format == "json" and output_path:
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_results, json_file, ensure_ascii=False, indent=2)
    
    # 最終結果の表示
    print(f"\n\n処理完了!")
    print(f"処理された画像数: {total_images}")
    print(f"成功数: {success_count} ({success_count/total_images*100:.1f}%)")
    if output_path:
        print(f"出力ファイル: {os.path.abspath(output_path)}")
    
    return total_images, success_count, output_path

def main():
    """コマンドラインからの実行用エントリーポイント"""
    parser = argparse.ArgumentParser(description='フォルダ内のJPEG画像から書籍コードを抽出します')
    parser.add_argument('folder', help='処理するJPEG画像が格納されているフォルダパス')
    parser.add_argument('--no-ai', action='store_true', help='AIバックアップ認識を無効化します（処理が高速化しますが、精度が低下する可能性があります）')
    parser.add_argument('--format', choices=['csv', 'json', 'console'], default='csv', help='出力形式を指定します (デフォルト: csv)')
    parser.add_argument('--output', help='出力ファイルパスを指定します')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細な出力を表示します')
    
    args = parser.parse_args()
    
    process_folder(
        args.folder, 
        use_ai=not args.no_ai, 
        output_format=args.format, 
        output_path=args.output,
        verbose=args.verbose
    )

if __name__ == "__main__":
    main()
