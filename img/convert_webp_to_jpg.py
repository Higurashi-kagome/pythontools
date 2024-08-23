import os
from PIL import Image

"""
将当前目录中的所有 .webp 文件转换为 .jpg 格式
"""
def convert_webp_to_jpg():
    """Convert all .webp images in the current directory to .jpg format."""
    current_directory = os.getcwd()  # 获取当前工作目录

    for filename in os.listdir(current_directory):
        if filename.lower().endswith('.webp'):
            webp_path = os.path.join(current_directory, filename)
            jpg_path = os.path.splitext(webp_path)[0] + '.jpg'  # 创建新的 JPG 文件名

            try:
                with Image.open(webp_path) as img:
                    img.convert('RGB').save(jpg_path, 'JPEG')  # 转换并保存为 JPG 格式
                print(f"Converted: {filename} to {os.path.basename(jpg_path)}")
            except Exception as e:
                print(f"Error converting {filename}: {e}")

if __name__ == "__main__":
    convert_webp_to_jpg()
    print("Conversion completed.")
