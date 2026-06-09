### Git 仓库初始化与推送工具 GitLab 支持实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将`others/gh_repo_init_push.py`升级为支持 GitHub 和 GitLab 的通用交互式仓库初始化与推送工具，其中 GitHub 行为尽量保持不变，GitLab 新增支持`gitlab.com`与自建实例、namespace 和`internal`可见性。

**Architecture:** 采用“通用主流程 + 平台适配层”的单文件实现方式，先在`others/git_repo_init_push.py`中抽取共用的 Git 操作和交互逻辑，再为 GitHub 与 GitLab 封装最小平台差异。保留`others/gh_repo_init_push.py`作为兼容入口，避免破坏旧调用方式。

**Tech Stack:** Python 标准库，`subprocess`，`json`，`dataclasses`，`unittest`

### 文件结构

- Create: `others/git_repo_init_push.py`

- Modify: `others/gh_repo_init_push.py`

- Create: `tests/others/test_git_repo_init_push.py`

- Modify: `README.md`

### Task 1: 先补测试，锁定现有 GitHub 行为与新增 GitLab 分支

**Files:**

- Create: `tests/others/test_git_repo_init_push.py`

- [ ] **Step 1: 为纯函数和平台分支写测试**

```python
def test_build_lfs_patterns_groups_suffixes_and_plain_files(self) -> None:
    ...

def test_get_visibility_options_returns_internal_for_gitlab(self) -> None:
    ...

def test_parse_github_accounts_reads_active_login(self) -> None:
    ...
```

- [ ] **Step 2: 为 GitLab 关键流程写命令组装测试**

```python
def test_gitlab_create_remote_uses_hostname_and_namespace(self) -> None:
    ...

def test_gitlab_commit_email_falls_back_to_git_config_then_prompt(self) -> None:
    ...
```

- [ ] **Step 3: 运行测试，确认当前实现尚不满足**

Run: `python -m unittest tests.others.test_git_repo_init_push -v`

Expected: FAIL，提示目标模块或目标符号不存在

### Task 2: 新建通用主脚本并迁移 GitHub 现有实现

**Files:**

- Create: `others/git_repo_init_push.py`

- [ ] **Step 1: 复制并整理现有 GitHub 脚本骨架**

```python
class CommandError(RuntimeError):
    ...

@dataclass
class Account:
    ...

@dataclass
class Profile:
    ...
```

- [ ] **Step 2: 抽取通用主流程**

```python
def main() -> int:
    ensure_tool_exists('git')
    platform = prompt_platform()
    host = resolve_host(platform)
    ...
```

- [ ] **Step 3: 保持 GitHub 现有行为基本不变**

```python
def github_login_or_switch_account(host: str) -> LoginResult:
    ...

def github_get_profile(host: str) -> Profile:
    ...
```

- [ ] **Step 4: 运行测试，确认 GitHub 相关测试通过**

Run: `python -m unittest tests.others.test_git_repo_init_push -v`

Expected: GitHub 相关测试 PASS，GitLab 相关测试仍可能失败

### Task 3: 接入 GitLab 平台支持

**Files:**

- Modify: `others/git_repo_init_push.py`

- [ ] **Step 1: 新增 GitLab 平台适配能力**

```python
def gitlab_login_or_switch_account(host: str) -> LoginResult:
    ...

def gitlab_get_profile(host: str) -> Profile:
    ...

def gitlab_create_remote_repo(..., namespace: str) -> None:
    ...
```

- [ ] **Step 2: 新增 GitLab 主机、namespace 和可见性流程**

```python
def resolve_host(platform: str) -> str:
    ...

def prompt_namespace(profile: Profile, platform: str) -> str | None:
    ...
```

- [ ] **Step 3: 实现 GitLab 提交邮箱保守回退策略**

```python
def resolve_commit_email_for_gitlab(...) -> str:
    ...
```

- [ ] **Step 4: 运行测试，确认 GitLab 测试通过**

Run: `python -m unittest tests.others.test_git_repo_init_push -v`

Expected: PASS

### Task 4: 保留旧入口并补充文档

**Files:**

- Modify: `others/gh_repo_init_push.py`

- Modify: `README.md`

- [ ] **Step 1: 将旧脚本改为兼容入口**

```python
from others.git_repo_init_push import main

if __name__ == '__main__':
    raise SystemExit(main())
```

- [ ] **Step 2: 更新 README 工具说明**

```text
| [Git 仓库初始化与推送工具](others/git_repo_init_push.py) | 交互式完成 GitHub/GitLab 账号处理、本地仓库初始化、提交、创建远程仓库与推送；支持 GitLab 自建实例、namespace 与 Git LFS |
```

- [ ] **Step 3: 运行最终针对性测试**

Run: `python -m unittest tests.others.test_git_repo_init_push -v`

Expected: PASS

### Task 5: 做一次手工冒烟验证

**Files:**

- No file changes required

- [ ] **Step 1: 验证 GitHub 流程仍可进入平台选择并走原有路径**

Run: `python others/git_repo_init_push.py`

Expected: 能选择 GitHub，后续交互与原脚本基本一致

- [ ] **Step 2: 验证 GitLab 流程出现主机、namespace 和`internal`可见性**

Run: `python others/git_repo_init_push.py`

Expected: 选择 GitLab 后出现主机输入、namespace 输入与`public/internal/private`

- [ ] **Step 3: 验证旧入口仍可运行**

Run: `python others/gh_repo_init_push.py`

Expected: 能进入新主流程，并保持兼容提示或兼容行为
