import re
import time
import pyperclip

# 写这个的原因：
# 用Makdown做完笔记之后有大量插入的图片为如下格式
# <center><img src="https://..." alt="图5.18 AB+AB的逻辑电路组成" style="zoom:25%;" /></center>
# 现想要如下将其中的style="zoom:25%;"修改为style="zoom:80%;"，并将<center></center>的格式改为<div align=center></div>
# <div align=center><img src="https://..." alt="图5.18 AB+AB的逻辑电路组成" style="zoom:80%;" />
# 因为大量图片都需要作此修改，故写下这个程序

# 使用：
# 使用时只需要先复制(Ctrl + C)原来图片的Markdown内容，程序就会将剪切板内容修改为想要的Markdown格式，直接粘贴即可
# 在Markdown文本中选中下面内容：
# <center><img src="https://..." alt="图5.18 AB+AB的逻辑电路组成" style="zoom:25%;" /></center>
# Ctrl + C复制
# Ctrl + V粘贴
# 得到<div align=center><img src="https://..." alt="图5.18 AB+AB的逻辑电路组成" style="zoom:80%;" />

# 思路：
# 先从剪切板获取整个字符串
# 再获取字符串中间部分的有效内容
# 然后将获取的中间部分的style部分修改为style = "80%"
# 最后添加使之居中的HTML语法
# 将最后得到的字符串复制到剪切板

# 获取剪切板内容
last_string = pyperclip.paste()

while True:
    # 检查频率
    time.sleep(0.2)
    # 每循环一次获得剪切板上的内容
    string = pyperclip.paste()
    # 如果剪切板上的内容发生了变化(与剪切板上的原内容不一致)
    if string != last_string and string != '':
        # 获取剪切板中的前部分有效内容
        temp_list1 = re.findall(r"<img[\s\S]*zoom:",string)
        # 获取剪切板中的后部分有效内容
        temp_list2 = re.findall(r";\" />",string)
        # 如果有效部分获取成功
        if temp_list1 and temp_list2:
            # 在有效部分前后添加使之居中的HTML语法并赋值给temp_string
            temp_string = "<div align=center>" + temp_list1[0] +"80%" + temp_list2[0] + "</div>"
            pyperclip.copy(temp_string)
            string = pyperclip.paste()
            print(temp_string)
        else:
            print("not match")
        # 每一次剪切板有变化都将last_string设置成剪切板上的新内容
        last_string = string
