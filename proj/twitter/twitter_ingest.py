import logging
from datetime import datetime, timedelta
from pathlib import Path

import json
from base64 import b64encode
from urllib.parse import quote

import requests

log_file = 'twitter_ingest.log'
logging.basicConfig(format="%(asctime)-15s %(message)s",
                    filename=log_file,
                    level=logging.INFO)

cred_file = Path('../../.creds')
creds = json.load(cred_file.open('r', encoding='utf-8'))
twitter_api_key = creds['twitter_api_key']
twitter_api_secret_key = creds['twitter_api_secret_key']
OUTFILE = Path('singapore_twitter.json')

SEARCH_URL = 'https://api.twitter.com/2/tweets/search/recent'

bearer_token = (quote(twitter_api_key)
                + ':'
                + quote(twitter_api_secret_key))
bearer_b64 = b64encode(bytes(bearer_token, 'utf-8')).decode('utf-8')

# Create the necessary inputs, in the right format to
# communicate with Twitter's API
auth_headers = {
    'Authorization': 'Basic {}' + bearer_b64,
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }
auth_response = requests.post(url='https://api.twitter.com/oauth2/token',
                              headers=auth_headers,
                              data={'grant_type': 'client_credentials'})
headers = {
    'Authorization': 'Bearer ' + auth_response.json()['access_token']
}
# These are the parameters to customize my query
twitter_queries = ['singapore ((death penalty) OR (capital punishment))',
                   'singapore -(death penalty) -(capital punishment)',
                   'singapore (drug OR narcotics)']
if OUTFILE.exists():
    out = json.load(OUTFILE.open('r', encoding='utf-8'))
else:
    out = []

temp_out = []
next_token = ''
rate_cap = int(420 / len(twitter_queries))
for tq in twitter_queries:
    counter = 0
    while counter < rate_cap:
        start_time = datetime.utcnow() - timedelta(days=7, minutes=-5)
        end_time = datetime.utcnow() - timedelta(days=6)

        params = {
            'query': tq,
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'user.fields': 'name,entities,id,username,verified,public_metrics,location',
            'max_results': 100,
            'tweet.fields': ('author_id,created_at,entities,public_metrics,'
                             'referenced_tweets,source,text,reply_settings,'
                             'in_reply_to_user_id'),
            'place.fields': 'country,country_code,geo,full_name,name,place_type',
            'expansions': ('author_id,entities.mentions.username,in_reply_to_user_id,'
                           'referenced_tweets.id.author_id,referenced_tweets.id,geo.place_id')
        }
        if next_token:
            params.update({'next_token': next_token})

        response = requests.get(url=SEARCH_URL,
                                params=params,
                                headers=headers)
        assert response.status_code == 200
        results = response.json()['data']
        meta = response.json()['meta']
        if not meta['result_count']:
            logging.info('no results seen after %d records with %s',
                counter * params['max_results'] + len(results), tq)
            break
        counter += 1
        temp_out.extend(results)
        next_token = meta.get('next_token')
        if not next_token:
            logging.info('exhausted next tokens for query %s', tq)
            break
        if counter == rate_cap:
            logging.info('hit max iteration cap for query %s', tq)
            break


out.extend(temp_out)
json.dump(out, OUTFILE.open('w', encoding='utf-8'))
