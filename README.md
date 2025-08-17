# pythontools

使用之前请在当前目录（pythontools）下执行如下命令以安装依赖：

<!-- 依赖文件更新命令（确保安装了 pipreqs）：pipreqs ./ --encoding=utf8 --force -->

```
pip install -r requirements.txt
```

网络不好可参考[镜像站使用帮助 \| 清华大学开源软件镜像站](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/)设置镜像源。

另：运行使用了 Selenium 的脚本前需确保 [chromedriver.exe](utils/chromedriver.exe) 和 [geckodriver.exe](utils/geckodriver.exe) 与对应浏览器版本相匹配。

| 程序                                                         | 使用                                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [微信读书笔记工具：wereader](wereader)                       | [介绍](https://www.cnblogs.com/Higurashi-kagome/p/12872060.html) |
| [获取知乎回答（已失效）](zhihu)                              | [示例](zhihu/README.md)                                      |
| [为本地 Markdown 文件生成目录（可在 GitHub 上正常显示）](text/toc.py) | [介绍](https://www.cnblogs.com/Higurashi-kagome/p/12724993.html) |
| [为本地 Markdown 文件的标题编号](text/title_number.py)       | [介绍](https://www.cnblogs.com/Higurashi-kagome/p/12747857.html) |
| [使用正则表达式替换字符串](text/str_replace.py)              | [示例](demo/str_replace.md)                                  |
| [建标库规范自动化下载](spider/jianbiaoku/jianbiaoku.py)      | [介绍](https://www.cnblogs.com/Higurashi-kagome/p/15242418.html) |
| [生成参考文档索引](text/references_doc/references_doc.py)    | [演示](text/references_doc/references_doc.gif)               |
| [删除不被依赖的文件](text/find_dependencies.py)              |                                                              |
| [打印指定路径下重名的文件](fs/same_name.py)                  |                                                              |
| [下载 Markdown 文件中的图片到本地](text/get_markdown_img.py) |                                                              |
| [裁剪图片中的二维码](img/crop_qr_code.py) |                                                              |
| [将传入路径中的所有 .webp 文件转换为 .jpg 格式（不传路径时默认当前目录）](img/convert_webp_to_jpg.py) |                                                              |
| [读取 Markdown 文件，复制其中的图片链接为注释](text/copy_image_links_to_comments.py) |                                                              |
| [解析指定格式的文本为 CSV 文本](text/save_to_csv_text/save_to_csv_text.py) |                                                              |
| [CSV 文本转 SQL INSERT 语句](text/csv_to_sql/csv_to_sql.py)                  |                                                              |
| [统计 SQL 中的表名](text/extract_table_names/extract_table_names.py)                  |                                                              |
| [录制指定时长的音频](media/record_audio.py)                  |                                                              |
| [完成照相，保存为文件](media/take_photo.py)                  |                                                              |
