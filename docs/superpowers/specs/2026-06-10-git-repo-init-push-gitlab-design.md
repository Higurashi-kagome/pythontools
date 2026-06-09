### 背景

现有`others/gh_repo_init_push.py`是一个面向 GitHub 的交互式工具，负责完成账号切换、本地 Git 仓库初始化、提交身份配置、大文件 Git LFS 处理、创建远程仓库并推送。

当前需求是在尽量保持 GitHub 现有行为稳定的前提下，为该工具增加 GitLab 支持。GitLab 需要兼容`gitlab.com`和自建 GitLab，优先复用`glab`的当前登录上下文和 CLI 能力。用户允许为了支持多平台而对脚本做小幅通用化调整，例如在开始时先选择平台，也允许将文件从 GitHub 专属命名重命名为通用命名。

### 目标

新增一个通用的 Git 仓库初始化与推送工具，同时支持 GitHub 和 GitLab，并满足以下目标：

- GitHub 相关流程尽量保持不变，降低回归风险

- GitLab 支持`gitlab.com`和自建实例

- GitLab 优先使用`glab`当前登录上下文进行账号切换、资料获取和仓库创建

- 本地 Git 初始化、提交身份配置、LFS、大文件处理、提交和推送逻辑尽量复用

- 工具保持交互式使用方式，不引入命令行参数依赖

### 非目标

本次设计不包含以下内容：

- 不支持除 GitHub 和 GitLab 之外的代码托管平台

- 不新增 SSH 登录流程，仍沿用当前基于`gh/glab` CLI 的默认协议能力

- 不支持复杂的批量仓库创建或非交互式自动化调用

- 不重写现有工具为多文件大型框架，保持在当前仓库工具脚本风格内

### 设计原则

- GitHub 保守兼容：已有交互项、行为和回退策略尽量不变

- GitLab 增量增强：仅在 GitLab 平台下引入主机、namespace、internal 可见性等差异能力

- 差异隔离：把平台差异集中在适配层，避免主流程散落条件分支

- 用户可诊断：依赖缺失、账号状态异常、邮箱无法确定等问题要明确提示

### 总体方案

建议将主脚本重命名为`others/git_repo_init_push.py`，并保留`others/gh_repo_init_push.py`作为兼容入口。

整体采用“两层结构”：

- 通用主流程层

  - 负责平台选择、仓库路径输入、Git 初始化、LFS 检测、提交、推送、摘要打印和错误处理

- 平台适配层

  - 负责 GitHub 和 GitLab 在 CLI、账号管理、资料获取、仓库创建、可见性和清理上的差异

这种结构允许 GitHub 分支尽量复用现有实现，同时把 GitLab 差异收敛在少量明确接口中。

### 文件与兼容策略

建议引入如下文件布局：

- `others/git_repo_init_push.py`

  - 新的通用主脚本，承载 GitHub 与 GitLab 支持

- `others/gh_repo_init_push.py`

  - 兼容入口，保留原文件名

兼容入口的职责仅有两项：

- 告知用户该工具已经升级为支持 GitHub/GitLab 的通用版本

- 复用新脚本的主入口，保持旧调用方式可继续使用

这样既能完成命名抽象，也不会打断当前使用者的已有习惯。

### 主流程设计

主流程按以下顺序执行：

1. 检查基础环境

   - 固定检查`git`

2. 选择平台

   - 选项为`GitHub`和`GitLab`

3. 解析平台主机

   - GitHub 固定为`github.com`

   - GitLab 提示用户输入主机，默认`gitlab.com`

   - GitLab 允许输入自建实例域名

4. 检查平台 CLI

   - GitHub 检查`gh`

   - GitLab 检查`glab`

5. 处理账号

   - 继续使用当前活动账号

   - 切换到已登录账号

   - 通过浏览器登录新账号

6. 获取当前活动账号资料

   - 用于配置本地仓库提交身份

7. 读取目标目录

   - 默认当前工作目录

8. 输入远程仓库信息

   - GitHub：保持当前“仓库名”模型

   - GitLab：增加 namespace 输入

9. 选择仓库可见性

   - GitHub：`public/private`

   - GitLab：`public/internal/private`

10. 输出执行摘要并请求确认

11. 初始化本地 Git 仓库（如需要）

12. 配置当前仓库本地提交身份

13. 检测超大文件并在需要时启用 Git LFS

14. 执行`git add`与提交

15. 创建远程仓库并推送，或已有`origin`时直接推送

16. 如果本次是新登录账号，结束后提供可选清理

### 平台选择与主机处理

#### GitHub

- 平台固定为 GitHub

- 主机固定为`github.com`

- 不新增额外主机输入，保持原行为简单稳定

#### GitLab

- 平台选择为 GitLab 后，提示输入主机

- 默认主机为`gitlab.com`

- 允许用户输入自建 GitLab 域名

- 后续账号查询、登录切换、仓库创建、登出都基于该主机执行

### 平台适配层设计

平台适配层不要求必须使用抽象基类，但必须提供统一职责边界。建议统一为以下能力：

- `ensure_cli_exists()`

- `get_accounts(host)`

- `get_active_account(host)`

- `login_or_switch_account(host)`

- `get_profile(host)`

- `get_visibility_options()`

- `create_remote_repo(repo_path, repo_name, visibility, host, namespace=None)`

- `logout_account(host, login)`

这样主流程不直接感知`gh`和`glab`的命令差异，只依赖统一的接口语义。

### 数据模型

建议保留并适度扩展现有数据模型：

#### Account

- `login`

- `active`

- `host`

用于表示某个平台某个主机上的已登录账号。

#### LoginResult

- `account`

- `newly_logged_in`

用于描述账号切换或新登录后的结果。

#### Profile

- `login`

- `display_name`

- `email`

- `commit_email_fallback`

建议通过属性方法统一产出：

- `commit_name`

  - 优先`display_name`

  - 无值时回退`login`

- `commit_email`

  - 优先`email`

  - 无值时回退`commit_email_fallback`

### GitHub 设计

GitHub 分支尽量保持现有行为，做最小必要改动。

保留如下逻辑：

- 使用`gh`

- 主机固定`github.com`

- 使用当前`gh auth status`、`gh auth switch`、`gh auth login`、`gh auth logout`风格流程

- 使用`gh api user`获取资料

- 仓库可见性保持`public/private`

- 无公开邮箱时继续使用 GitHub 的 noreply 邮箱策略

- 无`origin`时使用`gh repo create`

允许的最小通用化调整只有：

- 在脚本开头新增平台选择步骤

- 代码结构上从 GitHub 专用改为 GitHub/GitLab 共用主流程

### GitLab 设计

GitLab 是本次新增能力的重点，设计如下。

#### CLI 与账号管理

- 使用`glab`

- 支持基于主机上下文查询账号状态

- 支持继续当前活动账号、切换已登录账号、网页登录新账号

- 支持结束后按用户选择清理本次新登录账号

#### 主机

- 默认主机为`gitlab.com`

- 允许输入自建实例域名

- 适配层的所有 GitLab 命令都要显式使用该主机上下文

#### 可见性

GitLab 平台下显示以下可见性选项：

- `public`

- `internal`

- `private`

不强制和 GitHub 做伪统一，以保持平台能力完整。

#### namespace 与 project 处理

GitHub 继续保持“仓库名”输入模型，不强制引入 owner 输入。

GitLab 则单独增强 namespace 支持：

- 用户输入`namespace`

- 默认值优先使用当前账号个人 namespace 或 login

- 允许输入 group 或 subgroup 路径，例如`team/backend`

- `repo_name`继续单独输入，默认值为本地目录名

最终远程项目路径为：

`namespace/repo_name`

这种设计把 GitLab 的 group/subgroup 场景纳入支持范围，同时不影响 GitHub 的现有心智模型。

#### 提交邮箱策略

GitLab 不使用硬编码的 GitHub 风格 noreply 邮箱回退。

推荐策略如下：

1. 优先使用 CLI/API 获取到的邮箱

2. 若拿不到邮箱，则读取当前仓库本地`git config user.email`

3. 若本地仓库没有，再读取全局`git config user.email`

4. 仍无值时，提示用户手动输入一个提交邮箱

这样可以兼容 GitLab 自建实例和不同组织的邮箱策略，避免错误猜测。

### Git LFS 与大文件处理

这部分继续沿用现有逻辑，作为平台无关能力。

- 超过 100MB 的文件视为需要 Git LFS 处理

- 只有在检测到超大文件时才检查`git-lfs`

- 启用`git lfs install --local`

- 根据大文件后缀和相对路径生成跟踪规则

GitHub 和 GitLab 分支都共用这部分逻辑。

### 提交与推送逻辑

这部分同样作为平台无关能力处理。

- 执行`git add .`

- 若没有待提交变更，则跳过提交步骤

- 若已有待提交变更，则提示用户输入提交信息

- 若仓库没有任何提交，则在创建远程仓库前中止并报错

- 若已存在`origin`，则不执行平台侧仓库创建，直接`git push -u origin <branch>`

- 若不存在`origin`，则由平台适配层创建远程仓库并推送

这样可最大化复用现有本地 Git 操作逻辑。

### 错误处理

保持现有脚本“失败即明确报错”的风格，并增强以下场景的提示：

- 缺少`gh`或`glab`时，明确说明缺少哪个 CLI

- GitLab 无法确定提交邮箱时，明确进入手动输入流程

- 无法检测到活动账号时，明确提示先登录或在脚本中选择登录

- 无任何提交但试图创建远程仓库时，明确阻止继续

### 输出摘要

执行摘要保留现有风格，并增加多平台必要信息：

- 目标目录

- 平台

- 主机

- 活动账号

- 提交用户名

- 提交邮箱

- GitHub 下的远程仓库名

- GitLab 下的 namespace 与 repo_name

- 仓库可见性

让用户在执行前看到完整的最终上下文。

### 测试建议

本工具适合做轻量测试，不建议为其引入过重的测试框架设计。

建议覆盖以下内容：

- 账号状态解析函数

- Git LFS 跟踪规则生成函数

- GitHub 与 GitLab 的可见性选项分支

- GitLab 自建主机场景下命令参数拼装

- 已有`origin`时跳过远程创建逻辑

- GitLab 邮箱回退到本地配置与手动输入的分支

### 风险与控制

#### 风险 1：GitHub 回归

如果通用化时直接大改主流程，容易破坏现有 GitHub 使用体验。

控制方式：

- GitHub 行为尽量保持不变

- 优先抽取通用能力，避免重写 GitHub 逻辑

#### 风险 2：GitLab CLI 在不同主机上的差异

GitLab 自建实例在认证与资料返回上可能与`gitlab.com`存在差异。

控制方式：

- 以`glab`当前登录上下文为主

- 邮箱策略采用保守回退，不猜测平台特定邮箱格式

#### 风险 3：namespace 输入错误

GitLab group/subgroup 路径容易输错，导致远程创建失败。

控制方式：

- 执行摘要中明确显示最终`namespace/repo_name`

- 失败时直接展示平台 CLI 报错，避免吞掉细节

### 实施建议

建议按以下顺序实现：

1. 重命名主脚本并保留兼容入口

2. 抽取最小平台适配层，先保持 GitHub 分支行为稳定

3. 接入 GitLab 平台选择、主机输入和可见性分支

4. 接入 GitLab 账号管理与仓库创建

5. 接入 GitLab namespace 与邮箱回退流程

6. 更新 README 中该工具的说明

7. 增补最小测试覆盖
