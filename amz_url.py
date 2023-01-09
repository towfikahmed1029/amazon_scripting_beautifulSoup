from bs4 import BeautifulSoup
import requests
import mysql.connector 
import sys
import os
if sys.platform in ['Windows', 'win32', 'cygwin']:
    mydb = mysql.connector.connect(
    host = "database-1.criq1nathhcp.us-west-2.rds.amazonaws.com",
    user = "admin",
    password = "5HjTd1Fr7e3DS",
    database = "affiliate",
    port=33360
    )
else:
    mydb = mysql.connector.connect(
    host = os.environ['DB_HOST'],
    user = os.environ['DB_USER'],
    password = os.environ['DB_PASS'],
    database = os.environ['DB_NAME'],
    port=os.environ['DB_PORT']
    
    )

mycursor = mydb.cursor()
mycursor.execute("SELECT * FROM keywords WHERE status = 0 AND type = 2 LIMIT 1")
myresult = mycursor.fetchone()
try:
    key = myresult[1].split(":")
except:
    mydb.close()
    print("\nPlease Input Keywords.")
    exit()
product_input=key[0]
catgry=key[1]
keyid =  myresult[0]
print("\n",product_input) 
print("\n",catgry) 
mycursor = mydb.cursor()
sql = "UPDATE keywords SET status = 1  WHERE id = '{0}' ".format(keyid)
mycursor.execute(sql)
mydb.commit()
URL = 'https://www.amazon.com/s?k={0}&i={1}'.format(product_input,catgry)
print(URL)
headinfo={
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding":"gzip, deflate, br",
"Accept-Language":"en-US,en;q=0.5",
"Connection":'keep-alive',
"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0"
}
page = requests.get(URL,headers=headinfo).content
soup = BeautifulSoup(page, 'html.parser')
def itemparche(soup):
    a = 1
    mainarea = soup.find("div",class_='s-main-slot s-result-list s-search-results sg-row')
    for item in mainarea.find_all("div",attrs={"class": "s-result-item"}):
        asin=item.attrs['data-asin']
        if asin:
            print("Num -", a)
            a+=1
            url ='https://www.amazon.com/dp/'+asin
            review = 0
            status = 0
            mycursor = mydb.cursor()
            mycursor.execute("SELECT * FROM product_url WHERE url = '{0}'".format(url))
            myresult = mycursor.fetchone()
            if myresult == None:
                id= mycursor.lastrowid
                sqlproduct_url=("Insert into product_url(id,url,status,review) values(%s,%s,%s,%s)")
                sqlproduct_url_value=[id,url,status,review]
                mycursor.execute(sqlproduct_url,sqlproduct_url_value)
                mydb.commit()
            else:
                print("You have already this Url.") 
asd = 1
while True:
    print("Products page collecting---", asd)
    asd +=1 
    try :
        next = soup.find("a", class_ ="s-pagination-item s-pagination-next s-pagination-button s-pagination-separator")
        try:
            nexturl = "https://www.amazon.com"+(next.attrs['href'])
        except:
            nexturl=None
        if nexturl:
            itemparche(soup)
    except:
        nexturl=None
        itemparche(soup)
    if nexturl:
        page = requests.get(nexturl,headers=headinfo).content
        soup = BeautifulSoup(page, 'html.parser')
    print(nexturl)
    if not nexturl:
        try:
            itemparche(soup)
        except:
            print("\n0 products found by your search reasult.")
            mycursor.close()
            mydb.close()
            break
        print("\nSuccessfully collected ",product_input ,"'s all url.")
        mycursor.close()
        mydb.close()
        break
exit()