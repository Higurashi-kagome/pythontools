import os
import re

def ex(cmd):
    wrap_close = os.popen(cmd)
    out = wrap_close.read()
    wrap_close.close()
    return out

# 运行 cmd 命令
# https://www.cnblogs.com/qican/p/11468866.html
# https://segmentfault.com/a/1190000040734370
if __name__ == '__main__':
    # 要管理员权限运行
    # out = ex('net stop Redis')
    # print(out)
    # out = ex('net start Redis')
    # print(out)
    out = ex(r'netstat -aon | find /i "listening" | find "6699"')
    out = out.strip()
    print(out)
    if len(out) > 0:
        pid = re.split(' +', out)[-1]
        print(pid)
        ex('taskkill /F /PID ' + pid)