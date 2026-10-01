"""全局夹具：环境地址、会话、失败产物自动落盘。

设计原则：失败排查用的钩子**绝不能自己抛异常**，否则一条用例挂掉会拖垮整个套件。
"""

import json
import os
import traceback

import pytest
import requests

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

# 最近一次HTTP调用的信息，供失败落盘使用
_LAST_CALL = {"method": "", "url": "", "status": ""}


def _record_response(resp, *args, **kwargs):
    try:
        _LAST_CALL["method"] = resp.request.method
        _LAST_CALL["url"] = resp.request.url
        _LAST_CALL["status"] = resp.status_code
    except Exception:
        pass


def _safe_write(path, content, limit=None):
    try:
        if limit is not None and isinstance(content, str) and len(content) > limit:
            content = content[:limit] + "\n...[truncated]"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as exc:  # 落盘失败不能影响用例本身
        print(f"[warn] write {path} failed: {exc}")


def pytest_addoption(parser):
    parser.addoption("--base-url", default="http://127.0.0.1:8899", help="被测环境地址")
    parser.addoption("--out", default=REPORT_DIR, help="用例产物目录")


@pytest.fixture(scope="session")
def base_url(request):
    return request.config.getoption("--base-url")


@pytest.fixture(scope="session")
def out_dir(request):
    return request.config.getoption("--out")


@pytest.fixture(scope="session")
def session():
    """连接池复用 + 记录请求元信息，比每次 new 一个 requests 对象更接近真实项目。"""
    s = requests.Session()
    s.headers.update({"User-Agent": "api-automation-kit/1.0", "Accept": "application/json"})
    # 关键：企业网络常把 127.0.0.1 也走代理，会导致本地用例报 502
    # 对测试环境地址（非 localhost）想走代理时，把下面这行注释掉即可
    s.trust_env = False
    s.hooks["response"] = [_record_response]
    yield s
    s.close()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """用例失败时落盘：请求元信息 / 断言错误 / 完整 traceback，排查不用再抓包。"""
    if call.excinfo is None:
        return
    try:
        base = os.path.join(item.config.getoption("--out"), "failed-cases", item.nodeid.replace("/", "_"))
        os.makedirs(base, exist_ok=True)
        _safe_write(os.path.join(base, "request.txt"),
                    f"{_LAST_CALL['method']} {_LAST_CALL['url']}\nstatus: {_LAST_CALL['status']}\n")
        _safe_write(os.path.join(base, "error.txt"), str(call.excinfo))
        _safe_write(os.path.join(base, "report.json"),
                    json.dumps({"nodeid": item.nodeid,
                                "error": str(call.excinfo),
                                "traceback": traceback.format_exc()},
                               ensure_ascii=False, indent=2), limit=20000)
    except Exception as exc:
        print(f"[warn] dump failed-case failed: {exc}")
