"""本地 Mock 服务：让整套用例脱离外网即可跑通，用于作品演示与新人上手。

真实项目中这一步用你的测试环境地址替换即可，其余代码不用改。
"""

import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8899


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path, _, query = self.path.partition("?")

        if path == "/health":
            return self._json({"status": "ok", "ts": int(time.time())})

        if path == "/items":
            # 模拟真实系统里偶发的下游超时，用来验证用例的错误分支与自愈断言
            if "fail=1" in query:
                return self._json({"code": 500, "msg": "upstream timeout"}, 503)
            return self._json(
                {"code": 0, "msg": "ok", "total": 2, "data": [{"id": 1, "name": "sku-A"}, {"id": 2, "name": "sku-B"}]}
            )

        self._json({"code": 404, "msg": "route not found", "path": path}, 404)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"mock api listening on http://127.0.0.1:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
