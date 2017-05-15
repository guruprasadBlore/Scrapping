import re
import sys
import MySQLdb
from threading import Thread
from Queue import Queue
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC




connection = MySQLdb.connect(host="localhost",user="root",passwd="root",db="sample") #Connect to db
cursor = connection.cursor()



def scrapForResults(destination):
    """Method to scrap the website and update the db with results"""

    url = 'http://www.example.com'

    # Use FireFox webdriver(Gecko)
    browser = webdriver.Firefox( executable_path=
             "Path to geckodriver" )
    browser.implicitly_wait(10)
    browser.get(url)

    #Fill the form

    place = browser.find_element_by_id('ss')
    place.clear()
    place.send_keys(destination)

    inmonth = browser.find_element_by_name('checkin_month')
    inmonth.clear()
    inmonth.send_keys(5)

    inday = browser.find_element_by_name('checkin_monthday')
    inday.clear()
    inday.send_keys(29)

    inyear = browser.find_element_by_name('checkin_year')
    inyear.clear()
    inyear.send_keys(2017)

    outmonth = browser.find_element_by_name('checkout_month')
    outmonth.clear()
    outmonth.send_keys(5)

    outday = browser.find_element_by_name('checkout_monthday')
    outday.clear()
    outday.send_keys(30)

    outyear = browser.find_element_by_name('checkout_year')
    outyear.clear()
    outyear.send_keys(2017)

    button = browser.find_element_by_class_name("sb-searchbox__button")
    button.submit()                  #Submitting the form with data

    WebDriverWait(browser, 20).until(
    EC.presence_of_element_located((By.CLASS_NAME, "sr-hotel__name"))) #Wait For results page

    soup = BeautifulSoup(browser.page_source, "html5lib") # Create soup object of the marker
    breadcrumb = soup.find("div",class_="breadcrumb")
    atags = breadcrumb.find_all("a")
    state = atags[2].text
    city = atags[3].text

    #Search for fields from soup object
    for rtdiv in soup.find_all("div", class_="rlt-right"):
        bookingCount = 0
        duration = "0"
        for property in rtdiv.find_all("div", class_="sr_item"):
            name = property.find('span', class_="sr-hotel__name")
            PropName = ""
            if name:
                PropName = name.text.strip('\n')
                PropName.encode( 'utf-8' )
                PropName = "".join(PropName.split("'"))

            lastbooking = property.find( 'div', class_='lastbooking' )
            if lastbooking:
                lstbooking = lastbooking.text
                sObj = re.search( r'.*(\d+).*(\d+)', lstbooking )
                if sObj:
                    bookingCount = sObj.group(1)
                    duration = sObj.group(2)
                    duration.encode( 'utf-8' )
            strikeprice = property.find( 'span', class_='strike-it-red_anim' )
            stkprice = "0"
            if strikeprice:
                orgprice = strikeprice.find( 'span' ).text
                stkObj = re.search(r'(\d+),(\d+)', orgprice)
                if stkObj:
                    stkprice = str(stkObj.group(1)) + str(stkObj.group(2))
                    stkprice.encode('utf-8')
            price = property.find('strong', class_='price')
            cost = "0"
            if price:
                pObj = re.search(r'(\d+),(\d+)', price.find('b').text)
                cost = pObj.group(1) + pObj.group(2)
                cost.encode('utf-8')
            avaialble = property.find('a', class_='b-button')
            aval = 1
            if avaialble:
                vacant = avaialble.find('span', 'b-button__text').text
                aObj = re.search(r'(\d+).*', vacant)
                if aObj:
                    aval = int(aObj.group(1))

            query = ( "insert into sample.hotels (Name,BookingCnt,Duration,StrikePrice,Discountprice,AvailableRooms,State,City)"
                     " values ('%s','%s','%s','%s','%s','%s','%s','%s')" % (
                     PropName, bookingCount, duration, stkprice, cost, aval, state, city))
            connection.set_character_set('utf8')
            try:
                cursor.execute(query)  # Update db with results
                connection.commit()
            except MySQLdb.Error:
                sys.exit("Database connection error")

    browser.quit()


class ScrapingThread(Thread):
    def __init__(self):
        super(ScrapingThread,self).__init__()

    def run(self):
        if not dstqueue.empty():
            mydst = dstqueue.get()
            scrapForResults(mydst)
            dstqueue.task_done()


dstqueue = Queue()
for dst in destinations:
    dstqueue.put(dst)

for i in range(len(destinations)):
    t = ScrapingThread()
    t.start()

dstqueue.join()
connection.close()




