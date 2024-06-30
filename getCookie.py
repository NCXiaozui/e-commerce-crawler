import json
import time

from selenium import webdriver

if __name__ == "__main__":
    # 初始化浏览器
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver=webdriver.Chrome(options=options)
    print("init webdriver\n")

    # 打开淘宝URL
    url = 'https://login.taobao.com/member/login.jhtml'
    driver.get(url)

    for second in range(0,61):
        print("倒计时: {}".format(60-second),flush=True)
        time.sleep(1)
    with open(f'./taobao.cookie','w') as file:
        file.write(json.dumps(driver.get_cookies()))
    driver.close()
    driver.quit()
    print('\nCookie已保存')
    time.sleep(5)
