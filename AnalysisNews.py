import pandas as pd
import re
from keras.preprocessing import sequence
from sklearn.model_selection import train_test_split
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import Embedding
from keras.layers import LSTM
from keras.layers import Activation
import numpy as np

xlsFileName = 'ThreadsNewsData.xls'
dataF = pd.read_excel(xlsFileName)
keyValueFrame = dataF[['category','title']]

#分类的转换比较容易，可以将所有分类从 1 开始映射，首先生成一个分类的列表，然后生成两个字典，分别是 分类名称:数字 以及 数字:分类名称 的字典，方便映射和查找
catagories = keyValueFrame.groupby('category').size().index.tolist()
catagory_dict = {}
int_catagory = {}
for i, k in enumerate(catagories):
    catagory_dict.update({k:i})
    int_catagory.update({i:k})

#dataframe 加上一个映射的 column，使用 apply 方法：
keyValueFrame['c2id'] = keyValueFrame['category'].apply(lambda x: catagory_dict[x])
#这样就完成了 category 到 数字的映射，重新取 title，c2id 两列来准备接下来的工作：
prepared_data = keyValueFrame[ ['title', 'c2id'] ]
#print(keyValueFrame['category'])


#因为我们最终的目的是用作新数据的分类，所以用单字进行转换映射较好。
prepared_data['words'] = prepared_data['title'].apply(lambda x: re.findall('[\x80-\xff]{3}|[\w\W]', x))
# print(prepared_data)

#生成字的映射字典：
all_words = []
for w in prepared_data['words']:
    all_words.extend(w)
word_dict = pd.DataFrame(pd.Series(all_words).value_counts())
word_dict['id'] = list(range(1, len(word_dict)+1))
# print(word_dict)

#字映射为数字
prepared_data['w2v'] = prepared_data['words'].apply(lambda x: list(word_dict['id'][x]))
print(prepared_data)
#然后补全或者截断为固定长度为 25 的队列 ( 新闻标题一般不会超过 25 个字 )：
maxlen = 25
prepared_data['w2v'] = list(sequence.pad_sequences(prepared_data['w2v'], maxlen=maxlen))
# print(prepared_data)

#生成训练数据和测试数据,简单地使用 sklearn.model_selection 的 train_test_split 随机将所有数据以 3:1 的比例分隔为训练数据和测试数据：
seed = 7
X = np.array(list(prepared_data['w2v']))
Y = np.array(list(prepared_data['c2id']))
x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.25, random_state=seed)
y_train = np_utils.to_categorical(y_train)
y_test = np_utils.to_categorical(y_test)

#建立模型
model = Sequential()
model.add(Embedding(len(word_dict)+1, 256))
model.add(LSTM(256))
model.add(Dropout(0.5))
model.add(Dense(y_train.shape[1]))
model.add(Activation('softmax'))
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
#训练
model.fit(x_train, y_train, batch_size=128, epochs=20)
#测试
model.evaluate(x=x_test, y=y_test)

model.save('model.hdf5')

import pickle
def save_obj(obj, name ):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

save_obj(int_catagory, 'int_catagory')
save_obj(catagory_dict, 'catagory_dict')
word_dict.to_csv('word_dict.csv', encoding='utf8')
prepared_data.to_csv('prepared_data.csv', encoding='utf8')

