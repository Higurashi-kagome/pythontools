import jieba.posseg as psg
import os

# 根据词频降序排序


def get_frequency(lst):
    word_frequency = {}
    for word in lst:
        if word in word_frequency:
            word_frequency[word] += 1
        else:
            word_frequency[word] = 1
    word_frequency_list = sorted(
        word_frequency.items(), key=lambda x: x[1], reverse=True)
    return word_frequency_list


def print_word_frequency(file_path):
    if os.path.exists(file_path) and os.path.isfile(file_path):
        with open(file=file_path, mode='r', encoding='utf-8') as f:
            content = (f.read())
    else:
        print('文件不存在：{}'.format(file_path))
        return
    # 2. 分离出感兴趣的名词，放在 lst_words 里
    lst_words = []
    for x in psg.cut(content):
        # 保留名词、人名、地名，长度至少两个字
        if x.flag in ['n', 'nr', 'ns'] and len(x.word) > 1:
            lst_words.append(x.word)

    # 3. 按照词频由大到小排序，放在 lst_sorted 里
    frequen_list = get_frequency(lst_words)

    # 4. 打印 TOP10
    # 使柱图不太长或太短
    divide = 50
    # 词汇个数超过十个且第十个词汇的频率低于 divide
    if len(frequen_list) >= 10 and frequen_list[9][1] < divide:
        divide = frequen_list[9][1]//2
    # 词汇个数不超过十个且最后一个词汇的频率低于 divide
    elif len(frequen_list) < 10 and frequen_list[-1][1] < divide:
        divide = frequen_list[-1][1]//2
    if divide == 0:
        divide = 1
    print('\n序号\t名词\t词频\t柱图\n')
    for i in range(10):
        if i < len(frequen_list):
            print('{}\t{}\t{}\t{}\n'.format(
                i+1, frequen_list[i][0], frequen_list[i][1], '.' * (frequen_list[i][1] // divide)))


if __name__ == "__main__":
    print_word_frequency('./README.md')
