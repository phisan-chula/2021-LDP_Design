#
# AlignExport.py : read LandXML alighment by 'xmltodict',convert to dataframe
#                   and export to GIS geopackage
#
import pandas as pd
import geopandas as gpd
import numpy as np
from pygeodesy.utm import Utm
from xmltodict import parse
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString
from shapely import ops
import fiona
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'

def Az(LS):
    assert(len(LS.coords)==2)
    az = np.arctan2( LS.coords[1][0]-LS.coords[0][0] , LS.coords[1][1]-LS.coords[0][1] )
    return divmod( az,2*np.pi)[1]
####################################################################
class RouteAlignment:
    def __init__( self, XMLFILE, SAMPL_INT=2 ):
        with open( XMLFILE, 'r') as f:
            contents = parse( f.read() )  
        EPSG = contents['LandXML']['CoordinateSystem']['@epsgCode']  # '4326'/'32647'/'32648'
        self.EPSG = f'EPSG:{EPSG}'
        self.SAMPL_INT = SAMPL_INT
        align0 = contents['LandXML']['Alignments']['Alignment'][0] # "Alignment_Down Track"
        align1 = contents['LandXML']['Alignments']['Alignment'][1] # "Alignment_Final"
        align2 = contents['LandXML']['Alignments']['Alignment'][2] # "Alignment_Down Track"
        for i, ali in enumerate( contents['LandXML']['Alignments']['Alignment'] ):
            print( f'Alignemnt#{i} @name : {ali["@name"]} ') 
        ##############################################
        self.HORALI = align1['CoordGeom']
        self.PROFIL = align1['Profile']['ProfAlign']
        ##############################################
        self.dictTYPE = dict()
        for ali_type in ('Line','Curve','Spiral'):  # OrderedDict breaks semantics here!!!
            self.dictTYPE[ali_type] = pd.DataFrame( self.HORALI[ali_type] ) 
            print( self.dictTYPE[ali_type] )
        dfRoutPnt, dfRoutLS = self.RestrucRoute()
        gdfRoutPnt, gdfRoutLS,_ = self.CalcLinRefRoute( dfRoutPnt, dfRoutLS) # weld LS and LR
        ##############################################
        dfSamplPnt,dfSampLS = self.ResamplRoute(dfRoutPnt, self.dictTYPE['Curve']) # curve!!
        self.gdfSamplPnt,self.gdfSampLS, RouteLS = self.CalcLinRefRoute( dfSamplPnt,dfSampLS  ) # weld LS and LR
        dfCL = pd.DataFrame( [['CenterLine',RouteLS]], columns=['Name','geometry'] )
        self.gdfCL = gpd.GeoDataFrame( dfCL,crs=self.EPSG, geometry=dfCL.geometry ) 
        self.CalcProfile()

    ####################################################################
    def CalcProfile(self ):
        dfProfil =pd.DataFrame( self.PROFIL['ParaCurve'] )
        def MakeProfil( row ):
            dist_m,msl =  np.fromstring( row['#text'], sep=" " )
            return pd.Series( [dist_m,msl] )
        dfProfil[['Dist_m','MSL']] = dfProfil.apply( MakeProfil, axis='columns' )
        assert( self.gdfCL.iloc[0].geometry.geom_type=='LineString' and len(self.gdfCL)==1 )
        def CalcDistProfil( row ):
            pnt = self.gdfCL.iloc[0].geometry.interpolate( row.Dist_m, normalized=False )
            return pd.Series([ pnt.x, pnt.y ])
        dfProfil[['x','y']] = dfProfil.apply( CalcDistProfil, axis='columns'  )
        self.gdfProfil = gpd.GeoDataFrame( dfProfil, crs='EPSG:32647', 
                      geometry=gpd.points_from_xy( dfProfil.x, dfProfil.y) )
        #import pdb; pdb.set_trace()

    ####################################################################
    def RestrucRoute(self):
        'Harmonize all "Line", "Curve", "Sprial" to single dataframe'
        rt_pnt = list(); rt_lin = list()
        CNT_LIN=0; CNT_CRV=0; CNT_SPI=0
        for ali_type in ('Line','Curve','Spiral'):
            for i,row in self.dictTYPE[ali_type].iterrows():
                stt = np.flip( np.fromstring( row.Start, sep=" "))
                end = np.flip( np.fromstring( row.End, sep=" "))
                len_flt = float(row['@length'])
                len_str = 'L={:.2f}m'.format( len_flt )
                if ali_type == 'Line':
                    ALI_CNT = f'{ali_type}#{CNT_LIN}' ; CNT_LIN += 1
                    mid    = (stt+end)/2 
                    radi   = '' 
                    radi_m = ''
                    rot    = ''
                elif ali_type == 'Curve':
                    ALI_CNT = f'{ali_type}#{CNT_CRV}' ; CNT_CRV += 1
                    mid    = np.flip( np.fromstring( row.PI, sep=" ") ) 
                    radi_m = float(row['@radius'])
                    radi   = 'R={:.0f}m.'.format( radi_m )
                    rot    = row['@rot']
                    #import pdb; pdb.set_trace()
                elif ali_type == 'Spiral':
                    ALI_CNT  = f'{ali_type}#{CNT_SPI}' ; CNT_SPI += 1
                    mid      = np.flip( np.fromstring( row.PI, sep=" ") ) 
                    rot      = row['@rot']
                    if row['@radiusStart']=='INF': 
                        radi_m = float(row['@radiusEnd'])
                        radi   = 'Re={:.0f}m.'.format( radi_m )
                    elif row['@radiusEnd']=='INF': 
                        radi_m = float(row['@radiusStart'])
                        radi   = 'Rs={:.0f}m.'.format( radi_m )
                    else:
                        raise f'*** ERROR ***{i}#{row}' 
                else:
                    raise "***ERROR *** curve not type 'Line','Curve','Spiral' "
                #if ali_type=='Curve': import pdb; pdb.set_trace()
                rt_pnt.append( [ ALI_CNT, ali_type, 'PC', Point(stt) ] )
                #rt_pnt.append( [ f'{ALI_CNT}:{rot}\n{len_str}\n{radi}\n', ali_type, 
                rt_pnt.append( [ ALI_CNT, ali_type, 'PI', Point(mid) ] )
                rt_pnt.append( [ ALI_CNT, ali_type, 'PT', Point(end) ] )
                rt_lin.append( [ ALI_CNT, ali_type, radi, radi_m, rot, 
                                 len_flt, LineString( [stt,mid,end] ) ] )
        dfRoutPnt = pd.DataFrame( rt_pnt, columns=['Name','AliType', 'PntType', 'geometry'])
        dfRoutLS  = pd.DataFrame( rt_lin, columns=[ 'Name','AliType', 'Radi', 'Radi_m', 
                                                   'RotDir', 'Length',  'geometry'])
        return dfRoutPnt, dfRoutLS

    ######################################################################
    def CalcLinRefRoute(self, dfRoutPnt, dfRoutLS): 
        LS_route = ops.linemerge( MultiLineString(  list(dfRoutLS.geometry) ) )
        snapped_ls = list()
        for i in range( len(LS_route.geoms)-1 ):    # welding contiguos points ...
            snapped_ls.append( ops.snap( LS_route.geoms[i], LS_route.geoms[i+1], 0.001 ) )
        snapped_ls.append( LS_route.geoms[-1] )
        RoutLS = ops.linemerge( MultiLineString(  list(snapped_ls) ) )
        assert( RoutLS.geom_type=='LineString')  # if linemerge successed--> LineString
        print( 'Route lenght (by vertex) : {:,.3f} meters'.format(RoutLS.length) )
        def CalcDist( at_geom):
            return  RoutLS.project( at_geom, normalized=False )
        dfRoutPnt['Dist'] = dfRoutPnt['geometry'].apply( CalcDist )
        dfRoutPnt.sort_values( by='Dist', inplace=True, ignore_index=True )
        gdfRoutPnt = gpd.GeoDataFrame( dfRoutPnt, crs=self.EPSG, 
                                     geometry=list(dfRoutPnt.geometry) )
        gdfRoutLS = gpd.GeoDataFrame( dfRoutLS, crs=self.EPSG,
                                     geometry=list(dfRoutLS.geometry) )
        #import pdb; pdb.set_trace()
        return gdfRoutPnt, gdfRoutLS, RoutLS

    def ResamplCurve(self, CurveData, INT=150 ):
        '''resampling each "simple circular" curve, designated radius is assumed
           to be TRUE distance and reduced to UTM dist by scale factor'''
        S = float(CurveData['@length'])
        R = float(CurveData['@radius'])
        CEN =  np.flip( np.fromstring( CurveData['Center'], sep=' ') )
        STT =  np.flip( np.fromstring( CurveData['Start'], sep=' ' ) )
        END =  np.flip( np.fromstring( CurveData['End'], sep=' ' ) )
        CTROID =  MultiPoint( [CEN,STT,END] ).centroid
        u = Utm( 47, 'N', CTROID.x, CTROID.y )   
        Rgd=u.toLatLon().scale*R                  # scaled R by PSF
        #import pdb; pdb.set_trace()
        nseg, head_tail = divmod( S , INT )
        pnts = np.linspace( head_tail/2., S-(head_tail/2), num=int(nseg),endpoint=True)
        if head_tail > 0.0:
            pnts = np.hstack( ( [0.0], pnts, [S] ) ) 
        RP_PC = LineString( [ CEN, STT] ) 
        SIGN = -1 if CurveData['@rot']=='ccw' else +1
        AZs = Az(RP_PC) + SIGN*pnts/R
        pnt_E = CEN[0]+ Rgd*np.sin(AZs)
        pnt_N = CEN[1]+ Rgd*np.cos(AZs)
        df = pd.DataFrame( zip( pnt_E,pnt_N ) , columns=['E','N'] )
        gdf = gpd.GeoDataFrame( df , crs=self.EPSG, 
                                geometry=gpd.points_from_xy( df.E, df.N ) )
        gdf.drop( ['E','N' ], axis='columns', inplace=True )
        return gdf

    def ResamplRoute( self, dfROUTE, dfCURVE):
        '''resample Route by dividing curve point '''
        dfSamplPnt = dfROUTE.copy()
        for ic in range( len(dfCURVE) ):
            df_curv = self.ResamplCurve( dfCURVE.iloc[ic] ,self.SAMPL_INT )
            df_curv[['Name','AliType','PntType','Dist']] =\
                        [ f'Curve#{ic}', 'Curve', 'SAMPL', np.NaN ]
            pi = dfSamplPnt[ (dfSamplPnt['Name']==f'Curve#{ic}') &\
                             (dfSamplPnt['PntType']=='PI' ) ]
            assert( len(pi)==1 )
            PRECEED = dfSamplPnt.loc[0 :pi.index[0]]
            SUCCEED = dfSamplPnt.loc[pi.index[0]+1:]
            dfSamplPnt = pd.concat( [PRECEED,df_curv,SUCCEED], 
                                        ignore_index=True, sort=False ) 
        PPP = dfSamplPnt[(dfSamplPnt['AliType']=='Curve')&(dfSamplPnt['PntType'].\
                                            isin(['PC','PI','PT']) )]
        dfSamplPnt.drop( PPP.index, inplace=True)
        dfSamplPnt['Dist'] = np.NaN
        ls = list()
        for i in range( len(dfSamplPnt)-1 ):
            P0 =  dfSamplPnt.iloc[i].geometry 
            P1 =  dfSamplPnt.iloc[i+1].geometry
            if P0.distance( P1 ) > 0.0001:
                ls.append( ['SAMPL',LineString( [P0,P1] ) ]  )
        dfSamplLin = pd.DataFrame( ls , columns=['AliType','geometry']) 
        return dfSamplPnt, dfSamplLin

###############################################################################
###############################################################################
###############################################################################
FILE_ALIGN = './Data/Design Alignment Track_2021-11-05_Final.xml'
FILE_SAMPL = './Data/DraftFinalAlignment_2021-07-19.kml'

route = RouteAlignment( FILE_ALIGN, SAMPL_INT=10 )
#pd.set_option('display.max_rows', None )
#print( dfRoutPnt )

##############################################
OUT_GIS = 'df_Route_Align.gpkg' 
#import pdb; pdb.set_trace()
if 1:
    route.gdfCL.to_file( OUT_GIS, driver="GPKG", layer='CenterLine')
    route.gdfSampLS.to_file( OUT_GIS, driver="GPKG", layer='SamplingLS')
    route.gdfSamplPnt.to_file( OUT_GIS, driver="GPKG", layer='SamplingPnt')
    route.gdfProfil.to_file( OUT_GIS, driver="GPKG", layer='Profile')
##############################################
