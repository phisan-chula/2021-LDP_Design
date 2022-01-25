#
# AlignExport.py : read LandXML alighment by 'xmltodict' , convert to dataframe
#                   and export to GIS geopackage
#
import pandas as pd
import geopandas as gpd
import numpy as np
from xmltodict import parse
from shapely.geometry import Point, LineString, Polygon
from shapely import ops
import fiona
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'

####################################################################
def ReadLandXML( XMLFILE ):
    with open( XMLFILE, 'r') as f:
        contents = parse( f.read() )  
    align0 = contents['LandXML']['Alignments']['Alignment'][0] # "Alignment_Down Track"
    align1 = contents['LandXML']['Alignments']['Alignment'][1] # "Alignment_Final"
    align2 = contents['LandXML']['Alignments']['Alignment'][2] # "Alignment_Down Track"
    for i, ali in enumerate( contents['LandXML']['Alignments']['Alignment'] ):
        #import pdb; pdb.set_trace()
        print( f'Alignemnt#{i} @name : {ali["@name"]} ') 
    ##############################################
    HorAli = align1['CoordGeom']
    print( HorAli.keys() )
    Profi = align1['Profile']['ProfAlign']
    print( Profi.keys() )
    ##############################################
    df_ali = dict()
    for ali_type in ('Line','Curve','Spiral'):  # OrderedDict breaks semantics here!!!
        df_ali[ali_type] = pd.DataFrame( HorAli[ali_type] ) 
        print( f'Alightment type "{ali_type}" , count = {len(df_ali[ali_type])} .' )
        print( df_ali[ali_type] )

    dfProfil =pd.DataFrame( Profi['ParaCurve'] )
    def MakeProfil( row ):
        dist_m,msl =  np.fromstring( row['#text'], sep=" " )
        return pd.Series( [dist_m,msl] )
    dfProfil[['Dist_m','MSL']] = dfProfil.apply( MakeProfil, axis='columns' )
    #print( dfProfil )
    return df_ali, dfProfil

####################################################################
def RestrucRoute( df_ali ):
    rt_pnt = list(); rt_lin = list()
    for ali_type in ('Line','Curve','Spiral'):
        for i,row in df_ali[ali_type].iterrows():
            stt = np.flip( np.fromstring( row.Start, sep=" "))
            end = np.flip( np.fromstring( row.End, sep=" "))
            len_flt = float(row['@length'])
            len_str = 'L={:.2f}m'.format( len_flt )
            if ali_type == 'Line':
                mid = (stt+end)/2 
                radi = '' 
                radi_m = ''
                rot = ''
            elif ali_type == 'Curve':
                mid = np.flip( np.fromstring( row.PI, sep=" ") ) 
                radi_m = float(row['@radius'])
                radi = 'R={:.0f}m.'.format( radi_m )
                rot = row['@rot']
            elif ali_type == 'Spiral':
                mid = np.flip( np.fromstring( row.PI, sep=" ") ) 
                rot = row['@rot']
                if row['@radiusStart']=='INF': 
                    radi_m = float(row['@radiusEnd'])
                    radi = 'Re={:.0f}m.'.format( radi_m )
                elif row['@radiusEnd']=='INF': 
                    radi_m = float(row['@radiusStart'])
                    radi = 'Rs={:.0f}m.'.format( radi_m )
                else:
                    raise f'*** ERROR ***{i}#{row}' 
            else:
                raise "***ERROR *** curve not type 'Line','Curve','Spiral' "
            #if ali_type=='Curve': import pdb; pdb.set_trace()
            rt_pnt.append( [ f'{ali_type}#{i}', f'{ali_type}', 
                                'PC', Point(stt) ] )
            rt_pnt.append( [ f'{ali_type}#{i}:\n{len_str}\n{radi}', f'{ali_type}', 
                                'PI', Point(mid) ] )
            rt_pnt.append( [ f'{ali_type}#{i}', f'{ali_type}', 
                                'PT', Point(end) ] )
            rt_lin.append( [ f'{ali_type}#{i}', f'{ali_type}', radi, radi_m, rot, 
                             len_flt, LineString( [stt,mid,end] ) ] )
    dfRoutPnt = pd.DataFrame( rt_pnt, columns=['Name','AliType', 'PntType', 'geometry'])
    dfRoutLS = pd.DataFrame( rt_lin, columns=[ 'Name','AliType', 'Radi', 'Radi_m', 
                                               'RotDir', 'Length',  'geometry'])
    LS_route = ops.linemerge( list(dfRoutLS.geometry) )
    print( 'Route lenght (by vertex) : {:,.3f} meters'.format(LS_route.length) )
    def CalcDist( at_geom):
        return  LS_route.project( at_geom, normalized=False )
    dfRoutPnt['Dist'] = dfRoutPnt['geometry'].apply( CalcDist )
    dfRoutPnt.sort_values( by='Dist', inplace=True, ignore_index=True )
    dfRoutPnt = gpd.GeoDataFrame( dfRoutPnt, crs='EPSG:32647', 
                                 geometry=list(dfRoutPnt.geometry) )
    dfRoutLS = gpd.GeoDataFrame( dfRoutLS, crs='EPSG:32647', 
                                 geometry=list(dfRoutLS.geometry) )
    return dfRoutPnt, dfRoutLS

###############################################################################
###############################################################################
###############################################################################
FILE_ALIGN = './Data/Design Alignment Track_2021-11-05_Final.xml'
FILE_SAMPL = './Data/DraftFinalAlignment_2021-07-19.kml'
df_ali, dfProfil = ReadLandXML( FILE_ALIGN )
dfRoutPnt, dfRoutLS = RestrucRoute( df_ali )

##############################################
dfCL = gpd.read_file(FILE_SAMPL, driver='KML' )
dfCL = dfCL.to_crs('EPSG:32647')
CL_LS = dfCL.iloc[0].geometry 
def CalcDistProfil( row ):
    pnt = CL_LS.interpolate( row.Dist_m, normalized=False )
    return pd.Series([ pnt.x, pnt.y ])
dfProfil[['x','y']] = dfProfil.apply( CalcDistProfil, axis='columns'  )
dfProfil = gpd.GeoDataFrame( dfProfil, crs='EPSG:32647', 
                             geometry=gpd.points_from_xy( dfProfil.x, dfProfil.y) )
##############################################
OUT_GIS = 'df_Route_Align.gpkg' 
isPI = dfRoutPnt.PntType=='PI'
if 1:
    dfRoutPnt[ isPI].to_file( OUT_GIS,driver="GPKG", layer='CurveDataPI')
    dfRoutPnt[~isPI].to_file( OUT_GIS, driver="GPKG", layer='CurvePoint')
    dfRoutLS.to_file( OUT_GIS, driver="GPKG", layer='Line_Curve')
    dfProfil.to_file( OUT_GIS, driver="GPKG", layer='Profile')
    dfCL.to_file( OUT_GIS, driver="GPKG", layer='CenterLine')
#import pdb; pdb.set_trace()
##############################################
if 0:
    for i in (0,-1):
        dist_m,msl = np.fromstring( Profi['PVI'][i], sep=" ")
        import pdb; pdb.set_trace()
        dfProfil = dfProfil.append( ( Profi['PVI'][i], '', dist_m, msl  ) )
