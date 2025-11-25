from cmu_graphics import *
import math
import xml.etree.ElementTree as ET 

#used Python ElementTree XML API docs https://docs.python.org/3/library/xml.etree.elementtree.html
def parseGPX(file):
    tree = ET.parse(file)
    root = tree.getroot()

    points = []
    ns = {'gdx': 'http://www.topografix.com/GPX/1/1'}

    for trackpoint in root.findall('.//gdx:trkpt', ns):
        lat = float(trackpoint.get('lat'))
        lon = float(trackpoint.get('lon'))
        ele = float(trackpoint.find('gdx:ele', ns).text)
        time = (trackpoint.find('gdx:time', ns).text)

        ext = trackpoint.find("gdx:extensions", ns)
        speed = float(ext.find("gdx:speed", ns).text)
        course = float(ext.find("gdx:course", ns).text)
        hAcc = float(ext.find("gdx:hAcc", ns).text)
        vAcc = float(ext.find("gdx:vAcc", ns).text)
        # need to still extract hr

        newPt = Point(lat, lon, ele, time, speed, course, hAcc, vAcc, hr = None)
        points.append(newPt)
    
    newPath = Path(points)
    newPath.getStats()

    return newPath

class Path: 
    def __init__(self, points):
        self.points = points
        self.totalDist = 0
        self.netEle= 0
        self.duration = 0
        self.dateTime = ''

    def getStats(self):
        if len(self.points) < 2:
            return

        for i in range(1, len(self.points)):
            p1 = self.points[i-1]
            p2 = self.points[i]

            d = p1.distanceTo(p2)
            self.totalDist += d

            netEle += (p2.ele - p1.ele)

        startTime, endTime = self.points[0].time, self.points[-1].time
        self.duration = Path.get #finish this
    

class Point:
    #sometimes HR not recorded; current GPX does not include HR
    def __init__(self, lat, lon, ele, time, speed, course, hAcc, vAcc, hr = None):
        self.lat = lat
        self.lon = lon
        self.ele = ele
        self.time = time
        self.speed = speed
        self.course = course
        self.hAcc = hAcc
        self.vAcc = vAcc
        self.hr = hr

    def __repr__(self):
        return f'Point(lat: {self.lat}, lon: {self.lon}, ele: {self.ele}, hr: {self.hr}) at {self.timeStr}'
    
    def getTimeStr(self):
    # current format: 2025-11-02T17:05:54Z
        self.year = s[:4]
        self.month = s[5:7]
        self.day = s[8:10]
        # default time is est -- make timezone options available later
        utcHr = int(s[11:13]
        self.hour = (utcHr) - 5) % 24
        self.min = s[14:16]
        self.sec = s[17:-1]
        # FUTURE: implement hour, day, month rollover

        self.timeStr = f'{self.month}/{self.day}/{self.year} {self.hour}:{self.min}:{self.sec}'
    
cmu_graphics.run()

#implement haversine function
#implement get duration
#map latitude and longitude