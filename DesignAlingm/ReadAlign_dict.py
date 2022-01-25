#
# ReadAlign_dict.py : read LandXML alighment by 'xmltodict' and transform to
#                     dataframe.
#
import pandas as pd
from xmltodict import parse


FILE = 'Design Alignment Track_2021-11-05_Final.xml'
with open( FILE, 'r') as f:
    contents = parse( f.read() )  

align0 = contents['LandXML']['Alignments']['Alignment'][0] # "Alignment_Down Track"
align1 = contents['LandXML']['Alignments']['Alignment'][1] # "Alignment_Final"
align2 = contents['LandXML']['Alignments']['Alignment'][2] # "Alignment_Down Track"

##############################################
HorAli = align1['CoordGeom']
print( HorAli.keys() )
Profi = align1['Profile']['ProfAlign']
print( Profi.keys() )

##############################################
df_ali = dict()
for ali_type in ('Line','Curve','Spiral'):
    df_ali[ali_type] = pd.DataFrame( HorAli[ali_type] )
    print( f'Alightment type "{ali_type}" , count = {len(df_ali[ali_type])} .' )
    print( df_ali[ali_type] )
#-----------------------------------------
dfProfil =pd.DataFrame( Profi['ParaCurve'] )
print( dfProfil )
#import pdb; pdb.set_trace()
