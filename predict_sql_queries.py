import pandas as pd
import nltk
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from nltk.stem import WordNetLemmatizer


def build_model():
    text = pd.read_csv("datasets/plain.txt", sep='\n', skiprows=2, header=None)
    text.head()
    text.rename(columns={0: 'txt'}, inplace=True)
    text2 = pd.read_csv("datasets/sql_querys.txt", sep='\n', header=None)
    s1 = list(text['txt'])
    s2 = list(text2[0])
    s1 = [i.lower() for i in s1]
    s2 = [i.lower() for i in s2]
    y1 = [0 for i in range(len(s1))]
    y2 = [1 for i in range(len(s2))]
    y = y1 + y2

    word_lem = WordNetLemmatizer()

    new_s1 = []
    stopwords = nltk.corpus.stopwords.words("english")
    for i in s1:
        temp = i.split(' ')
        temp1 = []
        for j in temp:

            j = j.strip(',').strip(r'["]').strip(';').strip('“').strip('”').strip(r'[.]+')
            j = j.replace("’", '')
            if j not in stopwords and j.isalpha():
                j = word_lem.lemmatize(j)
                temp1.append(j)

        new_s1.append(' '.join(temp1))

    new_s2 = []
    for i in s2:
        temp = i.split(' ')
        temp1 = []
        for j in temp:
            if j not in stopwords:
                j = word_lem.lemmatize(j)
                temp1.append(j)

        new_s2.append(' '.join(temp1))

    new_s = new_s1 + new_s2

    tokenizer1 = Tokenizer(num_words=100000, oov_token="<OOV>")
    tokenizer1.fit_on_texts(new_s)

    model = load_model("model/model.h5")
    return model, tokenizer1


"""
entry = input("Please enter sql query for check: ")
entry = entry.lower()
temp = []
temp.append(entry)

token = tokenizer1.texts_to_sequences(temp)
pad = pad_sequences(token, maxlen=150, padding="post")

decision = model.predict_proba(pad)[0][0]

if decision < 0.6:
    print(f"{entry} - is not identified as a malicious query")
else:
    print(f"{entry} - is identified as a malicious query !!!")
"""