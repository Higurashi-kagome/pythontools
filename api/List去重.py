import re

s = 'AA-BB-EE-DD-AA-A(B,C)-CC-A(B,C)'
l = re.split('-', s)
print(l)
f = list(set(l))
print(f)
# https://blog.csdn.net/Jerry_1126/article/details/68451634