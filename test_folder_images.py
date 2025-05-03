import os
import sys
import base64
import json
import requests
import argparse
import time
from datetime import datetime
import traceback
from pprint import pprint

def test_folder_images(folder_path, api_key="AIzaSyBa1QVKJWaE0tmVIMeyO-1x4q6Q1-Njmdk", output_file=None):
    """
    フォルダ内の画像をすべてテストする
    
    Args:
        folder_path: テスト対象の画像が含まれるフォルダパス
        api_key: Gemini APIのAPIキー
        output_file: 結果を保存するファイルパス（オプション）
    """
    # フォルダの存在チェック
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"エラー: フォルダ {folder_path} が見つからないか、ディレクトリではありません")
        return
    
    # 出力ファイルの準備
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"image_test_results_{timestamp}.txt"
    
    # 結果を格納するリスト
    results = []
    
    # JPEG画像を検索
    image_files = []
    for file in os.listdir(folder_path):
        lower_file = file.lower()
        if lower_file.endswith('.jpg') or lower_file.endswith('.jpeg'):
            image_files.append(os.path.join(folder_path, file))
    
    if not image_files:
        print(f"フォルダ {folder_path} にJPEG画像が見つかりませんでした")
        return
    
    print(f"フォルダ内に {len(image_files)} 件の画像が見つかりました")
    
    # 各画像の処理
    for i, image_path in enumerate(image_files):
        print(f"\n処理中 [{i+1}/{len(image_files)}]: {os.path.basename(image_path)}")
        print("-" * 50)
        
        # 処理時間の計測
        start_time = time.time()
        
        result = {
            'file_name': os.path.basename(image_path),
            'path': image_path,
            'success': False,
            'error': None,
            'api_response': None,
            'extracted_data': None,
            'processing_time': 0
        }
        
        try:
            # 画像ファイルのチェック
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"ファイル {image_path} が見つかりません")
            
            # 画像のメタデータ
            file_size = os.path.getsize(image_path) / 1024  # KB
            result['file_size'] = f"{file_size:.2f} KB"
            print(f"ファイルサイズ: {file_size:.2f} KB")
            
            # 画像ファイルをBase64エンコード
            with open(image_path, 'rb') as img_file:
                encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
            
            # APIエンドポイント
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={api_key}"
            
            # APIリクエストの作成
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": """
                                この本の裏表紙の画像から以下の情報を抽出してください：
                                1. ISBNコード（ISBN978-x-xx-xxxxxx-x形式）
                                2. JANコード（バーコード下の13桁の数字）
                                3. Cコード（Cxxxx形式）
                                4. 価格表示（¥xxxE形式）
                                
                                以下のJSON形式で回答してください：
                                {
                                    "isbn_text": "ISBN978-x-xx-xxxxxx-x",
                                    "jan_barcode": "9784xxxxxxxxx",
                                    "c_code": "Cxxxx",
                                    "price_code": "¥xxxE"
                                }
                                
                                情報が見つからない場合はnullと表示してください。
                                JSONのみを出力してください。説明文は不要です。
                                """
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": encoded_image
                                }
                            }
                        ]
                    }
                ],
                "generation_config": {
                    "temperature": 0.0,
                    "top_p": 0.95,
                    "max_output_tokens": 1024
                }
            }
            
            print("APIリクエスト送信中...")
            
            # APIリクエストの送信
            response = requests.post(
                api_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30  # タイムアウトを30秒に設定
            )
            
            # エラー処理
            if response.status_code != 200:
                error_message = f"APIエラー: {response.status_code} - {response.text}"
                print(error_message)
                result['error'] = error_message
                results.append(result)
                continue
            
            print("APIレスポンス受信")
            
            # レスポンスの解析
            response_data = response.json()
            response_text = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '{}')
            
            # APIレスポンスを保存
            result['api_response'] = response_text
            
            # JSON部分を抽出
            import re
            json_text = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_text:
                extracted_data = json.loads(json_text.group(0))
                result['extracted_data'] = extracted_data
                result['success'] = True
                
                print("JSON解析成功:")
                pprint(extracted_data)
            else:
                error_message = "JSONが見つかりませんでした"
                print(error_message)
                result['error'] = error_message
            
        except Exception as e:
            error_message = f"処理エラー: {str(e)}"
            print(error_message)
            print(traceback.format_exc())
            result['error'] = error_message
        
        # 処理時間を記録
        processing_time = time.time() - start_time
        result['processing_time'] = f"{processing_time:.2f}秒"
        print(f"処理時間: {processing_time:.2f}秒")
        
        # 結果を格納
        results.append(result)
        
        # 出力ファイルに結果を書き込み（逐次保存）
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"ファイル: {result['file_name']}\n")
            f.write(f"処理時間: {result['processing_time']}\n")
            f.write(f"成功: {result['success']}\n")
            
            if result['error']:
                f.write(f"エラー: {result['error']}\n")
            
            if result['extracted_data']:
                f.write("抽出データ:\n")
                for key, value in result['extracted_data'].items():
                    f.write(f"  {key}: {value}\n")
            
            f.write(f"APIレスポンス:\n{result['api_response']}\n")
    
    # 結果の概要
    success_count = sum(1 for r in results if r['success'])
    print(f"\n処理完了!")
    print(f"処理画像数: {len(image_files)}")
    print(f"成功数: {success_count}")
    print(f"失敗数: {len(image_files) - success_count}")
    print(f"結果ファイル: {os.path.abspath(output_file)}")
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='フォルダ内の画像をすべてテストする')
    parser.add_argument('folder_path', help='テスト対象の画像が含まれるフォルダパス')
    parser.add_argument('--api-key', default="AIzaSyBa1QVKJWaE0tmVIMeyO-1x4q6Q1-Njmdk", help='Gemini APIのAPIキー')
    parser.add_argument('--output', help='結果を保存するファイルパス')
    
    args = parser.parse_args()
    test_folder_images(args.folder_path, args.api_key, args.output)
