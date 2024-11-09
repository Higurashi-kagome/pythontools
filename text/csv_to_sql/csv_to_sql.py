import sys

def csv_to_sql(csv_file, sql_file):
    # 读取 CSV 文件的所有行（UTF-8 编码）
    lines = open(csv_file, 'r', encoding='utf-8').readlines()
    # 遍历读取的每一行
    for line in lines:
        # 将行按逗号分隔
        values = line.strip().split(',')
        name = values[0] # 成果类别
        male = values[1] # 课题名称
        age = values[2] # 完成单位
        marry = values[3] # 小组成员
        with open(sql_file, 'a', encoding='utf-8') as f:
            f.write(f"INSERT INTO `sys_user` ( `name`, `male`, `age`, `marry`) VALUES ( '{name}', '{male}', {age}, '{marry}' );\n")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法：python script.py <csv_file_path> <text_file_path>")
        # python csv_to_sql.py csv.txt sql.sql
    else:
        csv_file_path = sys.argv[1]
        text_file_path = sys.argv[2]
        csv_to_sql(csv_file_path, text_file_path)