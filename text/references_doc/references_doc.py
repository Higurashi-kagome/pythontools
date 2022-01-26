""" 用于生成 References.md。 """
# 比如一个文件夹中的一些源文件中包含参考链接，本脚本将其提取出来，总结到 References.md 中。
""" 使用 """
# 1. 根据自己的需要修改 glob_str 及 re_pattern。
# 2. 将该脚本放到源文件所在文件夹
# 3. 运行该脚本，成功则会在源文件所在文件夹生成一个 References.md 文件

import glob
import os
import re

glob_str = '*.py'
re_pattern = '(https:\/\/github\.com.*(?<=\/)(.*)$)'

def gen_ref_doc():
	global glob_str
	global re_pattern
	# 依次读取文件获取注释信息
	java_file = glob.glob(glob_str)
	doc_lines = []
	for file_name in java_file:
		with open(file_name,'r',encoding='utf-8') as f:
			lines = [line.rstrip() for line in f]
			for line in lines:
				match = re.search(re_pattern, line)
				if match:
					link = match.group(1)
					link_name = match.group(2)
					doc_lines.append('[{fn}]({fn})：[{ln}]({l})\n\n'.format(
						fn=file_name, ln=link_name, l=link))
	# 将注释信息写入文件
	ref_doc = os.path.join(os.getcwd(), 'References.md')
	if not os.path.exists(ref_doc):
		with open(ref_doc, 'w+',encoding='utf-8') as f:
			f.writelines(doc_lines)
			print('References.md 文件已生成')
	else:
		print('文件名重复：References.md')


if __name__ == '__main__':
	gen_ref_doc()