# -*- coding: utf-8 -*-
"""
Git Clone Tool
Read Git repository URL from clipboard and execute clone in specified directory

Usage:
    python git_clone.py <target_directory>
    python git_clone.py "E:\\path\\to\\"
"""

import sys
import os
import re
import subprocess
import pyperclip


def is_git_url(text):
    """Check if text is a valid Git repository URL"""
    text = text.strip()

    # Git URL patterns
    patterns = [
        r'^https?://[^\s]+\.git$',
        r'^https?://[^\s]+/[^\s]+/[^\s]+$',
        r'^git@[^\s]+:[^\s]+\.git$',
        r'^git@[^\s]+:[^\s]+$',
    ]

    for pattern in patterns:
        if re.match(pattern, text):
            return True

    # Check common Git hosting platforms
    git_domains = ['github.com', 'gitlab.com', 'gitee.com', 'bitbucket.org']
    if any(domain in text for domain in git_domains):
        return True

    return False


def clone_repo(repo_url, target_dir):
    """Execute git clone in specified directory with progress display"""
    if not os.path.exists(target_dir):
        print(f"Error: Target directory does not exist: {target_dir}")
        return False

    try:
        # 不捕获、不转发，让 git 直接向控制台输出（只看到 git 自己的输出）
        completed = subprocess.run(
            ['git', 'clone', '--progress', repo_url],
            cwd=target_dir
        )
        return completed.returncode == 0

    except FileNotFoundError:
        print("Error: git command not found. Please install Git and add to PATH")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python git_clone.py <target_directory>")
        print('Example: python git_clone.py "E:\\path\\to\\"')
        input("Press Enter To Exit")
        sys.exit(1)

    target_dir = sys.argv[1]

    # Get clipboard content
    try:
        clipboard_content = pyperclip.paste()
    except Exception as e:
        print(f"Error: Cannot read clipboard: {e}")
        input("Press Enter To Exit")
        sys.exit(1)

    if not clipboard_content:
        print("Error: Clipboard is empty")
        input("Press Enter To Exit")
        sys.exit(1)

    print(f"Clipboard content: {clipboard_content}")

    # Check if it's a Git URL
    if not is_git_url(clipboard_content):
        print("Error: Clipboard content is not a valid Git repository URL")
        print("Supported formats:")
        print("  - https://github.com/user/repo.git")
        print("  - https://github.com/user/repo")
        print("  - git@github.com:user/repo.git")
        input("Press Enter To Exit")
        sys.exit(1)

    print("Valid Git repository URL detected")

    # Execute clone
    success = clone_repo(clipboard_content, target_dir)

    input("Press Enter To Exit")
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
