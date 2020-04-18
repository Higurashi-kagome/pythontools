import pyperclip
import time

# 用于获得使文字居中的Markdown文本

# 思路：
# 1.获得剪切板上的新内容
# 2.将获得的新内容加上使其居中的Markdown格式
# 3.将新内容复制到剪切板

# 使用：
# 1.剪切想要居中的文本
# 2.粘贴文本

# 获取剪切板内容
last_string = pyperclip.paste()

while True:
    # 检查频率
    time.sleep(0.2)
    # 每循环一次获得剪切板上的内容
    string = pyperclip.paste()
    # 如果剪切板上的内容发生了变化(与剪切板上的原内容不一致)
    if string != last_string and string != '':
        temp_string = "<p align = \"center\">" + string + "</p>"
        pyperclip.copy(temp_string)
        string = pyperclip.paste()
        print(temp_string)
        # 每一次剪切板有变化都将last_string设置成剪切板上的新内容
        last_string = string
