#
#
#
import os,sys,gc
from pyproj import Proj, CRS, Transformer, Geod
import pandas as pd
import geopandas as gpd
import numpy as np
import yaml
import pathlib
import matplotlib.pyplot as plt
import pyproj
import argparse
import subprocess as sp

def DescDiff( CMD, PJT ):
    results = list()
    for i,row in df.iterrows():
        lng = row.geometry.x
        lat = row.geometry.y
        cmd = CMD.format( lat,lng )
        #import pdb; pdb.set_trace()
        res = sp.run( cmd, shell=True, check=True, capture_output=True )
        cols = res.stdout.decode("utf-8").split()
        cols = list(  map(float,cols) )
        #print(cmd)
        results.append( cols )
        #if i==2: break
    df[[f'{PJT}_E_',f'{PJT}_N_', f'{PJT}_cv_',f'{PJT}_sf_']] = results
    df[f'{PJT}_E_'] = df[f'{PJT}_E']- df[f'{PJT}_E_']
    df[f'{PJT}_N_'] = df[f'{PJT}_N']- df[f'{PJT}_N_']
    df[f'{PJT}_sf_'] = df[f'{PJT}_sf']- df[f'{PJT}_sf_']
    print( df[ [f'{PJT}_E_',f'{PJT}_N_', f'{PJT}_sf_']].describe() )

###############################################################
SAMPFILE = 'RESULTS/ldp_sampling.gpkg'
YAMLFILE = 'DOH_107_CDOW.yaml'

df = gpd.read_file( SAMPFILE )
with open( YAMLFILE ) as f:
        YAML = yaml.load( f, Loader=yaml.FullLoader )

##########################################################
TMCx = CRS.from_proj4( YAML['LDP']['TMCx'] ).to_dict()
lon0 = TMCx['lon_0']
k0   = TMCx['k']
cmd = f''' TransverseMercatorProj -l {lon0} -k {k0}'''\
      f''' --input-string "{{}} {{}}" '''
DescDiff( cmd, 'TMCx' )

##########################################################
LCCx = CRS.from_proj4( YAML['LDP']['LCCx'] ).to_dict()
lon0 = LCCx['lon_0']
k0   = LCCx['k_0']
lat0 = LCCx['lat_0']
lat1 = LCCx['lat_1']
cmd = f''' ConicProj -c {lat0} {lat1} -l {lon0} -k {k0}  '''\
      f''' --input-string "{{}} {{}}" '''
DescDiff( cmd, 'LCCx' )
#import pdb; pdb.set_trace()
