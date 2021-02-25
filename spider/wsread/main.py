""" 向 https://weread.qnmlgb.tech/onestep 提交微信读书组队、无限卡信息 """

from selenium import webdriver

def weread(lianming=True, wuxian=True):
    driver = webdriver.Chrome()
    driver.get('https://weread.qnmlgb.tech/onestep')
    vid_input = driver.find_element_by_id('linkcode')
    vid_input.send_keys()
    driver.find_element_by_xpath("//button[text()='查找']").click()
    if lianming:
        driver.find_element_by_xpath("//a[text()='点击参与周四联名卡']").click()
        body_html = driver.find_element_by_tag_name('body').get_attribute('innerHTML')
        if '提交成功' not in body_html:
            print('联名卡提交失败')
        else:
            print('联名卡提交成功')
        driver.switch_to.window(driver.window_handles[0])
    if wuxian:
        driver.find_element_by_xpath("//a[text()='点击参与周六无限卡']").click()
        body_html = driver.find_element_by_tag_name('body').get_attribute('innerHTML')
        if '提交成功' not in body_html:
            print('无限卡提交失败')
        else:
            print('无限卡提交成功')
    driver.quit()

if __name__ == '__main__':
    accepts = ['y', 'Y']
    lianming = input('参与联名卡（y/n）：') in accepts
    wuxian = input('参与无限卡（y/n）：') in accepts
    vid = input('输入 userVid：')
    weread(lianming, wuxian)