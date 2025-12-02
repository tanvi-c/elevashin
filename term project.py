from cmu_graphics import *
import math
import xml.etree.ElementTree as ET 

def onAppStart(app):
    app.isHRSelected = False
    app.isSpeedSelected = True
    app.path = parseGPX('test.gpx')
    app.plotPoints = app.path.getPlotPoints(app.width, app.height, 20)

def redrawAll(app):
    for i in range(len(app.plotPoints) - 1):
        x1, y1 = app.plotPoints[i]
        x2, y2 = app.plotPoints[i + 1]
        color = app.path.getColor(app, app.path.points[i])
        drawLine(x1, y1, x2, y2, fill = color)

#used Python ElementTree XML API docs https://docs.python.org/3/library/xml.etree.elementtree.html
def parseGPX(file):
    tree = ET.parse(file)
    root = tree.getroot()

    points = []
    ns = {'gpx': root.tag.split('}')[0].strip('{')}

    for trackpoint in root.findall('.//gpx:trkpt', ns):
        lat = float(trackpoint.get('lat'))
        lon = float(trackpoint.get('lon'))
        ele = float(trackpoint.find('gpx:ele', ns).text)
        time = (trackpoint.find('gpx:time', ns).text)

        ext = trackpoint.find("gpx:extensions", ns)
        speed = float(ext.find("gpx:speed", ns).text)
        course = float(ext.find("gpx:course", ns).text)
        hAcc = float(ext.find("gpx:hAcc", ns).text)
        vAcc = float(ext.find("gpx:vAcc", ns).text)
        # FUTURE: extract hr

        newPt = Point(lat, lon, ele, time, speed, course, hAcc, vAcc, hr = None)
        points.append(newPt)
    
    newPath = Path(points)
    newPath.getStats()

    return newPath

# haversine is analogous to the distance function but for latitude and longitude (Source: medium.com)
# assumes Earth is a perfect sphere - minor errors OK in this app (relatively small distances) 
def haversine(lat1, lon1, lat2, lon2):
    r = 6371000 #Earth's radius in meters
    phi1, phi2 = lat1 * (math.pi/180), lat2 * (math.pi/180)
    lam1, lam2 = lon1 * (math.pi/180), lon2 * (math.pi/180)
    a = math.sin((phi2 - phi1)/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin((lam2 - lam1)/2)**2
    c = 2 * math.atan2(a**0.5, (1-a)**0.5)
    d = r * c
    return d

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
            self.netEle += (p2.ele - p1.ele)

        start, end = self.points[0], self.points[-1]
        self.duration = Path.getDuration(start, end)

    def getPlotPoints(self, width, height, margin):
        lats, lons = [], []

        for point in self.points:
            lats.append(point.lat)
            lons.append(point.lon)
        
        # +1 to avoid any 0 ranges
        latRange = max(lats) - min(lats) + 1
        lonRange = max(lons) - min(lons) + 1

        xScale = (width - margin * 2) / latRange
        yScale = (height - margin * 2) / lonRange
        scale = min(xScale, yScale) # to avoid stretch/compression

        plotPoints = []

        for i in range(len(self.points)):
            x = margin + (lons[i] - min(lons)) * scale
            y = height - (margin + (lats[i] - min(lats)) * scale)
            plotPoints.append((x, y))

        return plotPoints
    
    def getColor(self, app, point):
        # if app.isHRSelected == True:
        if app.isSpeedSelected == True:
            if point.speed < 1.5:
                return 'blue'
            elif point.speed < 3:
                return 'cyan'
            elif point.speed < 5.5:
                return 'lightGreen'
            elif point.speed < 7:
                return 'orange'
            else:
                return 'red'

    @staticmethod
    def getDuration(start, end):
        startDays = (start.year * 365) + ((start.month - 1)*30) + (start.day)
        startSec = startDays * 24 * 3600
        endDays = (end.year * 365) + ((end.month - 1)*30) + (end.day)
        endSec = (endDays * 24 * 3600) - startSec
        resHr = endSec // 3600
        resMin = (endSec - resHr * 3600) // 60
        resSec = rounded(endSec - resHr * 3600 - resMin * 60)
        return f'{resHr}:{resMin}:{resSec}'

class Point:
    #sometimes HR not recorded; current GPX does not include HR -- need to get new data set for testing
    def __init__(self, lat, lon, ele, time, speed, course, hAcc, vAcc, hr = None):
        self.lat = lat
        self.lon = lon
        self.ele = ele
        self.time = str(time)
        self.month, self.day, self.year, self.hour, self.min, self.sec = Point.getTimeStr(self.time)
        self.timeStr = f'{self.month}/{self.day}/{self.year} {self.hour}:{self.min}:{self.sec}'
        self.speed = speed
        self.course = course
        self.hAcc = hAcc
        self.vAcc = vAcc
        self.hr = hr

    def __repr__(self):
        return f'Point(lat: {self.lat}, lon: {self.lon}, ele: {self.ele}, hr: {self.hr}) at {self.timeStr}'
    
    @staticmethod
    def getTimeStr(s):
    # current format: 2025-11-02T17:05:54Z
        year = int(s[:4])
        month = int(s[5:7])
        day = int(s[8:10])
        # default time is est -- FUTURE: make timezone options available
        utcHr = int(s[11:13])
        hour = int((utcHr) - 5 % 24)
        min = int(s[14:16])
        sec = int(s[17:-1])
        # FUTURE: implement hour, day, month rollover

        return month, day, year, hour, min, sec

    # 3D distance logic: taking the arc length of the curve is summing all the hypotenuses (dx, dy) of infinitesimally small right triangles 
    # haversine gives the horizontal distance and elevation gives vertical distance
    def distanceTo(self, other):
        if isinstance(other, Point):
            horiz = haversine(self.lat, self.lon, other.lat, other.lon)
            vert = abs(other.ele - self.ele)
            return (horiz**2 + vert**2)**0.5

# need user to input age