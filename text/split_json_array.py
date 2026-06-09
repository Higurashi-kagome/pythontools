import argparse
import json
import re
from datetime import datetime
from pathlib import Path


WINDOWS_RESERVED_NAMES = {
    'CON',
    'PRN',
    'AUX',
    'NUL',
    'COM1',
    'COM2',
    'COM3',
    'COM4',
    'COM5',
    'COM6',
    'COM7',
    'COM8',
    'COM9',
    'LPT1',
    'LPT2',
    'LPT3',
    'LPT4',
    'LPT5',
    'LPT6',
    'LPT7',
    'LPT8',
    'LPT9',
}


def sanitize_filename(value: object) -> str:
    text = str(value).strip()
    text = re.sub(r'[<>:"/\\|?*]', '_', text)
    text = text.rstrip(' .')

    if not text:
        return ''

    if text.upper() in WINDOWS_RESERVED_NAMES:
        return f'_{text}'

    return text


def build_output_directory(input_path: Path, output_root: str | None = None, timestamp: str | None = None) -> Path:
    root_directory = Path(output_root) if output_root else input_path.parent
    folder_name = timestamp or datetime.now().strftime('%Y%m%d_%H%M%S')
    return root_directory / folder_name


def build_file_stem(item: dict, key_name: str | None, index: int) -> str:
    if key_name and key_name in item:
        sanitized_name = sanitize_filename(item[key_name])
        if sanitized_name:
            return sanitized_name

    return f'item_{index}'


def ensure_unique_file_path(output_directory: Path, file_stem: str) -> Path:
    output_path = output_directory / f'{file_stem}.json'
    duplicate_index = 2

    while output_path.exists():
        output_path = output_directory / f'{file_stem}_{duplicate_index}.json'
        duplicate_index += 1

    return output_path


def split_json_array_file(
    input_file: str,
    key_name: str | None = None,
    output_root: str | None = None,
    encoding: str = 'utf-8',
    timestamp: str | None = None,
) -> Path:
    input_path = Path(input_file)
    if not input_path.is_file():
        raise FileNotFoundError(f'文件不存在：{input_path}')

    with input_path.open('r', encoding=encoding) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError('输入文件的 JSON 顶层必须是数组。')

    output_directory = build_output_directory(input_path, output_root=output_root, timestamp=timestamp)
    output_directory.mkdir(parents=True, exist_ok=False)

    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f'第 {index} 个数组元素不是 JSON 对象。')

        file_stem = build_file_stem(item, key_name=key_name, index=index)
        output_path = ensure_unique_file_path(output_directory, file_stem)

        with output_path.open('w', encoding=encoding) as file:
            json.dump(item, file, ensure_ascii=False, indent=2)
            file.write('\n')

    return output_directory


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='将 JSON 数组拆分为多个单对象 JSON 文件')
    parser.add_argument('input_file', help='输入文件路径，文件内容需为 JSON 数组')
    parser.add_argument('-k', '--key', help='用于生成文件名的对象字段，默认按序号命名，例如 item_1')
    parser.add_argument(
        '-o',
        '--output-root',
        help='输出根目录，默认使用输入文件所在目录，并在其下创建当前时间命名的文件夹',
    )
    parser.add_argument('--encoding', default='utf-8', help='输入与输出使用的编码，默认 utf-8')
    return parser


def main() -> int:
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        output_directory = split_json_array_file(
            input_file=args.input_file,
            key_name=args.key,
            output_root=args.output_root,
            encoding=args.encoding,
        )
    except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError) as error:
        print(f'处理失败：{error}')
        return 1

    print(f'拆分完成，输出目录：{output_directory}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
