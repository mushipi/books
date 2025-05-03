import os
import json
import glob
import google.generativeai as genai
import time

# APIキーとモデル名
API_KEY = "AIzaSyAM_oZf_yZLe5aR0Ytr0A2UTCp2SIx6kAA"
MODEL_NAME = "gemini-1.5-flash"

# 画像ディレクトリと出力ディレクトリ
IMAGE_DIR = r"C:\Users\lovet\sauce\book_manager\pic"
OUTPUT_DIR = r"C:\Users\lovet\sauce\book_manager\results"

# プロンプト
PROMPT = """
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

def extract_book_info(image_path):
    try:
        # 画像ファイルをバイナリで読み込み
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # モデル呼び出し
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(
            [
                PROMPT,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ]
        )

        # レスポンスからJSON部分を抽出
        response_text = response.text.strip()
        try:
            # そのままJSONとしてロード
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # JSON部分だけ抜き出し
            import re
            match = re.search(r'({[\s\S]*})', response_text)
            if match:
                result = json.loads(match.group(1))
            else:
                result = {
                    "isbn_text": None,
                    "jan_barcode": None,
                    "c_code": None,
                    "price_code": None,
                    "error": "JSONが見つかりませんでした"
                }
        # エラーキーがなければ追加
        if "error" not in result:
            result["error"] = None
        return result

    except Exception as e:
        error_msg = str(e)
        if "deprecated" in error_msg.lower():
            error_msg += "\nモデル名が正しいか最新のドキュメントを確認してください"
        return {
            "isbn_text": None,
            "jan_barcode": None,
            "c_code": None,
            "price_code": None,
            "error": error_msg
        }

def main():
    # API初期化
    genai.configure(api_key=API_KEY)

    # 出力ディレクトリ作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 画像ファイル一覧取得
    image_files = glob.glob(os.path.join(IMAGE_DIR, "*.jpg")) + glob.glob(os.path.join(IMAGE_DIR, "*.jpeg"))

    for image_path in image_files:
        print(f"処理中: {image_path}")
        info = extract_book_info(image_path)
        # ファイル名から拡張子を除去し、出力ファイル名作成
        base = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{base}_info.json")
        # JSON保存
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        print(f"結果を保存しました: {output_path}")
        print(json.dumps(info, ensure_ascii=False, indent=2))
        print("-" * 50)
        time.sleep(1)  # API制限対策

if __name__ == "__main__":
    main()
