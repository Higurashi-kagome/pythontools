import os

# https://stackoverflow.com/questions/3430372/how-do-i-get-the-full-path-of-the-current-files-directory
if __name__ == '__main__':
    os.path.abspath(os.getcwd())