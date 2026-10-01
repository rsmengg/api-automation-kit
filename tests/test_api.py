import pytest


@pytest.mark.smoke
def test_health_check(session, base_url):
    """冒烟：服务活着，且字段结构没漂。"""
    r = session.get(f"{base_url}/health", timeout=5)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"status", "ts"}
    assert body["status"] == "ok"


@pytest.mark.regression
def test_list_items(session, base_url):
    """回归：列表接口返回结构契约稳定。"""
    r = session.get(f"{base_url}/items", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["total"] == len(body["data"])
    assert {item["id"] for item in body["data"]} == {1, 2}


@pytest.mark.regression
def test_upstream_error_is_surfaced_not_swallowed(session, base_url):
    """异常分支：下游 503 时接口要返回结构化错误码，而不是 200 空壳。"""
    r = session.get(f"{base_url}/items?fail=1", timeout=5)
    assert r.status_code == 503
    body = r.json()
    assert body["code"] == 500 and body["msg"] == "upstream timeout"

    # 下游恢复后同一条链路必须立刻可用，避免错误状态被缓存
    recovered = session.get(f"{base_url}/items", timeout=5)
    assert recovered.status_code == 200


def test_unknown_route_returns_404_payload(session, base_url):
    """边界：未知路由的响应也是约定结构，前端可以去重而不是崩。"""
    r = session.get(f"{base_url}/not-exist", timeout=5)
    assert r.status_code == 404
    assert r.json()["code"] == 404
