#!/usr/bin/env bash
# 一键跑通：起 mock -> 跑用例并生成 allure 原始结果 -> 关 mock
set -e
cd "$(dirname "$0")"

python3 mock_api.py & MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null || true' EXIT

for _ in $(seq 1 20); do
  curl -s -o /dev/null "http://127.0.0.1:8899/health" && break
  sleep 0.3
done

python3 -m pytest --base-url http://127.0.0.1:8899 --alluredir=reports/allure-results "$@"

if command -v allure >/dev/null 2>&1; then
  allure generate reports/allure-results -o reports/allure-report --clean
  echo "report: reports/allure-report/index.html"
else
  echo "allure CLI 未安装，原始结果在 reports/allure-results"
fi
