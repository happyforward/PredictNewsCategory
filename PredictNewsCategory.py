import re
import ast
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from keras.preprocessing import sequence
from keras.utils import np_utils
from keras.models import load_model

# 导入数据
word_dict = pd.read_csv('word_dict.csv', encoding='utf8')
word_dict = word_dict.drop(['0'], axis=1)
word_dict.columns = ['0', 'id']

import pickle
def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)

int_catagory = load_obj('int_catagory')
catagory_dict = load_obj('catagory_dict')


# 导入模型
model = load_model('model.hdf5')

maxlen=25

# 预测函数
def predict_(title):
    words = re.findall('[\x80-\xff]{3}|[\w\W]', title)
    w2v = [word_dict[word_dict['0']==x]['id'].values[0] for x in words]
    xn = sequence.pad_sequences([w2v], maxlen=maxlen)
    predicted = model.predict_classes(xn, verbose=0)[0]
    return int_catagory[predicted]

# 前三种可能性分类
def predict_3(title):
    words = re.findall('[\x80-\xff]{3}|[\w\W]', title)
    w2v = [word_dict[word_dict['0']==x]['id'].values[0] for x in words]
    xn = sequence.pad_sequences([w2v], maxlen=maxlen)
    predicted = model.predict(xn, verbose=0)[0]
    predicted_sort = predicted.argsort()
    li = [(int_catagory[p], predicted[p]*100) for p in predicted_sort[-3:]]
    return li[::-1]


# 拉取当天新闻并预测, 测试准确率

def check_news_today():
    today = datetime.today().strftime("%Y-%m%d")
    year, month_day = today.split('-')
    base_url = "http://www.chinanews.com/scroll-news/%s/%s/news.shtml" % (year, month_day)
    resp = requests.get(base_url, timeout=10)
    resp.encoding = "gbk"
    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.find('div', class_='content_list')
    li = content.find_all("li")
    count = 0
    match = 0
    for item in li:
        try:
            catagory = item.find('div', class_='dd_lm').text.replace(r'[', '').replace(r']', '')
            if catagory in ['', u'图片', u'视频', u'报摘']:
                continue
            title = item.find('div', class_='dd_bt').text
            href = item.find('div', class_='dd_bt').a.attrs['href']
            prediction = predict_(title)
            print("[%s] prediction:[%s] %s" % (catagory, prediction, title))
            if catagory == prediction:
                match += 1
            count += 1
        except:
            continue
    print("acc: %.2f%% (%d/%d)" % (float(100 * match) / count, match, count))


def check_news_today_3():
    today = datetime.today().strftime("%Y-%m%d")
    year, month_day = today.split('-')
    base_url = "http://www.chinanews.com/scroll-news/%s/%s/news.shtml" % (year, month_day)
    resp = requests.get(base_url, timeout=10)
    resp.encoding = "gbk"
    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.find('div', class_='content_list')
    li = content.find_all("li")
    count = 0
    match = 0
    for item in li:
        try:
            catagory = item.find('div', class_='dd_lm').text.replace(r'[', '').replace(r']', '')
            if catagory in ['', u'图片', u'视频', u'报摘']:
                continue
            title = item.find('div', class_='dd_bt').text
            href = item.find('div', class_='dd_bt').a.attrs['href']
            prediction = predict_3(title)
            print ("[%s] prediction:[%s(%.2f%%) %s(%.2f%%) %s(%.2f%%)] %s" % \
            (catagory, prediction[0][0], prediction[0][1], prediction[1][0], prediction[1][1], prediction[2][0],
             prediction[2][1], title))
            if catagory in [prediction[0][0], prediction[1][0], prediction[2][0]]:
                match += 1
            count += 1
        except:
            continue
    print("acc: %.2f%% (%d/%d)" % (float(100 * match) / count, match, count))


#预测今天数据
check_news_today()