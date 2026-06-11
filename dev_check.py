from backend.stations import flatten_stations
from backend.risk_engine import calculate_sensor_risk
from backend.database import MONITORED_SITE

stations = flatten_stations()
print('stations count', len(stations))
ids = [s['id'] for s in stations]
from collections import Counter
counts = Counter(ids)
dups = [k for k,v in counts.items() if v>1]
print('duplicate ids count', len(dups))
print('sample ids', ids[:10])
john_ware = [s for s in stations if s['name'].lower() == 'john ware substation']
print('john ware entries', john_ware)
print('MONITORED_SITE matches john_ware id:', MONITORED_SITE == john_ware[0]['id'] if john_ware else 'N/A')

r = calculate_sensor_risk('motion_detected','high', temp_c=36, light_level=50, door_open=False, flame_detected=False, maintenance_mode=False, recent_events=['door_open','motion_detected'])
print('risk output sample:', r)

