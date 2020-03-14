import pyperclip
import time

# 本文件可以运行在Python环境下(需要先安装pyperclip)，用于在依次复制图片URL和标题后生成Markdown格式的文本到剪切板

# 用于记录剪切板上的原内容(最新的内容)
last_string = pyperclip.paste()
# 生成Makdown图片格式的临时字符串,用于保存剪切板上的有效内容
temp_string = ""
# 记录剪切板改变次数
i = 0
while True:
                # 检测频率
                time.sleep(0.2)
                # 每循环一次获得剪切板上的内容
                string = pyperclip.paste()
                # 如果剪切板上的内容发生了变化(与剪切板上的原内容不一致)
                if string != last_string and string != '':
                                i=i+1
                                if i ==1:
                                    # 保存复制的第一个新字符串并加上Markdown部分内容
                                    temp_string = "<div align=center><img src=\""+ string + "\" alt=\""
                                if i == 2:
                                    # 保存复制的第二个新字符串并加上Markdown剩余部分内容
                                    temp_string =  temp_string + string + "\" style=\"zoom: 80%;\" /></div>"
                                    # 将剪切板设置为temp_string并将 string 设置为最新内容
                                    pyperclip.copy(temp_string)
                                    string = pyperclip.paste()
                                    print(string)
                                    # 完成两次复制以后回到重新开始记录
                                    i = 0
                                # 每一次剪切板有变化都将last_string设置成剪切板上的新内容
                                last_string = string
