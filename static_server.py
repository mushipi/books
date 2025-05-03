import http.server
import socketserver
import os

# HTTPサーバーの設定
PORT = 8000
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

if __name__ == "__main__":
    print(f"静的ファイルサーバーを起動: http://localhost:{PORT}")
    print(f"サービングディレクトリ: {DIRECTORY}")
    print("Ctrl+Cで停止します")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nサーバーを停止します")
