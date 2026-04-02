code = "RPC0001780"
print(code[:-7])
code = code[-7:]
code = int(code) + 1
code = str(code)
add = 7 - len(code)
for i in range(add):
    code = "0" + code
print(code)

import OSGridConverter
cvt_wgs84 = OSGridConverter.grid2latlong('SP950130')
print(cvt_wgs84.latitude)
print(cvt_wgs84.longitude)