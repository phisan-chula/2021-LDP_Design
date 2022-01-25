#
#
#
import pandas as pd
import geopandas as gpd

df_ldp = gpd.read_file("LDP_2/RESULTS/ldp_sampling.gpkg", layer='sampl')
df_pfl = gpd.read_file("DesignAlingm/df_Route_Align.gpkg", layer='Profile')

df_pfl_ = df_pfl.to_crs('EPSG:4326').copy()
df_ldp = df_ldp.sjoin_nearest( df_pfl_, how='inner' , 
                            max_distance=None, distance_col='NN_deg' )
diff = df_ldp['MSL_left']-df_ldp['MSL_right']
print( diff.describe() )
import pdb ; pdb.set_trace()
