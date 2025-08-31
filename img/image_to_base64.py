import base64
from PIL import Image
import io
import os

def image_to_base64(image_path, format='PNG'):
    """
    将图片文件转换为 Base64 编码字符串
    :param image_path: 图片文件路径
    :param format: 输出图像格式（如 'PNG', 'JPEG'），默认为 'PNG'
    :return: Base64 编码的字符串（包含 data URL 前缀）
    """
    # 检查文件是否存在
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在：{image_path}")

    # 打开图片
    with Image.open(image_path) as img:
        # 如果是 RGBA 模式且格式为 JPEG，转换为 RGB
        if img.mode == 'RGBA' and format.upper() == 'JPEG':
            img = img.convert('RGB')

        # 将图片保存到内存中的字节流
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        img_bytes = buffer.getvalue()
        buffer.close()

        # 转换为 base64
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        # 构造 data URL
        mime_type = f"image/{format.lower()}"
        data_url = f"data:{mime_type};base64,{img_base64}"

        return data_url

# 使用示例
if __name__ == "__main__":
    image_path = r"C:\Users\wx.png"  # 替换为你的图片路径
    try:
        result = image_to_base64(image_path, format='JPEG')
        print("Base64 Data URL:")
        print(result)
    except Exception as e:
        print(f"错误：{e}")