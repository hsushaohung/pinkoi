import cmd
import requests
import re
import json
import csv
from bs4 import BeautifulSoup
from datetime import datetime

DOMAIN = "https://www.pinkoi.com"

def crawl_comments(product_url):
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
        comment_dict['user_id'] = comment['owner_nick']
        comment_dict['feedback'] = comment['description']
        comment_dict['score'] = comment['score']
        comments_list.append(comment_dict)
    return comments_list

def crawl_list(category_url):
    producturl_list = []
    page = 1
    while True :
        html_text = requests.get('%s&page=%s'%(category_url,page)).text
        soup = BeautifulSoup(html_text,'html5lib')
        if soup.select('div.g_grid_items > div.items'):
            page += 1
            for i in range (len(re.findall('div class="title"><a href="(/product/.*)?\?category',html_text))):
                producturl_list.append(DOMAIN+re.findall('div class="title"><a href="(/product/.*)?\?category',html_text)[i])
        else:
            break
    return producturl_list

def crawl_product(product_url):
    html_text = requests.get(product_url).text

    product_dict = {}
    soup = BeautifulSoup(html_text,"html5lib")
    
    style_tag = ""
    style_taglist = ["可愛","簡約","浪漫","中性","復古","都會","禪風","民族","雜貨"]
    product_tags = soup.select_one("li.tag > div.r")
    if product_tags :
        tag_list = product_tags.text.split(" ")
        for t in tag_list:
            if (t in style_taglist):
                style_tag = t
            else:
                pass
    product_dict['style'] = style_tag
    
    if soup.find('span',{"data-translate":"title"}):
        product_dict['name'] = soup.find('span',{"data-translate":"title"}).text
    if soup.select_one('span.amount'): 
        product_dict['price'] = (soup.select_one('span.amount').text).replace(",","")
    if soup.select_one('span.store-link-wrap > a'):
        product_dict['brand'] = soup.select_one('span.store-link-wrap > a').text
    if re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+">(.*?)</a>',html_text):
        product_dict['category'] = re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+">(.*?)</a>',html_text)[0]
    else:
        product_dict['category'] = "no category"
    if re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+&material=\d+">(.*?)</a>',html_text):
        product_dict['memo'] = re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+&material=\d+">(.*?)</a>',html_text)[0]
    else:
        product_dict['memo'] = "no memo"
    if soup.select_one('div.m-richtext'):
        product_dict['desc'] = soup.select_one('div.m-richtext').text
    product_dict['comment'] = crawl_comments(product_url)
    ta_imgs = soup.select("div.thumbs > img")
    photo_urls = []
    for img in ta_imgs:
        photo_urls.append((img.get("src").replace("//","")))
    product_dict['picture'] = photo_urls
    product_dict['href'] = product_url
    
    id_count = len(product_list)+1
    product_dict["ID"] = "pk%06d" % id_count
    
    return product_dict



if __name__ == "__main__":
    start_time = datetime.now()
    category_url = input('category url :')
    category_num = re.findall('\?category=(\d+)',category_url)[0]
    subcategory_num = re.findall('subcategory=(\d+)',category_url)[0]
    producturl_list = crawl_list(category_url)
    
    url_item_count = "https://www.pinkoi.com/apiv2/match?category=%s&subcategory=%s" % (category_num,subcategory_num)
    item_html_text = requests.get(url_item_count).text
    js = json.loads(item_html_text)
    total_item = js["result"][0]["facets"]["category"]["total"]
    total_item
    current_item = 1
    for product_url in producturl_list:
            with open('pinkoi.txt', mode='r') as f:
                product_list = json.load(f)
            product_dict = crawl_product(product_url)                   
            print("crawled "+product_url + " ID : " + product_dict["ID"] + " " + str(current_item) + "/" + str(total_item))
            with open('pinkoi.txt', mode='w') as f:
                product_list.append(product_dict)
                json.dump(product_list, f)
            current_item += 1

    end_time = datetime.now()
    time_spent = str(end_time - start_time).split(".")[0]
    print('spent %s'%time_spent)
