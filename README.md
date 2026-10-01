# 接口自动化回归套件（API Regression Kit）

一个**开箱即用、带 CI、带报告、带失败排查产物**的接口自动化骨架。
不是 demo 片段，是一套能直接塞进你们仓库、周末配好周一就能跑的整套东西。

## 它替你省什么

| 现状痛点 | 这套东西给的解 |
| --- | --- |
| 每次发版靠人工点一遍接口，两三个人日 | 一条命令跑完全量，`pytest --base-url https://你的环境` |
| 用例挂了只知道"红了"，不知道挂在哪一步 | 失败自动落盘 request / 响应 / trace，不用再抓包 |
| 报告是控制台一屏绿点，给老板看不了 | Allure 报告：用例树、耗时、失败截图、历史趋势 |
| 用例每次手改域名、token | 全部走 `--base-url` 与 fixtures，换环境只改一个参数 |
| 回归靠"记得跑"，忘了就漏 | GitHub Actions / Jenkins 提交即跑，跑完上传 Artifact |
| 新人不会写用例，风格五花八门 | 示例用例即规范，照抄即可 |

**典型规模换算**：50 个接口 × 平均 3 个断言场景 ≈ 150 条用例，人工回归约 2 人日/轮；
自动化跑完约 3–8 分钟。按一周两轮算，**每月省下约 12–16 个人日**。

## 快速开始

```bash
pip install -r requirements.txt
bash run.sh                       # 起本地 mock + 跑用例 + 生成 Allure 报告
```

只想对着你们真实环境跑：

```bash
python3 -m pytest --base-url https://your-env.example.com --alluredir=reports/allure-results
```

结果文件：

```
reports/failed-cases/<用例名>/error.txt      # 失败原因
reports/failed-cases/<用例名>/request.txt    # 请求方法 + 地址
reports/failed-cases/<用例名>/report.json    # 完整 traceback
```

## 目录结构

```
.
├── mock_api.py                  # 本地 mock，脱离外网也能演示
├── conftest.py                  # 环境参数、连接池、失败产物落盘
├── pytest.ini                   # 用例收集与 marker 规范
├── requirements.txt
├── run.sh                       # 一键运行 + 报告生成
├── .github/workflows/ci.yml     # 提交即跑的 CI
└── tests/
    └── test_api.py              # 示例用例（即写法规范）
    └── ...
```

## 交付清单（接单时可直接引用进需求）

1. 用例目录与命名规范
2. 全量 / 冒烟两档执行，或按 tag 筛选（`pytest -m smoke`）
3. Allure 报告 + 失败自动落盘
4. CI 流水线（GitHub Actions / Jenkins / GitLab CI 任选）
5. 一份《用例维护手册》，新人照着加用例
6. 首轮交付附一份《接口风险清单》：哪些接口值得自动化、哪些不适合

## 不适用 / 需要商量的场景

诚实说明这套骨架的边界，避免交付翻车：

- 纯前端页面逻辑它覆盖不到，需要接 UI 自动化（Playwright）
- 强依赖真实第三方支付、短信网关的接口，需要你们提供沙箱环境，否则只能打桩
- 涉及**生产环境真实数据**的接口，我们不碰，只在测试/预发环境执行

## 已知的踩坑点（已处理）

- **本地 127.0.0.1 被代理劫持** → 企业网络常见，`requests` 会把本地请求也送代理导致 502。
  会话里已设 `session.trust_env = False`；若你的测试环境地址在公司代理后面，
  把 `conftest.py` 里那行注释掉即可恢复走代理。
- **失败钩子自己炸了** → 落盘全部包在 try/except 里，写文件失败绝不影响用例本身。

## 技术选型

Python 3.11 · pytest 8 · requests · Allure · GitHub Actions（CI 可换）

## 商用声明

本项目脱敏自真实零售/电商系统的接口回归实践，不含任何真实业务域名、密钥、接口文档。
可自由使用、二次开发；如用于商业交付，建议保留此说明段落。
