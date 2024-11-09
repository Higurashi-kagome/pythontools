import cv2

def take_photo(filename):
    # 打开默认摄像头
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("无法打开摄像头")
        return

    # 读取一帧
    ret, frame = cap.read()

    if ret:
        # 保存图像
        cv2.imwrite(filename, frame)
        print(f"照片已保存为 {filename}")
    else:
        print("无法读取图像")

    # 释放摄像头
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    filename = input("请输入保存照片的文件名（例如 photo.jpg）：")
    take_photo(filename)
