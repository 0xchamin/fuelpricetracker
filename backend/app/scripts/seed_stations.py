import asyncio
import httpx
from sqlalchemy import text
from app.database import engine, Base, async_session
from app.models import Station

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Query for fuel stations on the island of Ireland
OVERPASS_QUERY = """
[out:json][timeout:60];
area["ISO3166-1"="IE"]->.roi;
(
  node["amenity"="fuel"](area.roi);
  way["amenity"="fuel"](area.roi);
);
out center;
"""

# Query for EV charging stations
OVERPASS_QUERY_EV = """
[out:json][timeout:60];
area["ISO3166-1"="IE"]->.roi;
(
  node["amenity"="charging_station"](area.roi);
  way["amenity"="charging_station"](area.roi);
);
out center;
"""


async def fetch_overpass(query: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=90) as client:
        res = await client.post(OVERPASS_URL, data={"data": query})
        res.raise_for_status()
        data = res.json()
    return data.get("elements", [])


def parse_element(el: dict, station_type: str = "fuel") -> dict | None:
    if el["type"] == "node":
        lat, lng = el["lat"], el["lon"]
    elif el["type"] == "way" and "center" in el:
        lat, lng = el["center"]["lat"], el["center"]["lon"]
    else:
        return None

    tags = el.get("tags", {})
    name = tags.get("name", tags.get("brand", "Unknown"))
    brand = tags.get("brand")
    county = tags.get("addr:county")

    return {
        "name": name,
        "brand": brand,
        "lat": lat,
        "lng": lng,
        "county": county,
        "station_type": station_type,
    }


async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Fetching fuel stations from Overpass...")
    fuel_elements = await fetch_overpass(OVERPASS_QUERY)
    print(f"  Found {len(fuel_elements)} fuel station elements")

    print("Fetching EV charging stations from Overpass...")
    ev_elements = await fetch_overpass(OVERPASS_QUERY_EV)
    print(f"  Found {len(ev_elements)} EV charging elements")

    stations = []
    for el in fuel_elements:
        parsed = parse_element(el, "fuel")
        if parsed:
            stations.append(parsed)

    for el in ev_elements:
        parsed = parse_element(el, "ev")
        if parsed:
            stations.append(parsed)

    print(f"Inserting {len(stations)} stations into database...")

    async with async_session() as session:
        for s in stations:
            station = Station(
                name=s["name"],
                brand=s["brand"],
                lat=s["lat"],
                lng=s["lng"],
                geom=f"SRID=4326;POINT({s['lng']} {s['lat']})",
                county=s["county"],
                station_type=s["station_type"],
            )
            session.add(station)
        await session.commit()

    print("Done! Stations seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
