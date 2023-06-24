import os

# https://stackoverflow.com/questions/3430372/how-do-i-get-the-full-path-of-the-current-files-directory
if __name__ == '__main__':
    print(__file__)
    print(os.path.dirname(__file__))