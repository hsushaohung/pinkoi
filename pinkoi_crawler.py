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

DOMAIN = "https://www.pinkoi.com"
category_url = "https://www.pinkoi.com/browse/?category=9&subcategory=903"
def crawl_comments(product_url):
    """
	crawl 20 comments for the product
	
	args:
	     the url of the product 

	return:
	    comments_list <list>: a list of comment<dict>
    """

    html_text = requests.get(product_url).text

    tid = re.findall('/product/(.{8})',html_text)[0]
    sid = re.findall('data-store-id="(.*)"',html_text)[0]

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


def crawl_list(category_url):
    """
	crawl all the product url from the given category_url	
    """
    style_list = ['cute','minimal','romantic','neutral','vintage','zakka','urban','zen','green']
    product_list = []

    for style in style_list:
        page = 1
        html_text = requests.get('%s&style=%s&page=%s'%(category_url,style,page)).text
        soup = BeautifulSoup(html_text,'html5lib')
        if not re.findall('class="m-filter-empty-result-wrapper"',html_text):
            ## page    
            while True :
                html_text = requests.get(category_url+'&style=%s&page=%s'%(style,page)).text
                soup = BeautifulSoup(html_text,'html5lib')
                if soup.select('div.g_grid_items > div.items'):
                    page += 1
                    for i in range (len(re.findall('div class="title"><a href="(/product/.*)?\?category',html_text))):
                        product_list.append(re.findall('div class="title"><a href="(/product/.*)?\?category',html_text)[i])
                        for url in product_list:
                            product_dict = crawl_product(url)
                            product_dict["style"] = style
                            writer.writerow(product_dict)
                            f.flush()
                else:
                    break
        else:
            continue
    

def crawl_product(product_url):
    """
        crawl product info
        
        args:
            the url of the product
            
        return:
            product_dict<dict>: a dict within product info
    """
    resp = requests.get(product_url)

    html_text = resp.text

    product_dict = {}
    soup = BeautifulSoup(html_text,"html5lib")

    product_dict['title'] = soup.find('span',{"data-translate":"title"}).text
    product_dict['price'] = soup.select_one('span.amount').text
    product_dict['brand'] = soup.select_one('span.store-link-wrap > a').text
    if re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+">(.*?)</a>',html_text):
        product_dict['category'] = re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+">(.*?)</a>',html_text)[0]
    else:
        product_dict['category'] = ""
    if re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+&material=\d+">(.*?)</a>',html_text):
        product_dict['material'] = re.findall(r'<a href="/browse\?category=\d+&subcategory=\d+&material=\d+">(.*?)</a>',html_text)[0]
    else:
        product_dict['material'] = ""
    product_dict['description'] = soup.select_one('div.m-richtext').text
    if re.findall(r'被欣賞 (\d+)',soup.select_one('div.box > ul > li').text.replace(',','')):
        product_dict['view_count'] = re.findall(r'被欣賞 (\d+)',soup.select_one('div.box > ul > li').text.replace(',',''))[0]
    else:
        product_dict['view_count'] = ""
    product_dict['comments'] = crawl_comments(product_url)

    return product_dict


if __name__ == "__main__":
    with open('pinkoi.csv','w') as f:
        headers = ['title', 'price', 'category', 'material','brand','description','view_count','comments']
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        crawl_list(category_url)
