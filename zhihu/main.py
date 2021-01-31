import zhihu_answer
import login
from config import config
import word_analyze

""" 
在问题的回答数量较大时（比如 14941 个回答），通常可能遇到三类阻碍：
一是知乎客户端关闭连接，这时程序将会在等待后重试；
二是知乎提示需要登录（如果开始获取前没有登录的话），此时程序将会在等待一段时间后重试，重试无效后将弹出登录页面；
三是知乎提示需要输入验证码（在登录时发生），此时程序会等待一段时间后重试，重试无效后会弹出验证码输入页面。"""
if __name__ == '__main__':
    print('**********************************************************')
    print('当前配置：{}'.format(config))
    print('**********************************************************')
    if config['login']:
        login.main()
    question_id = input('请输入问题 id：').strip()
    answers = zhihu_answer.get_all_answers(question_id)
    if answers[0]:
        file_path = zhihu_answer.write_to_files(answers, config)
        if config['analyze']:
            print('**********************************************************')
            word_analyze.print_word_frequency(file_path)
    else:
        print('answers：{}'.format(answers))
    print('**********************************************************')
    