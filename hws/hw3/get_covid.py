import re
import logging
import matplotlib.pyplot as plt
import time
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import shape

logging.basicConfig(format="%(asctime)-15s %(message)s",
                    filename='covid_health_data.log',
                    level=logging.WARNING)
URL = "https://healthdata.gov/resource/anag-cw7u.json"

# If we want all the data
OFFSET = 0
record_cap = 50000
start_time = time.time()
dats = []
while OFFSET < 1:
    logging.info('offset is at %d', OFFSET)
    logging.info('time elapsed is %d seconds', (time.time() - start_time))
    resp = requests.get(
        url=URL,
        params={"$limit": record_cap, "$offset": OFFSET})
    assert resp.status_code == 200
    dat = pd.DataFrame(resp.json())
    dats.append(dat)
    if len(dat) < record_cap:
        break
    OFFSET += record_cap

df = pd.concat(dats)

# Plot same graphic?
condition = dat.collection_week == dat.collection_week.max()
condition2 = dat.geocoded_hospital_address.apply(lambda x: isinstance(x, dict))
assert condition.sum() > 4000

# coordinates on geocoded_hospital_address
sdf = dat.loc[condition & condition2,:]
geoms = [shape(geojson) for geojson in sdf.geocoded_hospital_address]
personnel_cols = [col for col in sdf.columns if re.search('total_personnel', col)]
sdf.loc[:, personnel_cols] < 0

total_staff = (
    sdf.total_personnel_covid_vaccinated_doses_none_7_day
    + sdf.total_personnel_covid_vaccinated_doses_one_7_day
    + sdf.total_personnel_covid_vaccinated_doses_all_7_day)

gdf = gpd.GeoDataFrame({'total_personnel_covid_vaccinated_doses_all_7_day': sdf.total_personnel_covid_vaccinated_doses_all_7_day, 'geometry': geoms})



not_conus = ['Hawaii', 'Alaska', 'Commonwealth of the Northern Mariana Islands',
             'Puerto Rico', 'American Samoa', 'Guam']
# https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
states = gpd.read_file("cb_2018_us_state_5m/cb_2018_us_state_5m.shp")
conus = states.loc[states.NAME.apply(lambda x: x not in not_conus), :]
min_bounds = conus.geometry.bounds.loc[:, ['minx', 'miny']].min()
max_bounds = conus.geometry.bounds.loc[:, ['maxx', 'maxy']].max()

base = conus.plot(color='#AAAAAA')
gdf.plot(ax=base, marker='o', color='red', markersize=gdf.)
#plt.xlim((min_bounds.minx, max_bounds.maxx))
#plt.ylim((min_bounds.miny, max_bounds.maxy))
plt.savefig('states.png')
plt.close()



