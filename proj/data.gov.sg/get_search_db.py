import requests
import pandas as pd

params = {"resource_id": "85be5dcc-93f6-4d36-ae10-c85b0907948c",
          "limit": 7000}
resp = requests.get("https://data.gov.sg/api/action/datastore_search",
                    params=params)
assert resp.status_code == 200
result = resp.json()['result']
result.keys()
assert result.get('total') < result.get('limit'), 'There may be more datasets not queried'

df = pd.DataFrame(result.get('records'))
df.to_csv("data_gov_sg_search_db.csv")

df.frequency.value_counts()
fast_stat = df.frequency.apply(lambda x: x in ['Daily', 'Weekly', 'Realtime'])
df.loc[fast_stat].organisation.value_counts()
df.loc[df.organisation == 'SkillsFuture Singapore', :]

has_foreign = df.description.apply(lambda x: x.lower().find('foreign') > 0)
has_foreign.sum()
df.loc[has_foreign, 'description']
