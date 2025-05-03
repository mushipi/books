import os
import json
import re
import time
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME

class BookCodeExtractor:
    def __init__(self, api_key=None, model_name=None):
        """
        書籍コード抽出機能の初期化
        
        Args:
            api_key: Gemini APIのAPIキー（Noneの場合は環境変数またはconfigから取得）
            model_name: 使用するGeminiモデル名
        """
        # APIキーの取得（優先順位: 引数 > 環境変数 > config）
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY
        self.model_name = model_name or os.environ.get("GEMINI_MODEL_NAME") or GEMINI_MODEL_NAME
        
        # APIが利用可能かどうか
        self.api_available = bool(self.api_key)
        
        # APIが利用可能な場合は初期化
        if self.api_available:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.genai = genai
                self.api_initialized = True
            except ImportError:
                print("警告: google.generativeaiライブラリがインストールされていません。pip install google-generativeaiを実行してください。")
                self.api_initialized = False
            except Exception as e:
                print(f"警告: Gemini APIの初期化中にエラーが発生しました: {str(e)}")
                self.api_initialized = False
        else:
            self.api_initialized = False
            
        # プロンプトテンプレート
        self.prompt_template = """
この本の裏表紙の画像から以下の情報を抽出してください：
1. ISBNコード（ISBN978-x-xx-xxxxxx-x形式）
2. JANコード（バーコード下の13桁の数字,9784xxxxxxxx形式,バーコードは2つある場合もあるので、形式に適合する数列のみを抽出）
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

    def extract_from_image(self, image_path):
        """
        画像から書籍コード情報を抽出
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            辞書形式で各種コード情報（抽出失敗時はNone）
        """
        try:
            # ローカルバーコード検出を試みる
            # TODO: pyzbarとOpenCVを使ったローカル検出機能を実装
            # local_result = self._extract_with_local(image_path)
            # if local_result.get("jan_barcode"):
            #     return local_result
            
            # ローカル処理で失敗したら、APIを使用
            if self.api_available and self.api_initialized:
                return self._extract_with_api(image_path)
            else:
                return {
                    "isbn_text": None,
                    "jan_barcode": None,
                    "c_code": None,
                    "price_code": None,
                    "error": "APIキーが設定されていないか、ライブラリが正しく初期化されていません"
                }
                
        except Exception as e:
            return {
                "isbn_text": None,
                "jan_barcode": None,
                "c_code": None,
                "price_code": None,
                "error": str(e)
            }
    
    def _extract_with_api(self, image_path):
        """APIを使用して画像から情報を抽出"""
        # 画像ファイルをバイナリで読み込み
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # モデル呼び出し
        try:
            model = self.genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                [
                    self.prompt_template,
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
    
    def _extract_with_local(self, image_path):
        """ローカル処理で画像から情報を抽出（未実装）"""
        # TODO: pyzbarとOpenCVを使用したバーコード検出を実装
        return {
            "isbn_text": None,
            "jan_barcode": None,
            "c_code": None,
            "price_code": None,
            "error": "ローカル処理は未実装です"
        }
