import re
import sys
sys.path.append('..')
from utils import In

if __name__ == "__main__":
    lines = In.input_lines()
    pattern = re.compile(input('Input pattern：'))
    replacement = input('Input replacement：')
    str = ''
    for line in lines:
        str += pattern.sub(replacement, str) + '\n'
    print('Replaced')
    print(str[:-1])

