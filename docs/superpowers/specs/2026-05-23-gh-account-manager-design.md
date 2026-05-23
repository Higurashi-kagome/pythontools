### gh 账号管理脚本设计

### 目标

提供一个独立的 Python 控制台脚本，交互式管理`github.com`上的 GitHub CLI 本地登录账号。

### 范围

- 查看当前`gh`已登录账号列表与活动账号

- 切换到某个已登录账号

- 通过浏览器登录一个新账号

- 删除某个本地保存的账号登录态

- 只操作`gh auth`，不修改 Git 全局配置，不处理 GitHub Enterprise

### 交互方案

脚本放在`others/gh_account_manager.py`，默认启动为主菜单循环。

主菜单提供以下操作：

- 查看账号状态

- 切换账号

- 登录新账号

- 删除账号

- 刷新状态

- 退出

交互层使用`questionary`，以减少手写输入校验逻辑。若环境尚未安装`questionary`，脚本应给出明确安装提示并退出，而不是直接抛出导入异常。

### 命令边界

账号状态读取使用：

```text
gh auth status --hostname github.com --json hosts
```

账号切换使用：

```text
gh auth switch --hostname github.com --user <login>
```

登录新账号使用：

```text
gh auth login --hostname github.com --git-protocol https --web --skip-ssh-key
```

删除账号使用：

```text
gh auth logout --hostname github.com --user <login>
```

### 数据解析

脚本不再解析`gh auth status`的人类可读文本，而是只解析 JSON 输出，降低因 CLI 文案变化导致的脆弱性。

状态对象至少保留以下字段：

- `login`

- `active`

- `state`

- `tokenSource`

- `gitProtocol`

- `scopes`

- `error`

### 错误处理

- 启动前检查`gh`命令是否存在

- 若未安装`questionary`，提示执行`pip install -r requirements.txt`

- 任一`gh`命令失败时，统一转换为简洁错误信息并返回菜单

- 删除账号前必须二次确认，并说明这只是删除本地登录态，不会吊销 GitHub 上的 token

### 测试

使用`unittest`，新增`tests/others/test_gh_account_manager.py`。

测试覆盖：

- `gh auth status` JSON 解析

- 切换账号命令参数

- 删除账号命令参数

- 新账号登录命令参数

- 缺少`questionary`时的失败路径
