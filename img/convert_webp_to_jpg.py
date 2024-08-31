import os
import argparse
from PIL import Image

"""
将传入路径中的所有 .webp 文件转换为 .jpg 格式（不传路径时默认当前目录）
"""
def convert_webp_to_jpg(directory):
    """Convert all .webp images in the specified directory to .jpg format."""
    for filename in os.listdir(directory):
        if filename.lower().endswith('.webp'):
            webp_path = os.path.join(directory, filename)
            jpg_path = os.path.splitext(webp_path)[0] + '.jpg'  # 创建新的 JPG 文件名

            try:
                with Image.open(webp_path) as img:
                    img.convert('RGB').save(jpg_path, 'JPEG')  # 转换并保存为 JPG 格式
                print(f"Converted: {filename} to {os.path.basename(jpg_path)}")
            except Exception as e:
                print(f"Error converting {filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert .webp images to .jpg format.')
    parser.add_argument('directory', type=str, nargs='?', default=os.getcwd(),
                        help='Directory containing .webp files (default: current directory)')

    args = parser.parse_args()
    convert_webp_to_jpg(args.directory)
    print("Conversion completed.")
