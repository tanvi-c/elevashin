from cmu_graphics import *
from datetime import datetime, timezone, timedelta
import math
import xml.etree.ElementTree as ET 

def onAppStart(app):
    app.isSpeedSelected = True
    app.path = parseGPX('test.gpx')
    app.plotPoints = app.path.getPlotPoints(app.width, app.height, 20)
    app.selectedDot = None
    app.setMaxShapeCount(10000)

def redrawAll(app):
    for i in range(len(app.plotPoints) - 1):
        x1, y1 = app.plotPoints[i]
        x2, y2 = app.plotPoints[i + 1]
        color = app.path.getColor(app, app.path.points[i])
        drawLine(x1, y1, x2, y2, fill = color)

    if app.selectedDot != None:
        currX, currY = app.plotPoints[app.selectedDot]
        curr = app.path.points[app.selectedDot]
        drawCircle(currX, currY, 4, fill = 'gray')
        drawRect(currX+10, currY-40, 95, 35, fill = 'lightgray')
        drawLabel(f'Speed: {pythonRound(curr.speed * 3.28084, 2)} ft/s', currX+15, currY-30, align = 'left')
        drawLabel(f'Elev: {pythonRound(curr.ele * 3.28084, 2)} ft', currX+15, currY-15, align = 'left')
    
    # Exercise Summary
    drawRect(app.width - 150, 20, 130, 90, fill='white', border='black', opacity = 75)
    drawLabel(f'SUMMARY', app.width - 85, 35, size = 18, font = 'montserrat',)
    drawLabel(f'Distance: {pythonRound(app.path.totalDist / 1609, 2)} miles', app.width - 140, 55, font = 'montserrat', align = 'left')
    drawLabel(f'Duration: {app.path.durationStr}', app.width - 140, 75, font = 'montserrat', align = 'left')
    drawLabel(f'Avg Speed: {pythonRound(app.path.avgSpeed * 3.28084, 2)} ft/s', app.width - 140, 95, font = 'montserrat', align = 'left')

    # Speed / HR button
    if app.isSpeedSelected:
        mode = 'Speed'
        color = 'gray'
        otherColor = 'white'
    else:
        mode = 'Heart Rate'
        color = 'lightgray'
        otherColor = 'black'
    drawRect(app.width - 150, 120, 130, 30, fill=color)
    drawLabel(f'{mode} Mode', app.width - 85, 135, fill = otherColor, size = 16, font = 'montserrat')

def onMouseMove(app, mouseX, mouseY):
    app.selectedDot = None
    for i in range(len(app.plotPoints)):
        x, y = app.plotPoints[i]
        if ((x - mouseX)**2 + (y - mouseY)**2)**0.5 < 8:
            app.selectedDot = i

def onMousePress(app, mouseX, mouseY):
    if app.width - 150 <= mouseX <= app.width - 20 and 120 <= mouseY <= 150:
        app.isSpeedSelected = not app.isSpeedSelected

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
        self.durationStr, self.durationSec = Path.getDuration(start, end)
        self.avgSpeed = self.totalDist / self.durationSec if self.durationSec > 0 else 0

    def getPlotPoints(self, width, height, margin):
        lats, lons = [], []

        for point in self.points:
            lats.append(point.lat)
            lons.append(point.lon)
        
        # +1 to avoid any 0 ranges
        latRange = max(lats) - min(lats) + 0.000000001
        lonRange = max(lons) - min(lons) + 0.000000001

        xScale = (width - margin * 2) / lonRange
        yScale = (height - margin * 2) / latRange
        scale = min(xScale, yScale) # to avoid stretch/compression

        plotPoints = []

        for i in range(len(self.points)):
            x = margin + (lons[i] - min(lons)) * scale
            y = height - (margin + (lats[i] - min(lats)) * scale)
            plotPoints.append((x, y))

        return plotPoints
    
    def getColor(self, app, point):
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
        else:
            # placeholder until HR data available
            return 'gray'

    @staticmethod
    def getDuration(start, end):
        duration = end.dateTime - start.dateTime
        secDiff = int(duration.total_seconds())
        hr = secDiff // 3600
        min = (secDiff % 3600) // 60
        sec = secDiff % 60
        return (f'{hr}:{min}:{sec}', secDiff)

class Point:
    # sometimes HR not recorded; current GPX does not include HR -- need to get new data set for testing
    def __init__(self, lat, lon, ele, time, speed, course, hAcc, vAcc, hr = None):
        self.lat = lat
        self.lon = lon
        self.ele = ele
        # datetime documentation: https://docs.python.org/3/library/datetime.html#datetime.datetime
        dateTime = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
        dateTime = dateTime.replace(tzinfo=timezone.utc)
        dateTime = dateTime.astimezone()
        self.dateTime = dateTime
        self.speed = speed
        self.course = course
        self.hAcc = hAcc
        self.vAcc = vAcc
        self.hr = hr

    # for debugging
    def __repr__(self):
        return f'Point(lat: {self.lat}, lon: {self.lon}, ele: {self.ele}, hr: {self.hr}) at {self.dateTime}'

    # 3D distance logic: taking the arc length of the curve is summing all the hypotenuses (dx, dy) of infinitesimally small right triangles 
    # haversine gives the horizontal distance and elevation gives vertical distance
    def distanceTo(self, other):
        if isinstance(other, Point):
            horiz = haversine(self.lat, self.lon, other.lat, other.lon)
            vert = abs(other.ele - self.ele)
            return (horiz**2 + vert**2)**0.5

# need user to input age

runApp(width=800, height=600)