### gh 账号管理脚本实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增一个交互式 Python 脚本，管理`github.com`上的`gh`本地账号登录态。

**Architecture:** 使用单文件 Python 脚本封装`gh`命令调用、JSON 状态解析和`questionary`交互菜单。核心逻辑保持为可单测的纯函数或薄封装，交互只放在`main()`和少量提示函数里。

**Tech Stack:** Python 标准库，`subprocess`，`json`，`dataclasses`，`unittest`，`questionary`

### 文件结构

- Create: `others/gh_account_manager.py`

- Create: `tests/others/test_gh_account_manager.py`

- Modify: `requirements.txt`

- Modify: `README.md`

### Task 1: 写失败测试并确认缺少实现

**Files:**

- Create: `tests/others/test_gh_account_manager.py`

- [ ] **Step 1: 写账号解析与命令调用测试**

```python
def test_parse_accounts_payload_reads_github_accounts(self) -> None:
    payload = {
        'hosts': {
            'github.com': [
                {'login': 'alice', 'active': True, 'state': 'success'},
                {'login': 'bob', 'active': False, 'state': 'success'},
            ],
        },
    }
    accounts = parse_accounts_payload(payload)
    self.assertEqual([account.login for account in accounts], ['alice', 'bob'])
```

- [ ] **Step 2: 运行测试，确认因缺少实现失败**

Run: `python -m unittest tests.others.test_gh_account_manager -v`

Expected: FAIL，提示`others.gh_account_manager`或目标符号不存在

### Task 2: 实现脚本最小可用版本

**Files:**

- Create: `others/gh_account_manager.py`

- [ ] **Step 1: 实现 JSON 解析与命令封装**

```python
def parse_accounts_payload(payload: dict[str, object]) -> list[Account]:
    ...

def read_accounts(command_runner=run_command) -> list[Account]:
    ...

def switch_account(login: str, command_runner=run_command) -> None:
    ...
```

- [ ] **Step 2: 实现`questionary`主菜单与动作分发**

```python
def main() -> int:
    ensure_tool_exists('gh')
    ensure_questionary_available()
    while True:
        accounts = read_accounts()
        action = prompt_main_action(accounts)
        ...
```

- [ ] **Step 3: 运行测试，确认通过**

Run: `python -m unittest tests.others.test_gh_account_manager -v`

Expected: PASS

### Task 3: 接入依赖与文档

**Files:**

- Modify: `requirements.txt`

- Modify: `README.md`

- [ ] **Step 1: 新增`questionary`依赖**

```text
questionary==2.1.1
```

- [ ] **Step 2: 在 README 中补充工具说明**

```text
| [GitHub CLI 账号管理工具](others/gh_account_manager.py) | 交互式查看、切换、登录和删除 github.com 上的本地 gh 账号 |
```

- [ ] **Step 3: 运行针对性测试完成收尾**

Run: `python -m unittest tests.others.test_gh_account_manager -v`

Expected: PASS
