import json
import csv
import sys
import time
import re
import random
import traceback

from tenacity import retry, stop_after_attempt, stop_after_delay, wait_fixed
from selenium import webdriver
from selenium.webdriver.common.by import By


TBPAGEVERSION = 0 # 淘宝页面旧0新1

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def getElement(goods, i):
    item_name = goods.text.split('\n')[0]
    try:
        item_price= goods.find_element(By.CSS_SELECTOR,
                            f'div:nth-child({i})>a>div > div:nth-child(1) > div:nth-child(4) > div').text
        item_paid=goods.find_element(By.CSS_SELECTOR,
                        f'div:nth-child({i})>a>div > div:nth-child(1) > div:nth-child(4) > span.Price--realSales--FhTZc7U').text
    except:
        item_price= goods.find_element(By.CSS_SELECTOR,
                            f'div:nth-child({i})>a>div > div:nth-child(1) > div:nth-child(3) > div').text
        item_paid=goods.find_element(By.CSS_SELECTOR,
                        f'div:nth-child({i})>a>div > div:nth-child(1) > div:nth-child(3) > span.Price--realSales--FhTZc7U').text
    item_shop = goods.find_element(By.CSS_SELECTOR,
                        f'div:nth-child({i})>a>div> div:nth-child(3) > div>a').text
    shop_link = goods.find_element(By.CSS_SELECTOR,
                        f'div:nth-child({i})>a>div> div:nth-child(3) > div>a').get_attribute(
'href')
    item_link = goods.find_element(By.CSS_SELECTOR,
                        f'div:nth-child({i})>a').get_attribute(
'href')

    return item_name,item_price,item_shop,shop_link,item_link,item_paid

if __name__ == "__main__":
    keyword = input("请输入想爬取的数据")
    csvfile = open(f'{keyword}_taobao_{time.strftime("%Y-%m-%d_%H-%M", time.localtime())}.csv', 'a', encoding='utf-8-sig',
                   newline='')
    csvWriter = csv.DictWriter(csvfile,
                               fieldnames=['item_name', 'item_price', 'item_shop', 'shop_link', 'item_link', 'bridge','item_paid'])
    csvWriter.writerow(
        {'item_name': '商品名', 'item_price': '商品价格', 'item_shop': '店铺名称', 'shop_link': '店铺链接',
         'item_link': '商品链接', 'bridge': '店铺id桥','item_paid':'付款人数(参考销量)'})


    # 浏览器参数
    print("开始启动Chrome")
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # 启动浏览器
    driver = webdriver.Chrome(options=options)

    # URL
    url = 'https://www.taobao.com'
    driver.get(url)  # 爬取想要的URL

    # 清空Cookie
    print("------正在清除Cookie------")
    driver.delete_all_cookies()
    print("------准备注入Cookie------")

    try:
        with open('./taobao.cookie', 'r') as f:
            cookie_list = json.load(f)
            for cookie in cookie_list:
                driver.add_cookie(cookie)

    except:
        print("未找到Cookie")

    print('------正在刷新浏览器------')
    driver.refresh()

    # 搜索词与页数获取
    print("------开始操作------")
    driver.get(f'https://s.taobao.com/search?q={keyword}')
    driver.implicitly_wait(10)

    try:
        # 老版PC淘宝页面
        taobaoPage = driver.find_element(By.CSS_SELECTOR,
                                          '#J_relative > div.sort-row > div > div.pager > ul > li:nth-child(2)').text
        taobaoPage = re.findall('[^/]*$', taobaoPage)[0]
        tbPageVersion = 0
    except:
        # 新版PC淘宝页面
        taobaoPage = driver.find_element(By.CSS_SELECTOR,
                                          '#sortBarWrap > div.SortBar--sortBarWrapTop--VgqKGi6 > div.SortBar--otherSelector--AGGxGw3 > div:nth-child(2) > div.next-pagination.next-small.next-simple.next-no-border > div > span').text
        taobaoPage = re.findall('[^/]*$', taobaoPage)[0]
        tbPageVersion = 1

    # 爬取页数控制
    print("------爬取页数获取成功------")
    print(f'共计{taobaoPage}页,建议每2小时总计爬取不超过20页')
    page_start = int(input('起始页数：'))
    page_end = int(input('截止页数：')) + 1

    for page in range(page_start, page_end):
        print(f'------当前正在获取第{page}页，还有{page_end - page_start - page}页------')
        driver.get(f'https://s.taobao.com/search?q={keyword}&page={page}&_input_charset=utf-8&commend=all&search_type=item&source=suggest&sourceId=tb.index')
        if driver.title == '验证码拦截':
            print(f'------出错：如有验证请验证。等待20秒------')
            time.sleep(20)
        time.sleep(5)
        # 尝试获取商品列表
        try:
            print(f'------当前正在获取第{page}页，还有{page_end - page_start - page}页------')
            goods_arr = driver.find_elements(By.CSS_SELECTOR, '#pageContent > div:nth-child(1) > div:nth-child(3) > div:nth-child(3) > div>div')
            goods_length = len(goods_arr)
            for i, goods in enumerate(goods_arr):
                try:
                    i=i+1
                    driver.execute_script("document.documentElement.scrollTop=1000")
                    print(f'------正在获取第{i}个,共计{goods_length}个------')
                    item_name, item_price, item_shop, shop_link, item_link,item_paid = getElement(goods, i)
                    try:
                        b = shop_link.split('https://store.taobao.com/shop/view_shop.htm?appUid=')[1]
                    except:
                        b = shop_link
                    csvWriter.writerow(
                        {'item_name': item_name, 'item_price': item_price, 'item_shop': item_shop, 'shop_link': shop_link,
                            'item_link': item_link, 'bridge': b,'item_paid':item_paid})
                    csvfile.flush()
                except:
                    print(f'第{i}个商品获取信息出错,跳过')
                    traceback.print_exc()
        except Exception as e:
            print(f'在遍历商品时出错{e}')
            traceback.print_exc()
            # 拉取商品列表失败则提示需要验证
            print(f'------出错：如有验证请验证。等待20秒------')
            print(f'------注意:第<{page}>页将跳过如需获取请重新运行程序！------')
            time.sleep(20)

        delay_time = random.randint(10, 30)
        for delay in range(delay_time):
            print(f'------第{page}页，还有{page_end - page_start - page}页------')
            print(f'------延时翻页：已延时{delay}秒，剩余{delay_time}秒------')
            time.sleep(1)

    print('------程序结束------')
    print('------程序结束正在保存文件------')
    csvfile.close()
    print('------保存文件完成，准备退出中')
    time.sleep(5)
    driver.close()
    sys.exit()
