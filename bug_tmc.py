#
#
import pyproj
TMC = '+proj=tmerc +lat_0=19.55 +lon_0=99.0666666666667 +k=1.0000847 +x_0=20000 +y_0=60000 +ellps=GRS80 +units=m +no_defs'


tmc = pyproj.CRS( TMC )
print( tmc.to_proj4() )
print( tmc.to_string() )
import pdb;pdb.set_trace()
