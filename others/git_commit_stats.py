#!/usr/bin/env python3
"""
递归查找git仓库并统计18:00之后的提交记录
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime, time
from pathlib import Path
from typing import List, Dict, Optional

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def is_git_repo(path: Path) -> bool:
    """检查给定路径是否为git仓库"""
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def find_git_repos(start_path: Path, skip_repo_search: bool = True) -> List[Path]:
    """递归查找git仓库"""
    git_repos = []
    
    # 首先检查起始路径本身是否是git仓库
    if is_git_repo(start_path):
        git_repos.append(start_path)
        if skip_repo_search:
            return git_repos  # 如果起始路径是git仓库且不继续搜索，直接返回
    
    try:
        for item in start_path.iterdir():
            if item.is_dir():
                if is_git_repo(item):
                    git_repos.append(item)
                    if skip_repo_search:
                        continue  # 跳过仓库内的递归
                
                # 递归查找子目录
                git_repos.extend(find_git_repos(item, skip_repo_search))
    except PermissionError:
        print(f"权限不足，跳过目录: {start_path}")
    
    return git_repos


def get_commits_after_time(repo_path: Path, target_time: time, authors: List[str] = None) -> List[Dict]:
    """获取指定时间后的提交记录，可按作者过滤"""
    try:
        # 执行git log命令获取提交信息
        cmd = [
            'git', 'log', 
            '--pretty=format:%H|%an|%ad|%s',
            '--date=iso'
        ]
        
        result = subprocess.run(
            cmd, 
            cwd=repo_path, 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            print(f"获取 {repo_path} 的提交记录失败: {result.stderr}")
            return []
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            try:
                commit_hash, author, commit_date, message = line.split('|', 3)
                
                # 解析日期时间
                dt = datetime.fromisoformat(commit_date.replace(' ', 'T', 1))
                
                # 检查时间是否在目标时间之后
                if dt.time() >= target_time:
                    # 如果指定了作者列表，检查作者是否在列表中
                    if authors is None or any(a.lower() in author.lower() for a in authors):
                        commits.append({
                            'hash': commit_hash,
                            'author': author,
                            'date': dt,
                            'message': message,
                            'repo': repo_path.name
                        })
            except ValueError:
                continue
        
        return commits
        
    except subprocess.CalledProcessError as e:
        print(f"执行git命令失败: {e}")
        return []
    except Exception as e:
        print(f"处理提交记录时出错: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='统计git仓库18:00之后的提交记录')
    parser.add_argument('path', help='起始搜索路径')
    parser.add_argument('--no-skip', action='store_false', dest='skip_repo_search',
                       help='在git仓库内继续递归搜索')
    parser.add_argument('--time', default='18:00', 
                       help='目标时间 (格式: HH:MM，默认: 18:00)')
    parser.add_argument('--output', '-o', 
                       help='输出到文件（可选）')
    parser.add_argument('--author', '-a', action='append',
                       help='过滤指定作者（可多次使用）')
    
    args = parser.parse_args()
    
    # 解析目标时间
    try:
        target_time = datetime.strptime(args.time, '%H:%M').time()
    except ValueError:
        print(f"时间格式错误，请使用 HH:MM 格式")
        return
    
    start_path = Path(args.path)
    if not start_path.exists():
        print(f"路径不存在: {start_path}")
        return
    
    # 自动生成输出文件名（如果没有指定）
    if not args.output:
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"git_commits_after_{args.time.replace(':', '')}_{current_time}.txt"
    
    print(f"开始查找git仓库，起始路径: {start_path}")
    print(f"目标时间: {target_time}")
    print(f"跳过仓库内搜索: {args.skip_repo_search}")
    if args.author:
        print(f"过滤作者: {', '.join(args.author)}")
    print(f"输出文件: {args.output}")
    print("-" * 50)
    
    # 查找所有git仓库
    git_repos = find_git_repos(start_path, args.skip_repo_search)
    
    if not git_repos:
        print("未找到任何git仓库")
        return
    
    print(f"找到 {len(git_repos)} 个git仓库")
    
    # 统计每个仓库的提交记录
    all_commits = []
    output_lines = []
    repos_with_commits = []
    
    for repo in git_repos:
        commits = get_commits_after_time(repo, target_time, args.author)
        all_commits.extend(commits)
        filter_desc = f" {target_time} 之后"
        if args.author:
            filter_desc += f" 且作者为 {', '.join(args.author)}"
        
        # 只记录有提交的仓库
        if len(commits) > 0:
            repo_stats = f"仓库 {repo.name}: 找到 {len(commits)} 个{filter_desc}的提交"
            repos_with_commits.append((repo_stats, len(commits)))
    
    # 按提交次数降序排序
    repos_with_commits.sort(key=lambda x: x[1], reverse=True)
    
    # 输出有提交的仓库
    for repo_stats, _ in repos_with_commits:
        print(repo_stats)
        output_lines.append(repo_stats)
    
    print("-" * 50)
    filter_desc = f" {target_time} 之后"
    if args.author:
        filter_desc += f" 且作者为 {', '.join(args.author)}"
    total_stats = f"总共找到 {len(all_commits)} 个{filter_desc}的提交"
    print(total_stats)
    output_lines.extend(["-" * 50, total_stats])
    
    # 按仓库分组并按时间排序显示详细信息
    if all_commits:
        # 按仓库分组
        from collections import defaultdict
        commits_by_repo = defaultdict(list)
        for commit in all_commits:
            commits_by_repo[commit['repo']].append(commit)
        
        # 按仓库名排序，每个仓库内按时间降序排序
        sorted_repos = sorted(commits_by_repo.keys())
        
        print("\n提交记录详情:")
        print("-" * 80)
        output_lines.extend(["\n提交记录详情:", "-" * 80])
        
        for repo_name in sorted_repos:
            repo_commits = commits_by_repo[repo_name]
            repo_commits.sort(key=lambda x: x['date'], reverse=True)
            
            # 仓库标题
            repo_header = f"\n【仓库: {repo_name}】 ({len(repo_commits)} 个提交)"
            print(repo_header)
            print("=" * 60)
            output_lines.extend([repo_header, "=" * 60])
            
            for commit in repo_commits:
                commit_details = [
                    f"  提交: {commit['hash'][:8]}",
                    f"  作者: {commit['author']}",
                    f"  时间: {commit['date'].strftime('%Y-%m-%d %H:%M:%S')}",
                    f"  信息: {commit['message']}",
                    "  " + "-" * 38
                ]
                
                for line in commit_details:
                    print(line)
                output_lines.extend(commit_details)
    
    # 写入输出文件
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"\n结果已保存到文件: {args.output}")
    except Exception as e:
        print(f"写入文件失败: {e}")


if __name__ == "__main__":
    main()