"""Small bounded WGS84 corridor operations, no road-km coordinate fabrication."""
import math


def finite(n):
    return isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)


def point(p):
    return isinstance(p, (list, tuple)) and len(p)>=2 and all(finite(n) for n in p[:2]) and -54<=p[0]<=-43 and -26<=p[1]<=-19


def vertices(g):
    if not isinstance(g, dict): return []
    c=g.get('coordinates', [])
    if g.get('type')=='Point': return [c] if point(c) else []
    if g.get('type')=='LineString': return c if len(c)>=2 and all(point(p) for p in c) else []
    if g.get('type')=='Polygon': return c[0] if c and len(c[0])>=4 and all(point(p) for ring in c for p in ring) else []
    return []


def bounds(g):
    ps=vertices(g)
    if not ps:return None
    return min(p[0] for p in ps), min(p[1] for p in ps), max(p[0] for p in ps), max(p[1] for p in ps)


def distance(a,b):
    return math.hypot((a[0]-b[0])*111320*math.cos(math.radians((a[1]+b[1])/2)), (a[1]-b[1])*110540)


def project(p,a,b):
    scale=111320*math.cos(math.radians(p[1])); ax=(a[0]-p[0])*scale;ay=(a[1]-p[1])*110540
    bx=(b[0]-p[0])*scale;by=(b[1]-p[1])*110540;dx=bx-ax;dy=by-ay
    t=max(0,min(1,-(ax*dx+ay*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return math.hypot(ax+t*dx,ay+t*dy), t


def bearing(a,b):
    return math.degrees(math.atan2((b[0]-a[0])*math.cos(math.radians(a[1])),b[1]-a[1]))%360


def inside(p,ring):
    yes=False
    for a,b in zip(ring,ring[1:]+ring[:1]):
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:yes=not yes
    return yes


def region_contains(p,g):
    return inside(p,g['coordinates'][0]) and not any(inside(p,hole) for hole in g['coordinates'][1:])


def crossing(a,b,x,y):
    dx,dy=b[0]-a[0],b[1]-a[1];ex,ey=y[0]-x[0],y[1]-x[1];det=dx*ey-dy*ex
    if abs(det)<1e-15:return None
    t=((x[0]-a[0])*ey-(x[1]-a[1])*ex)/det;u=((x[0]-a[0])*dy-(x[1]-a[1])*dx)/det
    return [a[0]+t*dx,a[1]+t*dy] if 0<=t<=1 and 0<=u<=1 else None


def corridor(items, coords, along=0, mode='CITY_MODE', speed=0):
    if not isinstance(coords,list) or not 2<=len(coords)<=5000 or not all(point(p) for p in coords):raise ValueError('Invalid route geometry (2..5000 SP points)')
    if not finite(along) or along<0 or not finite(speed) or not 0<=speed<=90:raise ValueError('Invalid route progress/speed')
    before,ahead=(3000,50000) if mode=='ROAD_MODE' else (1000,10000)
    ahead=min(ahead,max(2000,speed*1200)) if speed else ahead
    segments=[];total=0
    for a,b in zip(coords,coords[1:]):
        length=distance(a,b);segments.append((a,b,total,length));total+=length
    out=[]
    for item in items:
        g=item.get('geometry');ps=vertices(g);best=None
        for a,b,start,length in segments:
            if start+length<along-before or start>along+ahead:continue
            candidates=ps[:]
            if g and g['type']=='Polygon':
                candidates=[]
                if region_contains(a,g):candidates.append(a)
                for x,y in zip(ps,ps[1:]):
                    p=crossing(a,b,x,y)
                    if p:candidates.append(p)
            if g and g['type']=='LineString':
                # A route vertex near a long source segment must not be missed.
                for x,y in zip(ps,ps[1:]):
                    dd,tt=project(a,x,y)
                    if dd<=120:candidates.append([x[0]+tt*(y[0]-x[0]),x[1]+tt*(y[1]-x[1])])
            for p in candidates:
                if p[0]<min(a[0],b[0])-.002 or p[0]>max(a[0],b[0])+.002 or p[1]<min(a[1],b[1])-.002 or p[1]>max(a[1],b[1])+.002:continue
                d,t=project(p,a,b);at=start+t*length
                if not along-before<=at<=along+ahead:continue
                tolerance=120 if item['record_class']=='weather' else 35 if item['record_class']=='infrastructure' else 20
                if d>tolerance:continue
                direction=str(item.get('direction') or '').upper();hd=bearing(a,b)
                expected={'NORTE':0,'NORTH':0,'SUL':180,'SOUTH':180,'LESTE':90,'EAST':90,'OESTE':270,'WEST':270}.get(direction)
                if expected is not None and abs((hd-expected+180)%360-180)>70:continue
                if g and g['type']=='LineString' and len(ps)>1 and expected is None and direction not in ('','AMBOS','BOTH'):
                    if abs((hd-bearing(ps[0],ps[-1])+180)%360-180)>70:continue
                if best is None or d<best[0]:best=(d,at,hd)
        if best:out.append(dict(item,along_m=round(best[1],1),distance_from_route_m=round(best[0],1),distance_ahead_m=round(best[1]-along,1),road_bearing=best[2]))
    return sorted(out,key=lambda r:r['along_m'])
