"""
	www.pinkoi.com crawler
	Author: mabba8
	email: s226012005@gmail.com
"""
import cmd
import requests
import re
import json
import csv
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, wait

DOMAIN = "https://www.pinkoi.com"
style_list = ['cute','minimal','romantic','neutral','vintage','zakka','urban','zen','green']

def crawl_list(category_url,style):
    product_list = []

    # style loop
    for style in style_list:
        page = 1        
        html_text = requests.get('%s&style=%s&page=%s'%(category_url,style,page)).text
        soup = BeautifulSoup(html_text,'html5lib')
        if not re.findall('class="m-filter-empty-result-wrapper"',html_text):
                ## page loop
            while True :
                html_text = requests.get('%s&style=%s&page=%s'%(category_url,style,page)).text
                soup = BeautifulSoup(html_text,'html5lib')
                if soup.select('div.g_grid_items > div.items'):
                    page += 1
                    for i in range (len(re.findall('div class="title"><a href="(/product/.*)?\?category',html_text))):
                        product_list.append({"url":re.findall('div class="title"><a href="(/product/.*)?\?category',html_text)[i],"style":style})

                else:
                    break
        else:
            continue
    return product_list


def crawl_comments(product_info):
    product_url = DOMAIN + product_info["url"]
    html_text = requests.get(product_url).text
    soup = BeautifulSoup(html_text,"html5lib")

    tid = re.findall('/product/(.{8})',html_text)[0]
    
    sssid = (soup.select_one("span.store-link-wrap > a")).attrs["href"]
    ssid = re.findall('/store/(.*)',sssid)
    sid = ssid[0]
    
    comments_url = "https://www.pinkoi.com/apiv2/review/get?tid=%s&makeup_by_sid=%s&limit=20"%(tid,sid)

    comments_text = requests.get(comments_url).text

    js = json.loads(comments_text)

    comments_list = []
    for comment in js['result']:
        comment_dict = {}
        comment_dict['id'] = comment['owner_nick']
        comment_dict['comment'] = comment['description']
        comment_dict['score'] = comment['score']
        comments_list.append(comment_dict)
    return comments_list


def crawl_product(product_info):
    
    product_url = DOMAIN + product_info["url"]

    html_text = requests.get(product_url).text

    product_dict = {}
    soup = BeautifulSoup(html_text,"html5lib")
    
    product_dict['style'] = product_info["style"]
    product_dict['title'] = soup.find('span',{"data-translate":"title"}).text
    product_dict['price'] = soup.select_one('span.amount').text
    product_dict['brand'] = soup.select_one('span.store-link-wrap > a').text
    if re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+">(.*?)</a>',html_text):
        product_dict['category'] = re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+">(.*?)</a>',html_text)[0]
    else:
        product_dict['category'] = "no info"
    if re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+&material=\d+">(.*?)</a>',html_text):
        product_dict['material'] = re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+&material=\d+">(.*?)</a>',html_text)[0]
    else:
        product_dict['material'] = "no info"
    product_dict['description'] = soup.select_one('div.m-richtext').text
    if re.findall(r'被欣賞 (\d+)',soup.select_one('div.box > ul > li').text.replace(',','')):
        product_dict['view_count'] = re.findall(r'被欣賞 (\d+)',soup.select_one('div.box > ul > li').text.replace(',',''))[0]
    else:
        product_dict['view_count'] = "0"
    product_dict['comments'] = crawl_comments(product_info)

    print("crawled "+product_url)

    return product_dict

def crawl_save(product_info):
    product_dict = crawl_product(product_info)
    writer.writerrow(product_dict)
    f.flush()

if __name__ == "__main__":
    start_time = datetime.now()
    category_url = "https://www.pinkoi.com/browse/?category=9&subcategory=903" 
    category_num = re.findall('\?category=(\d+)',category_url)
    subcategory_num = re.findall('subcategory=(\d+)',category_url)
    product_list = [] 
    pool = ThreadPoolExecutor()
    futures = []
    style_list = ['cute','minimal','romantic','neutral','vintage','zakka','urban','zen','green']
    with open('pinkoi_%s_%s.csv'%(category_num[0],subcategory_num[0]),'w') as f:
        headers = ['title', 'price', 'category', 'material','brand','description','view_count','comments','style']
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for style in style_list:
            futures.append(pool.submit(crawl_list,category=category_url,style=style))
            product_list.append((pool.submit(crawl_list,category_url=category_url,style=style)).result())
        wait(futures)

        for product_info in product_list:
            futures.append(pool.submit(crawl_save,product_info))
        wait(futures)
    end_time = datetime.now()
    time_spent = str(end_time - start_time).split(".")[0]
    print('spent %s'%time_spent)
