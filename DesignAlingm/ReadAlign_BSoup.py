#
#
#
import pandas as pd
from lxml import etree
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import json


#df = pd.read_xml('Design Alignment Track_2021-11-05_Final.xml')
FILE = 'Design Alignment Track_2021-11-05_Final.xml'
#root = ET.parse( FILE ).getroot() 
with open( FILE, 'r') as f:
    contens = f.read()
    soup = BeautifulSoup( contens,'xml')

NODE_UNIT =  soup.contents[0].contents[1]
NODE_CRS  =  soup.contents[0].contents[3]
NODE_ALMN =  soup.contents[0].contents[9]

NODE_091 =  soup.contents[0].contents[9].contents[1]  # In-Bound Track
NODE_093 =  soup.contents[0].contents[9].contents[3] 
NODE_095 =  soup.contents[0].contents[9].contents[5]  # Out-Bound Track
if 0:
    for node in [ NODE_091,NODE_093, NODE_095]:
        print( node )
        print(132*'=')
        print(132*'=')
        print(132*'=')

###############################################
NODE_CoordGeom = NODE_093.contents[1]  #  <CoordGeom>
NODE_VerAlign = NODE_093.contents[3]  # <Profile name="Alignment_Final">

for node in ( NODE_CoordGeom, NODE_VerAlign ):
    for i in range( len( node.contents ) ):  
        print('=========================')
        data = node.contents[i]
        if data != '\n':
            print( data )
            import pdb; pdb.set_trace()


#----------------------- DATA I   NODE_091 -------------
# <Alignment desc="" length="250021.20408189198" name="Alignment_Down Track" staStart="0.">

#----------------------- DATA II  NODE_093 -------------
# <Alignment desc="" length="250420.00000001717" name="Alignment_Final" staStart="-400.000000000057">
# Profile name="Alignment_Final">
#<ProfAlign name="Profile_Final">
#<PVI>-400. 30.</PVI>
#<ParaCurve length="250.">240. 30.</ParaCurve>
#<ParaCurve length="250.">740. 34.999999999981</ParaCurve>
#<ParaCurve length="250.">1365. 30.</ParaCurve>
#<ParaCurve length="150.">1915. 30.</ParaCurve>
#...
#..
#<ParaCurve length="100.">2315. 33.</ParaCurve>

#----------------------- DATA III  NODE_095 -------------
# <Alignment desc="" length="250013.86779769332" name="Alignment_Up Track" staStart="0.">
#
