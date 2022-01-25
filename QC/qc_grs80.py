#
#
#
import pandas as pd
import geopandas as gpd

df = gpd.read_file( 'ldp_sampling_GRS80.gpkg' )

for ldp in ( f'TMC', 'LCC', 'OMC' ):
    df[f'{ldp}_dE'] = df[f'{ldp}_E']-df[f'{ldp}8_E']
    df[f'{ldp}_dN'] = df[f'{ldp}_N']-df[f'{ldp}8_N']
    print( df[ [f'{ldp}_dE',f'{ldp}_dN'] ].describe() )


import pdb; pdb.set_trace()

