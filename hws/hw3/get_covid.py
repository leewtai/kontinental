import re
import logging
import time
import numpy as np
import matplotlib.pyplot as plt
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
RECORD_CAP = 50000
start_time = time.time()
dats = []

while True:
    resp = requests.get(
        url=URL,
        params={"$limit": RECORD_CAP, "$offset": OFFSET,
                "$where": "collection_week > '2022-01-01T00:00:00'"})
    assert resp.status_code == 200
    dat = resp.json()
    dats.append(pd.DataFrame(dat))
    if len(dat) < RECORD_CAP:
        break
    OFFSET += RECORD_CAP
    logging.info('offset is at %d', OFFSET)
    logging.info('time elapsed is %d seconds', (time.time() - start_time))

df = pd.concat(dats)
logging.info('pulled %d records from health.gov', df.shape[0])

personnel_cols = [col for col in df.columns
                  if re.search('total_personnel', col)]
pers_df = df.loc[:, personnel_cols].astype(float)
pers_df[pers_df <0] = np.nan
# Leave NAs to calc percentage
df['total_personnel'] = pers_df.apply(sum, 1)
df['perc_unvax'] = (
    df.total_personnel_covid_vaccinated_doses_none_7_day.astype(float) / df.total_personnel
    * 100)

# Plot same graphic?
target_week = df.collection_week.max()
condition = df.collection_week == target_week
condition2 = df.geocoded_hospital_address.apply(lambda x: isinstance(x, dict))
assert condition.sum() > 4000

# coordinates on geocoded_hospital_address
sdf = df.loc[condition & condition2,:]
geoms = [shape(geojson) for geojson in sdf.geocoded_hospital_address]

gdf = gpd.GeoDataFrame({
    'total_personnel_reported': sdf.total_personnel.to_list(),
    'perc_unvax': sdf.perc_unvax,
    'beds_to_staff_ratio': (
        sdf.total_personnel
        / sdf.total_beds_7_day_avg.astype(float)).to_list(),
    'geometry': geoms})

not_conus = ['Hawaii', 'Alaska', 'Commonwealth of the Northern Mariana Islands',
             'Puerto Rico', 'American Samoa', 'Guam']
# https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
states = gpd.read_file("cb_2018_us_state_5m/cb_2018_us_state_5m.shp")
conus = states.loc[states.NAME.apply(lambda x: x not in not_conus), :]

conus_gdf = gdf.loc[(gdf.bounds.minx >= conus.bounds.minx.min())
                    & (gdf.bounds.miny >= conus.bounds.miny.min())
                    & (gdf.bounds.maxx <= conus.bounds.maxx.max())
                    & (gdf.bounds.maxy <= conus.bounds.maxy.max()),:]

marker_legends = [1, 30, 60, 100]
tot_max = conus_gdf.total_personnel_reported.max()
markersize = 100 * (conus_gdf.total_personnel_reported
                    / tot_max)
conus_gdf['total_reported'] = markersize
fig, ax = plt.subplots(figsize=(10, 7))
ax.set_facecolor('#AAAAAA')
conus.plot(color='#444444', ax=ax)
conus_gdf.plot(ax=ax, marker='o', markersize='total_reported',
               cmap='Greens', column="perc_unvax", legend=True,
               legend_kwds={'label': 'unvaccinated %'})
# Hack to get legends for marker size
legends = [plt.scatter([], [], s=i, edgecolor=None, color='grey')
           for i in marker_legends]
plt.legend(legends, [round(tot_max * i / 100) for i in marker_legends],
           loc='lower right', title='Total reported')
data_week = target_week[:10]
plt.title(f'Percent unvaccinated hospital personnel on week {data_week}')
plt.savefig('reproduce_unvaccinated.png')
plt.close()


not_inf = np.logical_not(np.isinf(conus_gdf.beds_to_staff_ratio))
markersize = 100 * (conus_gdf.beds_to_staff_ratio
                    / conus_gdf.beds_to_staff_ratio[not_inf].max())
base = conus.plot(color='#AAAAAA')
conus_gdf.plot(ax=base, marker='o', markersize=markersize,
               color='green')
plt.title(f'Total beds to staff ratio on week {data_week}')
plt.savefig('bed_to_staff_ratio.png')
plt.close()



# Group by the hospital id, see weekly data
hos_grp = df.groupby('hhs_ids')

TARGET = ''
for grp, ind in hos_grp.groups.items():
    # grp, ind = next(iter(hos_grp.groups.items()))
    sdf = df.loc[ind, ['collection_week', TARGET, personnel_cols]]
    sdf.sort_values('collection_week', inplace=True)
