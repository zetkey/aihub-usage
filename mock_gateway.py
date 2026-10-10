#!/usr/bin/env python3
"""Mock Scala AI Gateway (new-api) — meniru response asli sesuai sumber Go new-api.
Dipakai hanya untuk menguji parsing/format aihub-usage tanpa memakai credit asli."""
import gzip
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEY = "sk-testkey123"
BLANK = str()   # id kosong (new-api kadang mengirim entri tanpa id)
QPU = 500_000
SUB = {"object": "billing_subscription", "has_payment_method": True, "canceled": False,
       "soft_limit_usd": 12.3456, "hard_limit_usd": 12.3456,
       "system_hard_limit_usd": 12.3456, "access_until": 0}
USAGE = {"object": "list", "total_usage": 123.45}          # cent -> $1.2345
TOKEN = {"code": True, "message": "ok", "data": {
    "object": "token_usage", "name": "prod-hermes",
    "total_granted": 0, "total_used": 617_250, "total_available": 0,
    "unlimited_quota": True, "model_limits": {}, "model_limits_enabled": False,
    "expires_at": 0}}
TOKEN_LIMITED = {"code": True, "message": "ok", "data": {
    "object": "token_usage", "name": "kontraktor-1",
    "total_granted": 2_500_000, "total_used": 1_000_000, "total_available": 1_500_000,
    "unlimited_quota": False, "model_limits": {"gpt-5.5": True, "claude-sonnet-5.5": True},
    "model_limits_enabled": True, "expires_at": 1791458302}}
LOGS = {"success": True, "message": "", "data": [
    {"id": 9002, "type": 5, "created_at": 1791458402, "token_name": "prod-hermes",
     "request_id": "202610090001580000000005REQ9002",
     "model_name": "", "quota": 0, "prompt_tokens": 0, "completion_tokens": 0,
     "use_time": 2, "group": "auto", "content": "upstream timeout"},
    {"id": 9001, "type": 2, "created_at": 1791458302, "token_name": "prod-hermes",
     "request_id": "202610090001440000000002REQ9001",
     "model_name": "gpt-5.5", "quota": 12_500, "prompt_tokens": 1200,
     "completion_tokens": 340, "use_time": 4, "is_stream": True, "group": "auto"},
    {"id": 9000, "type": 2, "created_at": 1791454702, "token_name": "prod-hermes",
     "request_id": "202610082311000000000002REQ9000",
     "model_name": "deepseek-v4.1-flash", "quota": 5_000, "prompt_tokens": 800,
     "completion_tokens": 100, "use_time": 3, "group": "auto"},
    {"id": 8999, "type": 6, "created_at": 1791454702, "token_name": "prod-hermes",
     "request_id": "202610082311000000000006REQ8999",
     "model_name": "", "quota": 0, "prompt_tokens": 0, "completion_tokens": 0,
     "use_time": 1, "group": "auto"}]}
MODELS = {'object': 'list', 'data': [{'id': 'gpt-5.5'}, {'id': ''}, {'id': 'deepseek-v4.1-flash'}]}
STATUS = {"data": {"system_name": "metranet AI", "version": "2576fe9",
                   "quota_per_unit": QPU, "quota_display_type": "USD",
                   "currency_rates": {"USD": 1, "CNY": 7, "IDR": 18000},
                   "docs_link": "/docs/"}}

LIMITED = False
# --anykey: terima bearer token apa pun (untuk menguji scope arsip per key)
ANYKEY = False
# --redirect PORT: /v1/models membalas 302 ke server lain (uji kebocoran header)
REDIRECT_PORT = None
# --record-auth PATH: catat header Authorization yang diterima ke file
RECORD_AUTH = None
# --gzip: balas dengan Content-Encoding: gzip bila client menerimanya
GZIP = False
# --concurrency PATH: catat jumlah request bersamaan (puncak) ke file
CONCURRENCY_PATH = None
INFLIGHT = 0
INFLIGHT_MAX = 0
INFLIGHT_LOCK = threading.Lock()
# --delay MS: tahan setiap respons selama MS milidetik (agar tumpang-tindih
# request paralel bisa terukur)
DELAY_MS = 0
# --counts PATH: catat jumlah request per path (JSON) ke file
COUNTS_PATH = None
COUNTS = {}
COUNTS_LOCK = threading.Lock()
# --errlog: /api/log/token membalas HTTP 200 + {"success":false} seperti
# common.ApiError new-api saat handler gagal.
ERRLOG = False
# --emptylogs: /api/log/token sukses tapi belum ada baris log
EMPTY_LOGS = False
# --emptychoices: /v1/chat/completions tanpa entri `choices`
EMPTY_CHOICES = False
# --posids: `id` = nomor urut jendela (1 = terbaru), meniru perilaku gateway
# asli aihub.metranet.co.id — id berubah tiap fetch, hanya request_id yang stabil
POSIDS = False


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj, code=200, extra=None):
        b = json.dumps(obj).encode()
        enc = None
        if GZIP and self.headers.get("Accept-Encoding", "").find("gzip") >= 0:
            b = gzip.compress(b)
            enc = "gzip"
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        if enc:
            self.send_header("Content-Encoding", enc)
        for k, v in (extra or dict()).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        global INFLIGHT, INFLIGHT_MAX
        if CONCURRENCY_PATH:
            with INFLIGHT_LOCK:
                INFLIGHT += 1
                if INFLIGHT > INFLIGHT_MAX:
                    INFLIGHT_MAX = INFLIGHT
                peak = INFLIGHT_MAX
            try:
                self._handle_get()
            finally:
                with INFLIGHT_LOCK:
                    INFLIGHT -= 1
                    peak = INFLIGHT_MAX
                with open(CONCURRENCY_PATH, "w") as f:
                    f.write("%d\n" % peak)
            return
        return self._handle_get()

    def _handle_get(self):
        if DELAY_MS:
            time.sleep(DELAY_MS / 1000.0)
        if self.path.split("?")[0] == "/__reset":
            # dipakai test untuk membuang hitungan probe kesiapan
            with COUNTS_LOCK:
                COUNTS.clear()
                if COUNTS_PATH and os.path.exists(COUNTS_PATH):
                    os.remove(COUNTS_PATH)
            return self._send({"ok": True})
        if COUNTS_PATH:
            with COUNTS_LOCK:
                p0 = self.path.split("?")[0]
                COUNTS[p0] = COUNTS.get(p0, 0) + 1
                with open(COUNTS_PATH, "w") as f:
                    json.dump(COUNTS, f)
        auth = self.headers.get("Authorization", "")
        if RECORD_AUTH:
            with open(RECORD_AUTH, "a") as f:
                f.write("AUTH=%r\n" % (self.headers.get("Authorization")))
        p = self.path.split("?")[0]
        if p == "/api/status":
            return self._send(STATUS)
        if REDIRECT_PORT and p == "/v1/models":
            return self._send({"data":[]}, 302,
                              {"Location": "http://127.0.0.1:%d/v1/models" % REDIRECT_PORT})
        if auth != "Bearer " + KEY and not ANYKEY:
            return self._send({"error": {"message": "Invalid token", "type": "new_api_error"}}, 401)
        if p in ("/v1/dashboard/billing/subscription", "/dashboard/billing/subscription"):
            return self._send(SUB)
        if p in ("/v1/dashboard/billing/usage", "/dashboard/billing/usage"):
            return self._send(USAGE)
        if p == "/api/usage/token/":
            return self._send(TOKEN_LIMITED if LIMITED else TOKEN)
        if p == "/api/log/token":
            if ERRLOG:
                return self._send({"success": False,
                                   "message": "获取日志失败"}, 200)
            if EMPTY_LOGS:
                return self._send({"success": True, "message": "", "data":[]})
            data = LOGS["data"]
            if POSIDS:
                # id terus berganti tiap fetch (1 = terbaru) tapi request_id tetap
                data = [dict(l, id=len(data) - i) for i, l in enumerate(data)]
            return self._send({"success": True, "message": "", "data": data})
        if p == "/v1/models":
            return self._send(MODELS)
        return self._send({"error": {"message": "Invalid URL (GET %s)" % p,
                                     "type": "invalid_request_error"}}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"")
        p = self.path.split("?")[0]
        if p == "/v1/chat/completions":
            choices = []
            if not EMPTY_CHOICES:
                choices = [{"index": 0,
                            "message": {"role": "assistant", "content": "hi"}}]
            return self._send({"id": "chatcmpl-1", "model": body.get("model"),
                               "choices": choices,
                               "usage": {"prompt_tokens": 3, "completion_tokens": 1}})
        if p == "/v1/messages":
            return self._send({"id": "msg_1", "model": body.get("model"),
                               "content": [{"type": "text", "text": "hi"}],
                               "usage": {"input_tokens": 3, "output_tokens": 1}})
        return self._send({"error": {"message": "Invalid URL"}}, 404)


if __name__ == "__main__":
    import sys
    LIMITED = "--limited" in sys.argv
    ANYKEY = "--anykey" in sys.argv
    if "--redirect" in sys.argv:
        REDIRECT_PORT = int(sys.argv[sys.argv.index("--redirect") + 1])
    if "--record-auth" in sys.argv:
        RECORD_AUTH = sys.argv[sys.argv.index("--record-auth") + 1]
    GZIP = "--gzip" in sys.argv
    if "--counts" in sys.argv:
        COUNTS_PATH = sys.argv[sys.argv.index("--counts") + 1]
    if "--delay" in sys.argv:
        DELAY_MS = int(sys.argv[sys.argv.index("--delay") + 1])
    if "--concurrency" in sys.argv:
        CONCURRENCY_PATH = sys.argv[sys.argv.index("--concurrency") + 1]
    ERRLOG = "--errlog" in sys.argv
    EMPTY_LOGS = "--emptylogs" in sys.argv
    EMPTY_CHOICES = "--emptychoices" in sys.argv
    POSIDS = "--posids" in sys.argv
    port = int(sys.argv[1]) if sys.argv[1:2] and sys.argv[1].isdigit() else 8791
    # ThreadingHTTPServer: CLI memanggil endpoint secara paralel, jadi mock harus
    # bisa melayani request bersamaan (kalau tidak, paralelisme tidak terukur).
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
