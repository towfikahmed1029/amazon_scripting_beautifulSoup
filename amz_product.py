 # Import
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from nltk.stem.porter import PorterStemmer
from collections import Counter
from bs4 import BeautifulSoup
from datetime import datetime
from sklearn.svm import SVC
import mysql.connector
import pandas as pd
import requests
import time
import json
import nltk
import sys
import os
import re
nltk.download('stopwords')
from nltk.corpus import stopwords

# DB connect
if sys.platform in ['Windows', 'win32', 'cygwin']:
    mydb = mysql.connector.connect(
    host = "",
    user = "",
    password = "",
    database = "",
    port=
    )
else:
    mydb = mysql.connector.connect(
    host = os.environ['DB_HOST'],
    user = os.environ['DB_USER'],
    password = os.environ['DB_PASS'],
    database = os.environ['DB_NAME'],
    port=os.environ['DB_PORT']
    
    )
now = datetime.now()
date_time = now.strftime("%Y-%m-%d %H:%M:%S")
# DB Update
mycursor = mydb.cursor()
mycursor.execute("SELECT * FROM product_url WHERE status = 0 LIMIT 1")
myresult = mycursor.fetchone()
producturl = myresult[1]
urlid = myresult[0]
print("\nProduct Url---",producturl)
print("Product URL id---",urlid)
mycursor = mydb.cursor()
sql = "UPDATE product_url SET status = 1  WHERE id = '{0}' ".format(urlid)
mycursor.execute(sql)
mydb.commit()
# Product URL
URL = producturl
headinfo={
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding":"gzip, deflate, br",
    "Accept-Language":"en-US,en;q=0.5",
    "Connection":'keep-alive',
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0"
}
page = requests.get(URL,headers=headinfo).content
soup = BeautifulSoup(page, 'html.parser')
# Products Table + Catagory Table
productsname = soup.find('span', id = 'productTitle').text
try:
    productsreview_count_start = soup.find('span', id = 'acrCustomerReviewText').text
    productsreview_count_int=productsreview_count_start.replace("ratings", "")
    productsreview_count_int_f=productsreview_count_int.replace(",", "")
    productsreview_count=int(productsreview_count_int_f)
except:
    productsreview_count = 0
try:
    productsques_count_start=soup.find('a', class_ = 'a-link-normal askATFLink').text
    productsques_count_int=productsques_count_start.split(" ")
    while '' in productsques_count_int:
        productsques_count_int.remove('')
    productsques_count_int = productsques_count_int[0]
    productsques_count_int_f=productsques_count_int.replace(",", "")
    productsques_count=int(productsques_count_int_f)
except:
    productsques_count = 0
try:
    productsreview_average_start=soup.find('span',attrs={"data-hook":"rating-out-of-text"}).text
    productsreview_average_float=productsreview_average_start.replace(" out of 5", "")
    productsreview_average=float(productsreview_average_float)
except:
    productsreview_average = float(3.0)
try:
    productsDescription = soup.find('div', id = 'productDescription_feature_div').text
except:
    try:
        productsDescription = soup.find('div', class_ = 'a-section a-spacing-medium a-spacing-top-small').text
    except:
        productsDescription = "Empty"
productsurl = producturl
try:
    productsprice_find = soup.find('span', class_ = 'a-price aok-align-center reinventPricePriceToPayMargin priceToPay').contents[0].text
    productsprice =productsprice_find.replace("$", "")
    productsprice =float(productsprice)
except:
    productsprice = 0
def remove(string):
    return string.replace(" ", "")
try:
    productscatagory = soup.find('ul', class_ = 'a-unordered-list a-horizontal a-size-small')
    productscatagory = productscatagory.select("li")[0].text
    productscatagory = remove(productscatagory)
    productscatagory = "".join([s for s in productscatagory.splitlines(True) if s.strip("\r\n")])
    productscatagory = productscatagory.replace("'","")
    productscatagory = productscatagory.replace("\n", "")
except:
    productscatagory="Others"
time.sleep(2)
store = soup.find('a', id = 'bylineInfo').attrs['href']
store = store.split("?")[0]
time.sleep(2)
productsstore_url = ("https://www.amazon.com"+store)
storepage = requests.get(productsstore_url,headers=headinfo).content
soup = BeautifulSoup(storepage, 'html.parser')
time.sleep(2)
productsstore_name =  soup.find('span', itemprop = 'item').text
productsstore_name = productsstore_name.replace(".", "")
try:
    productsstore_logo = soup.find('img', class_ = 'style__heroImage__12q9C style__cover__2N0YX').attrs['src']
except:
    productsstore_logo = "Not Found"
productsname = productsname.replace(productsstore_name, "" )
productsname = productsname.split(",")[0].replace("\n", "").replace("  ", "")
if productsstore_name == None:
    productsstore_name = "Not Found"
brand= productsstore_name
print(productsname)
product_slug= productsname.lower().replace(' ','-').replace('--','-')
page = requests.get(URL,headers=headinfo).content
soup = BeautifulSoup(page, 'html.parser')
# DB Products
mycursor = mydb.cursor()
sqlproducts_value=[productsname,product_slug,productsreview_count,productsreview_average,productsDescription,productsurl,productsprice,productsstore_name,productsstore_url,productsstore_logo,productscatagory,brand,productsques_count]
sqlproducts=("Insert into products(name,slug,review_count,review_average,Description,url,price,store_name,store_url,store_logo,catagory,brand,ques_count) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
mycursor.execute(sqlproducts,sqlproducts_value)
productid= mycursor.lastrowid
mydb.commit()
print("Products ID--- ",productid)
#DB Catagory 
statusc = 2
mycursor = mydb.cursor(buffered=True)
mycursor.execute("SELECT category FROM categories WHERE category = '{0}'".format(productscatagory))
c_name = mycursor.fetchone()
if c_name == None:
    mycursor = mydb.cursor(buffered=True)
    sqlproduct_cat_info="Insert into categories(category,status,created_at,updated_at) values(%s,%s,%s,%s)"
    sqlproduct_cat_info_value=(productscatagory,statusc,now,now)
    mycursor.execute(sqlproduct_cat_info,sqlproduct_cat_info_value)
    mydb.commit()
else:
    pass
# DB Brands
mycursor = mydb.cursor(buffered=True)
mycursor.execute("SELECT brandName FROM brand_logos WHERE brandName = '{0}'".format(productsstore_name))
bn_name = mycursor.fetchone()
if bn_name == None:
    mycursor = mydb.cursor(buffered=True)
    sqlproduct_br_info="Insert into brand_logos(brandName,brandLogo,created_at,updated_at) values(%s,%s,%s,%s)"
    sqlproduct_br_info_value=(productsstore_name,productsstore_logo,now,now)
    mycursor.execute(sqlproduct_br_info,sqlproduct_br_info_value)
    mydb.commit()
else:
    pass
print("Products Brands name -- ",productsstore_name)
print("Products Category name -- ",productscatagory)
print("Products Store name -- ",productsstore_name)
print("Products Store URL -- ",productsstore_url, "\n")
#product_info Table
product_info_partent=soup.find("a" ,id ="productDetails").parent
items=[]
velues = product_info_partent.find_all("td")
countinfo=0
for item_name in product_info_partent.find_all("th"):
    product_infoname_f=item_name.text.replace('  ','').replace('\n','')
    product_infovalue_f=velues[countinfo].text.replace('  ','').replace('\n','')
    countinfo=countinfo+1
    mycursor = mydb.cursor(buffered=True)
    mycursor.execute("SELECT type FROM products_infos WHERE name = '{0}'".format(product_infoname_f))
    p_name = mycursor.fetchone()
    if p_name == None:
        p_type = "Technical Information"
    else:
        p_type = p_name[0]
# DB products_info
    mycursor = mydb.cursor(buffered=True)
    sqlproduct_info="Insert into products_infos(product_id,type,name,value) values(%s,%s,%s,%s)"
    sqlproduct_info_value=(productid,p_type,product_infoname_f,product_infovalue_f)
    mycursor.execute(sqlproduct_info,sqlproduct_info_value)
    product_info_id= mycursor.lastrowid
    mydb.commit()
print("Successfully collect Product info\n")
# Image table

print("---",productscatagory,"----")
imagesurl = soup.find("img" ,class_ ="a-dynamic-image").attrs['src']
print("Products img url: ",imagesurl)
print("Products Store name : ",productsstore_name,"\n")
print("Products Store img url: ",productsstore_logo,"\n")
# DB image
mycursor = mydb.cursor()
sqlimages_value=[productid,imagesurl]
sqlimages=("Insert into product_images(product_id,url) values(%s,%s)")
mycursor.execute(sqlimages,sqlimages_value)
mydb.commit()
# Review typ def 
df = pd.read_csv('Restaurant_Reviews.tsv', delimiter = '\t')
def rr_view(ttxxtt):
    corpus = []
    for i in range(0, 1000):
        review = re.sub('[^a-zA-Z]', ' ', df['Review'][i])
        review = review.lower()
        review = review.split()
        ps = PorterStemmer()
        all_stopwords = stopwords.words('english')
        all_stopwords.remove('not')
        review = [ps.stem(word) for word in review if not word in set(all_stopwords)]
        review = ' '.join(review)
        corpus.append(review)
    ## Creating the Bag of Words model
    cv = CountVectorizer(max_features = 1500)
    X = cv.fit_transform(corpus).toarray()
    y = df.iloc[:, -1].values
    ## Splitting the dataset into the Training set and Test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.35, random_state = 0)
    ## Training the SVM model on the Training set

    classifier = SVC(kernel = 'linear', random_state = 0)
    classifier.fit(X_train, y_train)

    ## Positive review
    new_review = ttxxtt
    new_review = re.sub('[^a-zA-Z]', ' ', new_review)
    new_review = new_review.lower()
    new_review = new_review.split()
    ps = PorterStemmer()
    all_stopwords = stopwords.words('english')
    all_stopwords.remove('not')
    new_review = [ps.stem(word) for word in new_review if not word in set(all_stopwords)]
    new_review = ' '.join(new_review)
    new_corpus = [new_review]
    new_X_test = cv.transform(new_corpus).toarray()
    new_y_pred = classifier.predict(new_X_test)
    if new_y_pred[0] == 1:
        r_viw_type = "possitive"
    else:
        r_viw_type = "Negative"
    return r_viw_type
# Review Table 
page = requests.get(URL,headers=headinfo).content
soup = BeautifulSoup(page, 'html.parser')
mycursor = mydb.cursor(buffered=True)
query = "SELECT value FROM setting_data WHERE name ='review_save'"
mycursor.execute(query)
myresult = mycursor.fetchone()
review_save = myresult[0]
review_save = int(review_save)

review = soup.find("a" ,attrs={"data-hook":"see-all-reviews-link-foot"}).attrs['href']
if review:
    review_pa =  review.split("?")[0]
    review_page_url = ("https://www.amazon.com"+review_pa)
    review_page = requests.get(review_page_url,headers=headinfo).content
    soup = BeautifulSoup(review_page, 'html.parser')
def reviewcall(soup):
    count = 1
    for customer in soup.find_all("div", class_ = "a-section celwidget"):
        print("Collecting review---", count)
        count += 1
        reviewsuser_name = customer.find("span", class_="a-profile-name").text
        reviewscountry_namex=customer.find("span", class_="a-size-base a-color-secondary review-date").text
        try:
            reviewscountry_namey = reviewscountry_namex.split("the")[1]
        except:
            pass
        try:
            reviewscountry_name = reviewscountry_namey.split("on")[0]
        except:
            pass
        reviewsdatex=customer.find("span", class_="a-size-base a-color-secondary review-date").text
        reviewsdate=reviewsdatex.split("on")[1]
        reviewstext=customer.find("span", class_="a-size-base review-text review-text-content").text
        def clean(text):
    # Removes all special characters and numericals leaving the alphabets
            text = re.sub('[^A-Za-z]+', ' ', text)
            return text
        rc = clean(reviewstext)
        try:
            reviewsstarsx=customer.find("i",attrs={"data-hook":"review-star-rating"}).text
            reviewsstars = float(reviewsstarsx.split(" ")[0])
        except:
            reviewsstars = 3.0
        try:
            reviewshelpfulx=customer.find("span", class_="a-size-base a-color-tertiary cr-vote-text").text
            reviewshelpful=int(reviewshelpfulx.split(" ")[0])
        except:
            reviewshelpful=0
        review_user_url = customer.find("a", class_="a-profile").attrs['href']
        review_user_url = "https://www.amazon.com"+review_user_url.split("?")[0]
        reviewsuser_img = customer.find("img").attrs["data-src"]
        review_ty_po = rr_view(rc)
        print("Review type ", review_ty_po)
#       # DB Review 
        mycursor = mydb.cursor()
        sqlreviews_value=[productid,reviewshelpful,reviewsuser_name,reviewscountry_name,reviewsdate,review_user_url,reviewstext,reviewsstars,reviewsuser_img,review_ty_po]
        sqlreviews="Insert into reviews(product_id,helpful,user_name,country_name,date,user_url,text,stars,user_img,review_type) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        mycursor.execute(sqlreviews,sqlreviews_value)
        mydb.commit()
rp = 1
while True:
    try :
        nextreview = soup.select(".a-last > a:nth-child(1)")
        try:
            nextreviewurl = "https://www.amazon.com"+(nextreview[0].attrs['href'])
        except:
            nextreviewurl=None
        if nextreviewurl:
            reviewcall(soup)
    except:
        nextreviewurl=None
        reviewcall(soup)
    if nextreviewurl:
        reviewpage = requests.get(nextreviewurl,headers=headinfo).content
        soup = BeautifulSoup(reviewpage, 'html.parser')
        print("Review page count---", rp, "\n")
        if review_save != 0:
            if rp == review_save:
                break
        rp += 1
    if not nextreviewurl:
        break
page = requests.get(URL,headers=headinfo).content
soup = BeautifulSoup(page, 'html.parser')
# Db review keywords
def rev_keyword(productid_word,reg="[a-zA-Z]+\s[a-zA-Z]+"):
    mycursor = mydb.cursor(buffered=True)
    query = "SELECT text FROM reviews WHERE product_id={0}".format(productid_word)
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    listall1 =[]
    for item in myresult:
        listall1.append(item)
    listall = []  ### All lower case
    for name in listall1:
        for name1 in name: 
            listall.append(name1.lower())
    counter =[]
    backlist= (",from the,these are,me as,i bought,one i,is it,easy to,so i,this for,because the,set up,but it,at the,i used,to adjust,on amazon,does not,has a,so it,would be,but they,i got,use it,for work,and has,a monitor,as a,this thing,of a,using it,of my,is great,me to,to work,to get,no issues,to a,,a few,my son,though i,s a,get the,my gaming,i love,comes with,is perfect,of it,on it,to this,used to,thing i,with my,monitor i,it for,on this,can be,up to,i really,was a,is the,the only,if it,had to,a little,it has,to have,monitor was,a lot,i could,the bridge,the shipping,this one,the black,bought this,a shipping,there is,with an,which i,it up,i also,into the,if i,i don,the screen,one of,as i,on a,a year,i didn,this monitor,using a,need to,ni bought,what i,i think,middle bracket,use the,going to,a very,did not,to me,the same,happy with,there are,of this,not be,that i,because i,and then,it was,looking for,pushing the,that it,for this,goes wrong,i guess,which is,i need,this is,i needed,using the,but it,monitor and,the product,and this,could not,i had,i do,be loaded,on my,use this,it does,are a,a second,a bit,i like,it was,but not,to be,it is,i would,for a,this is,i have, realized,you get,have a,monitor is,it to,you are,so far,to use,in the,when i,to my,very well,it is,i was,of these,tried to,i found,to make,a good,they are,to the,i did,i use,the job,you can,with a,lot of,out of,this was,have two,i wanted,and they,and a,that is,i will,and the,my old,s not,monitor to,but i,is a,a great,get a,want to,not a,have to,that the,be a,hz and,but the,these monitors,if you,quality is,on the,is that,for my,i am,i can,for the,and i,of the,so i,the price,if you,and it,with the,monitor for")
    backlist=backlist.split(",")
    for reviewitem in listall:
        list1 =re.findall(reg,str(reviewitem))
        for word in list1:
            counter.append(word)
        list2 =re.findall("\s{0}".format(reg),str(reviewitem))
        for word in list2:
            counter.append(word)
    final_count = []
    for remove_space in counter:
        final_count.append(str(remove_space).strip())
    counts = dict(Counter(final_count))
    duplicates = {key:value for key, value in counts.items() if value >5}
    keywords = {i:duplicates[i] for i in duplicates if i not in backlist} ### BlackList word remove
    return keywords

rev_kw_id = productid
ar = rev_keyword(rev_kw_id)
br= rev_keyword(rev_kw_id,'[a-zA-Z]+\s[a-zA-Z]+\s[a-zA-Z]+')
cr= rev_keyword(rev_kw_id,'[a-zA-Z]+\s[a-zA-Z]+\s[a-zA-Z]+\s[a-zA-Z]+')

review_final_word = {**ar, **br,**cr}
json_object = json.dumps(review_final_word)
# Db review keywords
mycursor = mydb.cursor(buffered=True)
sql= "UPDATE products SET review_keywords = %s WHERE id = %s"
mycursor.execute(sql,(str(json_object),rev_kw_id))
mydb.commit()

rv_ks = list(x for x in review_final_word.keys())
word_ava_stars = {}
for ss in rv_ks:
    if "'" in ss:
        continue
    mycursor = mydb.cursor(buffered=True)
    query = "SELECT AVG(stars) FROM reviews WHERE text LIKE '%{0}%' AND product_id={1}".format(ss,productid)
    mycursor.execute(query)
    myresult = mycursor.fetchone()
    word_ava_stars[ss] =round(myresult[0],1)

json_object_avg = json.dumps(word_ava_stars)
# Db review keywords
mycursor = mydb.cursor(buffered=True)
sql= "UPDATE products SET avg_word_review = %s WHERE id = %s"
mycursor.execute(sql,(str(json_object_avg),rev_kw_id))
mydb.commit()

# Question Answer Table
mycursor = mydb.cursor(buffered=True)
query = "SELECT value FROM setting_data WHERE name ='faq_save'"
mycursor.execute(query)
myresult = mycursor.fetchone()
faq_save = myresult[0]
faq_save = int(faq_save)

asin = producturl.split("/")[4]
question_page_url = "https://www.amazon.com/ask/questions/asin/"+asin
question_page = requests.get(question_page_url,headers=headinfo).content
soup = BeautifulSoup(question_page, 'html.parser')
def questioncall(soup):
    allquestion=soup.find("div", class_="a-section askTeaserQuestions")
    perquestion = allquestion.findChildren("div" , recursive=False)
    qc = 1
    for question in perquestion:
        print("Collecting Question---", qc)
        qc += 1
        votes = question.find("span",class_="count").text 
        questionvotes = int(votes)
        question_find = question.select('[id^=question]')[0]
        questionquestion = question_find.text.replace("Question:", "").replace("  ", "").replace("\n", "")
#         # DB question
        mycursor = mydb.cursor()
        sqlquestion="Insert into questions(product_id,votes,question) values(%s,%s,%s)"
        sqlquestion_value=[productid,questionvotes,questionquestion]
        mycursor.execute(sqlquestion,sqlquestion_value)
        questionid = mycursor.lastrowid
        mydb.commit()
        find_ans = question.find("div",class_ = "a-fixed-left-grid a-spacing-base")
        try:
            answersuser_name= find_ans.find("span",class_="a-profile-name").text
            answersdate = find_ans.find("span", class_="a-color-tertiary aok-align-center").text.replace("\n", "").replace("  ", "")
            answerstext =  find_ans.find_all("span")[1].text.replace("\n", "").replace("  ", "")
            answershelpful="yes"
        except:
            answersuser_name= "Empty"
            answersdate = "Empty"
            answerstext = "Empty"
            answershelpful="Empty"
        #DB Answer
        mycursor = mydb.cursor()
        sqlanswers="Insert into answers(question_id,text,date,user_name,helpful) values(%s,%s,%s,%s,%s)"
        sqlanswers_value=[questionid,answerstext,answersdate,answersuser_name,answershelpful]
        mycursor.execute(sqlanswers,sqlanswers_value)
        mydb.commit()
gt = 1
while True:
    try :
        nextquestion = soup.select(".a-last > a:nth-child(1)")
        try:
            nextquestionurl = "https://www.amazon.com"+(nextquestion[0].attrs['href'])
        except:
            nextquestionurl=None
        if nextquestionurl:
            questioncall(soup)
    except:
        nextquestionurl=None
        questioncall(soup)
    if nextquestionurl:
        questionpage = requests.get(nextquestionurl,headers=headinfo).content
        soup = BeautifulSoup(questionpage, 'html.parser')
        print("Question page count---", gt, "\n")
        if faq_save != 0:
            if gt == faq_save:
                break
        gt += 1
    if not nextquestionurl:
        break

# Db FAQ keywords
def faq_keyword(faq_word_id,reg="[a-zA-Z]+\s[a-zA-Z]+"):
    mycursor = mydb.cursor(buffered=True)
    query = "SELECT answers.text,questions.question FROM questions INNER JOIN answers ON questions.id = answers.question_id WHERE questions.product_id = {0};".format(faq_word_id)
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    listall1 =[]
    for item in myresult:
        listall1.append(item)
    listall = []  ### All lower case
    for name in listall1:
        for name1 in name: 
            listall.append(name1.lower())
    counter =[]
    backlist= ("from the,these are,me as,i bought,one i,is it,easy to,so i,this for,because the,set up,but it,at the,i used,to adjust,on amazon,does not,has a,so it,would be,but they,i got,use it,for work,and has,a monitor,as a,this thing,of a,using it,of my,is great,me to,to work,to get,no issues,to a,,a few,my son,though i,s a,get the,my gaming,i love,comes with,is perfect,of it,on it,to this,used to,thing i,with my,monitor i,it for,on this,can be,up to,i really,was a,is the,the only,if it,had to,a little,it has,to have,monitor was,a lot,i could,the bridge,the shipping,this one,the black,bought this,a shipping,there is,with an,which i,it up,i also,into the,if i,i don,the screen,one of,as i,on a,a year,i didn,this monitor,using a,need to,ni bought,what i,i think,middle bracket,use the,going to,a very,did not,to me,the same,happy with,there are,of this,not be,that i,because i,and then,it was,looking for,pushing the,that it,for this,goes wrong,i guess,which is,i need,this is,i needed,using the,but it,monitor and,the product,and this,could not,i had,i do,be loaded,on my,use this,it does,are a,a second,a bit,i like,it was,but not,to be,it is,i would,for a,this is,i have, realized,you get,have a,monitor is,it to,you are,so far,to use,in the,when i,to my,very well,it is,i was,of these,tried to,i found,to make,a good,they are,to the,i did,i use,the job,you can,with a,lot of,out of,this was,have two,i wanted,and they,and a,that is,i will,and the,my old,s not,monitor to,but i,is a,a great,get a,want to,not a,have to,that the,be a,hz and,but the,these monitors,if you,quality is,on the,is that,for my,i am,i can,for the,and i,of the,so i,the price,if you,and it,with the,monitor for")
    backlist=backlist.split(",")
    for reviewitem in listall:
        list1 =re.findall(reg,str(reviewitem))
        for word in list1:
            counter.append(word)
        list2 =re.findall("\s{0}".format(reg),str(reviewitem))
        for word in list2:
            counter.append(word)
    final_count = []
    for remove_space in counter:
        final_count.append(str(remove_space).strip())
    counts = dict(Counter(final_count))
    duplicates = {key:value for key, value in counts.items() if value >5}
    keywords = {i:duplicates[i] for i in duplicates if i not in backlist} ### BlackList word remove
    return keywords

faq_kw_id = productid
arf = faq_keyword(faq_kw_id)
brf= faq_keyword(faq_kw_id,'[a-zA-Z]+\s[a-zA-Z]+\s[a-zA-Z]+')
crf= faq_keyword(faq_kw_id,'[a-zA-Z]+\s[a-zA-Z]+\s[a-zA-Z]+\s[a-zA-Z]+')
faq_final_word = {**arf, **brf,**crf}
json_object_faq = json.dumps(faq_final_word)

# Db review keywords
mycursor = mydb.cursor(buffered=True)
sql= "UPDATE products SET faq_keywords = %s WHERE id = %s"
mycursor.execute(sql,(str(json_object_faq),faq_kw_id))
mydb.commit()
mycursor.close()
mydb.close()
print("Products Details collect Complete.")
