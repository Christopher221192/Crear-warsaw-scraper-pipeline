import json
import logging
import time
from math import radians, cos, sin, asin, sqrt
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderQueryError, GeocoderServiceError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

METRO_M1 = {
    "Kabaty": (52.1311, 21.0658), "Natolin": (52.1384, 21.0553), "Imielin": (52.1491, 21.0456),
    "Stokłosy": (52.1583, 21.0336), "Ursynów": (52.1623, 21.0267), "Służew": (52.1725, 21.0232),
    "Wilanowska": (52.1805, 21.0223), "Wierzbno": (52.1906, 21.0175), "Racławicka": (52.1989, 21.0121),
    "Pole Mokotowskie": (52.2087, 21.0083), "Politechnika": (52.2185, 21.0145), "Centrum": (52.2307, 21.0109),
    "Świętokrzyska M1": (52.2349, 21.0084), "Ratusz Arsenał": (52.2443, 21.0016), "Dworzec Gdański": (52.2577, 20.9959),
    "Plac Wilsona": (52.2685, 20.9839), "Marymont": (52.2718, 20.9702), "Słodowiec": (52.2774, 20.9576),
    "Stare Bielany": (52.2842, 20.9427), "Wawrzyszew": (52.2891, 20.9388), "Młociny": (52.2929, 20.9292)
}

METRO_M2 = {
    "Bemowo": (52.2376, 20.9100), "Ulrychów": (52.2384, 20.9324), "Księcia Janusza": (52.2396, 20.9439),
    "Młynów": (52.2378, 20.9606), "Płocka": (52.2341, 20.9678), "Rondo Daszyńskiego": (52.2299, 20.9822),
    "Rondo ONZ": (52.2325, 20.9997), "Świętokrzyska M2": (52.2349, 21.0084), "Nowy Świat-Uniwersytet": (52.2369, 21.0189),
    "Centrum Nauki Kopernik": (52.2407, 21.0315), "Stadion Narodowy": (52.2471, 21.0425), "Dworzec Wileński": (52.2543, 21.0338),
    "Szwedzka": (52.2631, 21.0440), "Targówek Mieszkaniowy": (52.2683, 21.0504), "Trocka": (52.2758, 21.0583),
    "Zacisze": (52.2818, 21.0448), "Kondratowicza": (52.2905, 21.0456), "Bródno": (52.2942, 21.0332)
}

# Proxy from last Q4-2025/Q1-2026 average primary market
NBP_AVERAGE_DISTRICT = {
    "Sródmiescie": 24000, "Wola": 20500, "Mokotów": 19500,
    "Zoliborz": 21000, "Ochota": 19500, "Praga-Poludnie": 17500,
    "Praga-Pólnoc": 17000, "Bielany": 17500, "Wilanów": 18500,
    "Ursynów": 18000, "Bemowo": 17500, "Targówek": 15500,
    "Bialoleka": 14500, "Ursus": 15000, "Wlochy": 16000,
    "Wawer": 13500, "Wesola": 12500, "Rembertów": 13000
}

geolocator = Nominatim(user_agent="geospatial_analyst_2026_poland")

def get_coordinates(title, developer):
    """Fallback logic to find coordinates via title or developer if null"""
    queries = []
    if developer and developer != "N/A":
        # Truncate to avoid URI too long
        dev_clean = developer[:80]
        queries.append(f"{dev_clean}, Warszawa, Poland")
    if title and title != "N/A" and len(title) < 120:
        title_clean = title[:80]
        queries.append(f"{title_clean}, Warszawa, Poland")
        
    for q in queries:
        try:
            loc = geolocator.geocode(q, timeout=10)
            if loc:
                return loc.latitude, loc.longitude
        except (GeocoderTimedOut, GeocoderQueryError, GeocoderServiceError) as e:
            logging.warning(f"Geocoder error for '{q[:50]}...': {e}")
            continue
        except Exception as e:
            logging.warning(f"Unexpected geocoder error: {e}")
            continue
        time.sleep(1) # rate limit Nominatim
        
    # Default to center of Warsaw if totally null
    return 52.2297, 21.0122

def get_district(lat, lon):
    try:
        loc = geolocator.reverse(f"{lat}, {lon}", timeout=10)
        time.sleep(1)
        if loc and loc.raw.get("address"):
            addr = loc.raw["address"]
            return addr.get("suburb", addr.get("city_district", addr.get("town", "Warszawa")))
    except:
        pass
    return "Warszawa"

def find_nearest_metro(lat, lon):
    min_dist = float('inf')
    station_name = ""
    line = ""
    
    for name, coords in METRO_M1.items():
        dist = geodesic((lat, lon), coords).meters
        if dist < min_dist:
            min_dist = dist
            station_name = name
            line = "M1"
            
    for name, coords in METRO_M2.items():
        dist = geodesic((lat, lon), coords).meters
        if dist < min_dist:
            min_dist = dist
            station_name = name
            line = "M2"
            
    # Adjust for walking distance approximation (x 1.3 urban grid factor)
    walking_dist = int(min_dist * 1.3)
    # Average walking speed = 80 meters / min
    walking_mins = int(walking_dist / 80)
    
    return f"{line} {station_name}", walking_dist, walking_mins

def normalize_district(name):
    import unicodedata
    n = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    if "Srod" in n: return "Sródmiescie"
    if "Zol" in n: return "Zoliborz"
    if "Poludnie" in n: return "Praga-Poludnie"
    if "Polnoc" in n: return "Praga-Pólnoc"
    if "Bialoleka" in n: return "Bialoleka"
    if "Wlochy" in n: return "Wlochy"
    return n

def get_future_plans(district):
    district = normalize_district(district)
    tags = []
    # M3 path: Praga, Mokotów, Ochota
    if district in ["Praga-Poludnie", "Praga-Pólnoc", "Mokotów", "Ochota"]:
        tags.append("M3 Metro Line Planned (2028-2050)")
    # M4 path: Tarchomin/Bialoleka, Srodmiescie, Wilanow
    if district in ["Bialoleka", "Sródmiescie", "Wola", "Ochota", "Mokotów", "Wilanów"]:
        tags.append("M4 Metro Line Planned (2050)")
    if district in ["Wilanów", "Ochota"]:
        tags.append("Tram Expansion (Short Term)")
    
    return tags

def process():
    logging.info("Loading Warsaw apartments data...")
    with open("warsaw_apartments_2027.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    enriched_data = []
    
    for idx, item in enumerate(data):
        title = item.get("title", "")
        
        # Skip junk records (page-level scraping artifacts with huge text blobs)
        if len(title) > 200:
            logging.warning(f"Skipping item {idx+1} — title too long ({len(title)} chars), likely a page artifact.")
            continue
            
        logging.info(f"Processing item {idx+1}/{len(data)}: {title[:60]}")
        lat = item.get("latitude")
        lon = item.get("longitude")
        
        if lat is None or lon is None:
            lat, lon = get_coordinates(title, item.get("developer"))
            item["latitude"] = lat
            item["longitude"] = lon
            
        district = get_district(lat, lon)
        nearest_metro, dist_m, dist_mins = find_nearest_metro(lat, lon)
        
        norm_dist = normalize_district(district)
        nbp_avg = NBP_AVERAGE_DISTRICT.get(norm_dist, 18000) # Fallback Warsaw average
        
        price_m2 = item.get("price_per_m2")
        market_diff = "N/A"
        market_diff_pct = None
        if price_m2 and nbp_avg:
            market_diff_pct = ((price_m2 - nbp_avg) / nbp_avg) * 100
            market_diff = f"{market_diff_pct:+.2f}%"
            
        future_plans = get_future_plans(district)
        
        item["district"] = district
        item["nearest_metro"] = nearest_metro
        item["walking_distance_m"] = dist_m
        item["walking_minutes"] = dist_mins
        item["nbp_district_avg"] = nbp_avg
        item["market_diff"] = market_diff
        item["future_infra_2030"] = future_plans
        
        enriched_data.append(item)
        
    with open("warsaw_apartments_2027_enriched.json", "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, indent=4, ensure_ascii=False)
        
    logging.info("Enrichment completed!")

if __name__ == "__main__":
    process()
