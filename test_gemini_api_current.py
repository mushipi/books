import os
import sys
import base64
import json
import requests
import argparse
from pprint import pprint

def test_gemini_api(image_path, api_key="AIzaSyAM_oZf_yZLe5aR0Ytr0A2UTCp2SIx6kAA"):
    """
    現在のロジックでGemini APIを使用して書籍画像からコードを抽出するテスト
    
    Args:
        image_path: テストする画像のパス
        api_key: Gemini APIのAPIキー
    """
    print(f"画像ファイル: {image_path}")
    print("-" * 50)
    
    # 画像ファイルのチェック
    if not os.path.exists(image_path):
        print(f"エラー: ファイル {image_path} が見つかりません")
        return
    
    try:
        # 画像ファイルをBase64エンコード
        with open(image_path, 'rb') as img_file:
            encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
        
        print(f"ファイルサイズ: {os.path.getsize(image_path) / 1024:.2f} KB")
        print(f"Base64エンコード成功")
        
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
            json=payload
        )
        
        # エラー処理
        if response.status_code != 200:
            print(f"APIエラー: {response.status_code} - {response.text}")
            return
        
        print("APIレスポンス受信")
        print(f"ステータスコード: {response.status_code}")
        
        # レスポンスの解析
        response_data = response.json()
        response_text = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '{}')
        
        print("\n--- APIレスポンス原文 ---")
        print(response_text)
        print("--- 解析結果 ---")
        
        # JSON部分を抽出
        import re
        json_text = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_text:
            try:
                extracted_data = json.loads(json_text.group(0))
                print("JSON解析成功:")
                pprint(extracted_data)
            except json.JSONDecodeError as e:
                print(f"JSON解析エラー: {e}")
                print("元のテキスト:")
                print(json_text.group(0))
        else:
            print("JSONが見つかりませんでした")
        
    except Exception as e:
        print(f"処理エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gemini APIを使用した書籍コード認識のテスト')
    parser.add_argument('image_path', help='テストする画像のパス')
    parser.add_argument('--api-key', default="AIzaSyAM_oZf_yZLe5aR0Ytr0A2UTCp2SIx6kAA", help='Gemini APIのAPIキー')
    
    args = parser.parse_args()
    test_gemini_api(args.image_path, args.api_key)
