# -*- coding: utf-8 -*-
"""
兼容入口：已升级为通用的 GitHub/GitLab 仓库初始化与推送工具。
"""

from __future__ import annotations

import sys

from others.git_repo_init_push import main


if __name__ == '__main__':
    print('提示：该脚本已升级为支持 GitHub/GitLab 的通用版本。')
    sys.exit(main())
