import re
from datetime import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import spacy
import wordcloud

articles = pd.read_csv("cnb_articles.csv")
df = articles[['title', 'date', 'article']]
df['year'] = df.date.apply(lambda x: x[:4])

df.loc[:, 'date'] = pd.to_datetime(df.date)
nlp = spacy.load('en_core_web_sm')

cnb_verbs = []
for _, row in df.iterrows():
    if 'CNB' not in row.title:
        cnb_verbs.append([])
        continue
    doc = nlp(row.title)
    ## Find the verb that follows CNB immediately
    verbs = []
    for i, token in enumerate(doc):
        if token.text != 'CNB':
            continue
        if (len(doc) == i + 1) or doc[i + 1].text == "'s":
            # removes cases like "the CNB's sting operations"
            continue
        for j in range(i + 1, len(doc)):
            if doc[j].pos_ != 'VERB':
                continue
            verbs.append(doc[j].lemma_)
            break
    # keep unique words only
    cnb_verbs.append(list(set(verbs)))


max(map(len, cnb_verbs))
cnb_verbs = [verbs[0] if verbs else '' for verbs in cnb_verbs]
df['cnb_verb'] = cnb_verbs

df_grp = df.groupby('year')

for year in df_grp.groups:
    sdf = df_grp.get_group(year)
    verbs = [s for s in sdf.cnb_verb if s]
    if not verbs:
        continue
    combined_verbs = ' '.join(verbs)
    wc = wordcloud.WordCloud(collocations=False).generate(combined_verbs)
    plt.imshow(wc, interpolation='bilinear')
    # plt.title('Verbs in CNB News Headlines - {}'.format(year))
    plt.title('Verbs in CNB News Articles - {}'.format(year))
    plt.savefig('cnb_verbs_{year}_article.png'.format(year=year))
    # plt.savefig('cnb_verbs_{year}.png'.format(year=year))
    plt.close()


