import logging
logging.basicConfig(filename='chinanews.log', format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
import time
from urllib import request as requests
from bs4 import BeautifulSoup
import threading
import time
import xlwt
import xlrd
from datetime import datetime, timedelta
from queue import Queue

def set_style(name, height, bold=False):
    style = xlwt.XFStyle()  # 初始化样式
    font = xlwt.Font()  # 为样式创建字体
    font.name = name  # 'Times New Roman'
    font.bold = bold
    font.color_index = 4
    font.height = height
    style.font = font
    return style



#creat xls
xlsFileName = 'ThreadsNewsData.xls'
workbook = xlwt.Workbook(encoding='utf-8')
data_sheet = workbook.add_sheet('key_value_data')
row0 = [u'url',u'category',u'title']
#生成第一行
for i in range(0,len(row0)):
    data_sheet.write(0,i,row0[i],set_style('Times New Roman',220,True))
workbook.save(xlsFileName)

threadLock = threading.Lock()
threads = []
mQueue = Queue()


#parse html
def fetch_oneday(whichday):
    try:
        year, month_day = whichday.split('-')
    except:
        return None
    base_url = "http://www.chinanews.com/scroll-news/%s/%s/news.shtml" % (year, month_day)
    try:
        # resp = requests.get(base_url, timeout=10)
        resp =requests.urlopen(base_url, timeout=10)
        html_text = resp.read().decode('gbk')
        soup = BeautifulSoup(html_text, "html.parser")
        content = soup.find('div', class_='content_list')
        li = content.find_all("li")
        cnt = 0

        fatchDataList = []
        for item in li:
            try:
                category = item.find('div', class_='dd_lm').text.replace(r'[', '').replace(r']', '')
                title = item.find('div', class_='dd_bt').text
                href = item.find('div', class_='dd_bt').a.attrs['href']
                di = {'category':category, 'title':title}
                fatchDataList.append(FetchData(href,category,title))
            except Exception as e:
                print("parse error= %s"% e)
                continue
        print("%s/%s stored %d news" % (year, month_day, cnt))
        return fatchDataList
    except Exception as e:
        logging.error("failed on getting urls from %s, error=%s" % (base_url,e))
        return None

class FetchData:
    def __init__(self,href,category,title):
        self.href = href
        self.category = category
        self.title = title

class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        print("开始线程：" + self.name)
        while not mQueue.empty():
            argument = mQueue.get()
            result = fetch_oneday(argument)
            for data in result:
                if data is not None:
                    threadLock.acquire()
                    saveDataToXls(data.href, data.category, data.title)
                    print('save a data')
                    threadLock.release()
        print ("退出线程：" + self.name)


# save data to xls
def saveDataToXls(href, value1, value2):
    # Get Rows
    try:
        book = xlrd.open_workbook(xlsFileName)
        sheet = book.sheets()[0]
        # write data
        data_sheet.write(sheet.nrows, 0, href)
        data_sheet.write(sheet.nrows, 1, value1)
        data_sheet.write(sheet.nrows, 2, value2)
        workbook.save(xlsFileName)
        print('row%s----' % sheet.nrows)
    except Exception as e:
        print("save error= %s" % e)


if __name__ == "__main__":
    today = datetime.today()
    NUM = 8
    JOBS = 1500

    for i in range(1, 1500):
        whichday = (today - timedelta(days=i)).strftime("%Y-%m%d")
        print("start parese index=%d ---------day=%s"%(i,whichday))
        mQueue.put(whichday)

    argument = mQueue.get()

    # fork NUM个线程等待队列
    for i in range(NUM):
        t = myThread(i, "Thread-%d"% i, i)
        # t.setDaemon(True)
        t.start()
        print('start Thread %d'%i)
