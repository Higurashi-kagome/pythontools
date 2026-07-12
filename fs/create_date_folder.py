import argparse
from datetime import datetime
from pathlib import Path


TOKEN_MAPPING = {
    'YYYY': '%Y',
    'MM': '%m',
    'DD': '%d',
}


def build_folder_name(template: str = 'YYYYMMDD', current_datetime: datetime | None = None) -> str:
    """根据日期模板生成文件夹名称

    Args:
        template: 日期模板，默认`YYYYMMDD`
        current_datetime: 当前时间，测试时可传入固定值

    Returns:
        按模板格式化后的文件夹名称
    """
    normalized_template = template.strip()
    if not normalized_template:
        raise ValueError('日期模板不能为空。')

    format_template = normalized_template
    for token, format_code in TOKEN_MAPPING.items():
        format_template = format_template.replace(token, format_code)

    date_value = current_datetime or datetime.now()
    return date_value.strftime(format_template)


def create_date_folder(
    target_directory: str,
    template: str = 'YYYYMMDD',
    current_datetime: datetime | None = None,
) -> tuple[Path, bool]:
    """在指定目录下创建日期文件夹

    Args:
        target_directory: 目标文件夹路径
        template: 日期模板，默认`YYYYMMDD`
        current_datetime: 当前时间，测试时可传入固定值

    Returns:
        元组的第一个值为目标文件夹路径，第二个值表示是否本次新建成功
    """
    target_path = Path(target_directory).expanduser().resolve()
    if not target_path.exists():
        raise FileNotFoundError(f'目标文件夹不存在：{target_path}')
    if not target_path.is_dir():
        raise NotADirectoryError(f'目标路径不是文件夹：{target_path}')

    folder_name = build_folder_name(template, current_datetime=current_datetime)
    folder_path = target_path / folder_name

    if folder_path.exists():
        if not folder_path.is_dir():
            raise FileExistsError(f'已存在同名文件，无法创建文件夹：{folder_path}')
        return folder_path, False

    folder_path.mkdir()
    return folder_path, True


def show_duplicate_folder_notification(
    folder_path: Path,
    toaster_class: type | None = None,
    toast_class: type | None = None,
) -> None:
    """在 Windows 右下角弹出目录已存在通知

    Args:
        folder_path: 已存在的文件夹路径
        toaster_class: 通知发送类，测试时可注入假对象
        toast_class: 通知内容类，测试时可注入假对象
    """
    resolved_toaster_class = toaster_class
    resolved_toast_class = toast_class
    if resolved_toaster_class is None or resolved_toast_class is None:
        try:
            from windows_toasts import Toast, WindowsToaster
        except ModuleNotFoundError as error:
            raise ModuleNotFoundError(
                '未安装 windows-toasts，请先执行 pip install -r requirements.txt 或 pip install windows-toasts。'
            ) from error

        resolved_toaster_class = WindowsToaster
        resolved_toast_class = Toast

    toaster = resolved_toaster_class('create_date_folder')
    toast = resolved_toast_class()
    toast.text_fields = ['文件夹已存在', str(folder_path)]
    toaster.show_toast(toast)


def create_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器

    Returns:
        命令行参数解析器
    """
    parser = argparse.ArgumentParser(description='在指定目录下创建按日期命名的文件夹')
    parser.add_argument('directory', help='目标文件夹路径')
    parser.add_argument('template', nargs='?', default='YYYYMMDD', help='日期模板，默认 YYYYMMDD')
    return parser


def main() -> int:
    """脚本入口

    Returns:
        进程退出码
    """
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        folder_path, created = create_date_folder(args.directory, args.template)
    except (FileNotFoundError, NotADirectoryError, FileExistsError, ValueError, OSError) as error:
        print(f'处理失败：{error}')
        return 1

    if created:
        print(f'创建完成：{folder_path}')
    else:
        print(f'文件夹已存在：{folder_path}')
        try:
            show_duplicate_folder_notification(folder_path)
        except Exception as error:
            print(f'Windows 通知发送失败：{error}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
