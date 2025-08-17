from PIL import Image
from pyzbar import pyzbar
import os

def crop_qr_code(image_path, output_path):
    """
    从图片中检测二维码，裁剪并保存为新文件
    :param image_path: 输入图片路径
    :param output_path: 输出二维码图片路径
    """
    # 打开图片
    img = Image.open(image_path)

    # 检测图片中的二维码
    qr_codes = pyzbar.decode(img)

    if not qr_codes:
        print("未在图片中检测到二维码。")
        return False

    # 取第一个检测到的二维码（如果有多个）
    qr = qr_codes[0]
    x, y, w, h = qr.rect.left, qr.rect.top, qr.rect.width, qr.rect.height

    # 裁剪二维码区域
    cropped_img = img.crop((x, y, x + w, y + h))

    # 保存裁剪后的二维码图片
    cropped_img.save(output_path)
    print(f"二维码已裁剪并保存为：{output_path}")
    return True

# 使用示例
if __name__ == "__main__":
    input_image = "input.jpg"      # 输入图片路径
    output_image = "qrcode_cropped.png"  # 输出文件路径

    if not os.path.exists(input_image):
        print(f"错误：找不到图片文件 {input_image}")
    else:
        crop_qr_code(input_image, output_image)