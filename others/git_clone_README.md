# Git Clone 工具

从剪切板读取 Git 仓库 URL 并在指定目录下执行 clone 操作。

提供两个版本：
- **控制台版本** (`git_clone.py`)：命令行界面，显示 Git 原生进度
- **GUI 版本** (`git_clone_gui.py`)：图形界面，带进度条和实时输出

## 功能特点

- 自动读取剪切板内容
- 验证 Git 仓库 URL 格式
- 支持多种 Git URL 格式
- 在指定目录下执行 clone
- GUI 版本提供友好的图形界面和进度显示

## 使用方法

### 控制台版本

```bash
python git_clone.py <目标目录>
```

### GUI 版本（推荐）

```bash
python git_clone_gui.py <目标目录>
```

### 示例

```bash
# Windows 路径
python git_clone_gui.py "E:\projects\"
python git_clone_gui.py E:\projects\

# 相对路径
python git_clone_gui.py ./repos/
```

## GUI 版本特性

- 清晰的窗口界面
- 显示仓库 URL 和目标目录
- 动态进度条
- 实时输出 Git 克隆信息
- 状态提示（准备中/克隆中/成功/失败）
- 完成后可关闭窗口

## 支持的 URL 格式

- HTTPS: `https://github.com/user/repo.git`
- HTTPS (无 .git): `https://github.com/user/repo`
- SSH: `git@github.com:user/repo.git`
- SSH (无 .git): `git@github.com:user/repo`

## 使用流程

1. 复制 Git 仓库 URL 到剪切板
2. 运行脚本并指定目标目录
3. 脚本自动验证 URL 并执行 clone
4. GUI 版本会显示实时进度和输出

## 依赖

- **pyperclip**: 用于读取剪切板内容
- **tkinter**: GUI 版本使用（Python 标准库，无需额外安装）
- **git**: 需要系统已安装 Git 并添加到 PATH

## 错误处理

脚本会检查以下情况：
- 剪切板是否为空
- URL 格式是否有效
- 目标目录是否存在
- Git 命令是否可用

GUI 版本会通过弹窗显示错误信息。
