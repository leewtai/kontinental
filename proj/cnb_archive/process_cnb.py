import re
import matplotlib.pyplot as plt
import pandas as pd
import spacy
import wordcloud

articles = pd.read_csv("cnb_articles.csv")
df = articles[['title', 'date', 'article']]
df['year'] = df.date.apply(lambda x: x[:4])

nlp = spacy.load('en_core_web_sm')

df_grp = df.groupby('year')

verb_years = {}
for year in df_grp.groups:
    print(year)
    verbs = []
    sdf = df_grp.get_group(year)
    for i, row in sdf.iterrows():
        text = re.sub('[ \n]+', ' ', row.title + '. ' + row.article)
        doc = nlp(text)
        # doc = nlp(row.title)
        verbs.extend(token.lemma_ for token in doc if token.pos_ == 'VERB')
    verb_years.update({year: verbs})

for year in verb_years:
    wc = wordcloud.WordCloud(collocations=False).generate(' '.join(verb_years.get(year)))
    plt.imshow(wc, interpolation='bilinear')
    # plt.title('Verbs in CNB News Headlines - {}'.format(year))
    plt.title('Verbs in CNB News Articles - {}'.format(year))
    plt.savefig('cnb_verbs_{year}_article.png'.format(year=year))
    # plt.savefig('cnb_verbs_{year}.png'.format(year=year))
    plt.close()
