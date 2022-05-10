import re

import requests
import pandas as pd


# Article in March 2022
# Links pulled from https://www.straitstimes.com/singapore/more-than-80-of-sporeans-surveyed-believe-death-penalty-has-deterred-offenders-shanmugam?utm_source=Telegram&utm_medium=Social&utm_campaign=STTG
data_links = {'kidnapping': 'https://datawrapper.dwcdn.net/ReCdz/1/dataset.csv',
              'firearm': 'https://datawrapper.dwcdn.net/WOLys/1/dataset.csv'}


for crime, link in data_links.items():
    resp = requests.get(url=link)
    rows = resp.text.split('\n')
    dat = [row.split('\t') for row in rows]
    df = pd.DataFrame(dat, columns=['year', 'cases'])
    df.to_csv('data/scraped_straitstimes_{}.csv'.format(crime))
