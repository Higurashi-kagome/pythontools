""" 将 http://xt.hnnjgzbt.com/pub/gongshi 中的表格保存至 Excel """

from selenium import webdriver
from openpyxl import load_workbook
import pandas
import time
import os
import re

# 用于记录翻页（请求）次数
counter = 0

def get_dirver():
    driver = webdriver.Chrome(executable_path=r'../../utils/chromedriver.exe')
    driver.get('http://xt.hnnjgzbt.com/pub/gongshi')
    """ 点击表单，请求数据 """
    driver.find_element_by_id('areaName').click()
    driver.find_element_by_id('430300000000').click()
    driver.find_element_by_xpath("//button[text()='确定']").click()
    driver.find_element_by_id('jijuleixing').click()
    driver.find_element_by_xpath('//*[@id="treeType"]/li[6]/div').click()
    driver.find_element_by_id('0601').click()
    driver.find_element_by_xpath("//*[@id='dialog-confirmjj']/following-sibling::div[1]//button[text()='确定']").click()
    driver.find_element_by_class_name('s3').click()
    return driver

def update_counter(sleep_len=60, max=8):
    global counter
    counter = counter + 1
    if counter >= max:
        print('sleep({})'.format(sleep_len))
        time.sleep(sleep_len)
        counter = 0

def to_target_page(driver, page_index):
    finded = False
    while True:
        time.sleep(2)
        targetList = driver.find_elements_by_css_selector("a[href*='/pub/GongShiSearch?pageIndex={}']".format(page_index+1))
        for item in targetList:
            if item.text.isdigit() and int(item.text) == page_index+1:
                item.click()
                print('Finded target page.')
                finded = True
                update_counter(max=7)
                break
        if finded:
            break
        try:
            driver.find_element_by_xpath("//a[text()='下一页']/preceding-sibling::a[1]").click()
            update_counter(max=7)
        except:
            continue

def main():
    global counter
    driver = get_dirver()
    page_index = 0
    file_path = 'out.xlsx'
    if os.path.isfile(file_path):
        page_index = int(re.match('Sheet(\\d*)', pandas.ExcelFile('out.xlsx').sheet_names[-1]).group(1))
        print('There is a existing file.')
    if page_index:
        to_target_page(driver, page_index)
    book = None
    if os.path.exists(file_path):
        book = load_workbook(file_path)
    writer = pandas.ExcelWriter(file_path)
    if book:
        writer.book = book
    print('Start.')
    table_html = ''
    while True:
        time.sleep(2)
        try:
            next = driver.find_element_by_xpath('//a[text()="下一页"]')
            table_parent = driver.find_element_by_xpath('//table[@width="100%"]/..')
        except:
            continue
        try:
            if not table_parent or table_html == table_parent.get_attribute('innerHTML'):
                continue
            page_index = driver.find_element_by_xpath('//span[@class="current"]').text
            table_html = table_parent.get_attribute('innerHTML')
            df = pandas.read_html(table_html, encoding='utf-8')
            sheet_name = 'Sheet{}'.format(page_index)
            # 处理偶尔跳回第一页的情况
            try:
                if os.path.isfile(file_path) and sheet_name in pandas.ExcelFile(file_path).sheet_names:
                    print('Repeat sheet.')
                    writer.close()
                    driver.quit()
                    main()
                    break
            except:
                pass
            df[0].to_excel(writer, sheet_name=sheet_name)
            print(sheet_name)
            writer.save()
            # 检查抵达最后一页
            if  next and next.get_attribute('disabled'):
                print('At the last page. End.')
                break
            next.click()
            update_counter()
        except Exception as e:
            print(e)
            continue
            """ try:
                if driver.find_element_by_xpath('//h1[contains(text(),"服务器繁忙")]'):
                    update_counter(sleep_len=50, max=0)
                    writer.close()
                    driver.quit()
                    main()
                    break
            except:
                pass """
    writer.close()
    driver.quit()

if __name__ == '__main__':
    main()