import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DisasterType(Enum):
    EARTHQUAKE = "earthquake"
    WILDFIRE = "wildfire"
    FLOOD = "flood"
    HURRICANE = "hurricane"
    TSUNAMI = "tsunami"

class Country(Enum):
    UAE = "uae"
    CANADA = "canada"
    ALL = "all"

@dataclass
class CountryBounds:
    name: str
    code: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    center_lat: float
    center_lon: float

# Define country boundaries
COUNTRY_BOUNDS = {
    Country.UAE: CountryBounds(
        name="United Arab Emirates",
        code="AE",
        min_lat=22.5,
        max_lat=26.5,
        min_lon=51.0,
        max_lon=56.5,
        center_lat=24.0,
        center_lon=54.0
    ),
    Country.CANADA: CountryBounds(
        name="Canada",
        code="CA",
        min_lat=41.0,
        max_lat=84.0,
        min_lon=-141.0,
        max_lon=-52.0,
        center_lat=60.0,
        center_lon=-95.0
    )
}

@dataclass
class DisasterEvent:
    id: str
    type: DisasterType
    title: str
    magnitude: Optional[float]
    location: tuple
    timestamp: datetime
    severity: str
    affected_area: Optional[float]
    casualties: Optional[int]
    status: str
    description: str
    source: str
    country: Optional[str] = None

class DisasterDataService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache:
            return False
        return datetime.now() - self.cache[key]["timestamp"] < self.cache_duration
    
    def _get_country_from_coordinates(self, lat: float, lon: float) -> Optional[str]:
        """Determine country from coordinates"""
        for country, bounds in COUNTRY_BOUNDS.items():
            if (bounds.min_lat <= lat <= bounds.max_lat and 
                bounds.min_lon <= lon <= bounds.max_lon):
                return bounds.name
        return None
    
    def _filter_by_country(self, data: Dict, country: Country) -> Dict:
        """Filter geojson data by country boundaries"""
        if country == Country.ALL:
            return data
        
        if country not in COUNTRY_BOUNDS:
            return {"type": "FeatureCollection", "features": []}
        
        bounds = COUNTRY_BOUNDS[country]
        filtered_features = []
        
        for feature in data.get("features", []):
            coords = feature.get("geometry", {}).get("coordinates", [])
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
                
                # Check if coordinates are within country bounds
                if (bounds.min_lat <= lat <= bounds.max_lat and 
                    bounds.min_lon <= lon <= bounds.max_lon):
                    
                    # Add country information to properties
                    feature["properties"]["country"] = bounds.name
                    feature["properties"]["country_code"] = bounds.code
                    filtered_features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": filtered_features,
            "metadata": {
                "country": bounds.name,
                "country_code": bounds.code,
                "total_filtered": len(filtered_features)
            }
        }
    
    async def get_earthquakes(self, limit: int = 50, min_magnitude: float = 2.5, 
                            country: Country = Country.ALL) -> Dict:
        cache_key = f"earthquakes_{limit}_{min_magnitude}_{country.value}"
        
        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached earthquake data for {country.value}")
            return self.cache[cache_key]["data"]
        
        try:
            # For country-specific requests, adjust the bounding box
            params = {
                "format": "geojson",
                "limit": limit * 2,  # Get more data to ensure we have enough after filtering
                "minmagnitude": min_magnitude,
                "orderby": "time"
            }
            
            # Add geographic bounds for more efficient querying
            if country != Country.ALL and country in COUNTRY_BOUNDS:
                bounds = COUNTRY_BOUNDS[country]
                params.update({
                    "minlatitude": bounds.min_lat,
                    "maxlatitude": bounds.max_lat,
                    "minlongitude": bounds.min_lon,
                    "maxlongitude": bounds.max_lon
                })
            
            url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process and enrich earthquake data
            processed_data = self._process_earthquake_data(data)
            
            # Filter by country
            filtered_data = self._filter_by_country(processed_data, country)
            
            # Limit results after filtering
            if len(filtered_data["features"]) > limit:
                filtered_data["features"] = filtered_data["features"][:limit]
            
            self.cache[cache_key] = {
                "data": filtered_data,
                "timestamp": datetime.now()
            }
            
            logger.info(f"Fetched {len(filtered_data['features'])} earthquake events for {country.value}")
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error fetching earthquake data: {e}")
            return {"type": "FeatureCollection", "features": []}
    
    def _process_earthquake_data(self, data: Dict) -> Dict:
        """Process and enrich earthquake data with severity classifications"""
        for feature in data["features"]:
            props = feature["properties"]
            mag = props.get("mag", 0)
            
            # Add severity classification
            if mag >= 7.0:
                severity = "Extreme"
                color = "darkred"
            elif mag >= 6.0:
                severity = "Severe"
                color = "red"
            elif mag >= 5.0:
                severity = "Strong"
                color = "orange"
            elif mag >= 4.0:
                severity = "Moderate"
                color = "yellow"
            else:
                severity = "Light"
                color = "green"
            
            props["severity"] = severity
            props["color"] = color
            props["risk_level"] = self._calculate_risk_level(mag, props.get("depth", 0))
            
            # Add formatted timestamp
            if props.get("time"):
                props["formatted_time"] = datetime.fromtimestamp(
                    props["time"] / 1000
                ).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return data
    
    def _calculate_risk_level(self, magnitude: float, depth: float) -> str:
        """Calculate risk level based on magnitude and depth"""
        depth_factor = 1.0 if depth < 70 else 0.8 if depth < 300 else 0.6
        risk_score = magnitude * depth_factor
        
        if risk_score >= 6.5:
            return "Critical"
        elif risk_score >= 5.5:
            return "High"
        elif risk_score >= 4.0:
            return "Medium"
        else:
            return "Low"
    
    async def get_wildfires(self, country: Country = Country.ALL) -> Dict:
        """Get wildfire data filtered by country"""
        cache_key = f"wildfires_{country.value}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        
        # Enhanced wildfire data with country-specific incidents
        all_wildfires = {
            "type": "FeatureCollection",
            "features": [
                # UAE Wildfires (rare but possible)
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [55.2708, 25.2048]  # Dubai area
                    },
                    "properties": {
                        "title": "Al Hajar Mountains Brush Fire",
                        "severity": "Low",
                        "acres_burned": 120,
                        "containment": 85,
                        "color": "yellow",
                        "type": "wildfire",
                        "country": "United Arab Emirates"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [56.0833, 24.3667]  # Abu Dhabi Emirate
                    },
                    "properties": {
                        "title": "Empty Quarter Vegetation Fire",
                        "severity": "Low",
                        "acres_burned": 85,
                        "containment": 95,
                        "color": "green",
                        "type": "wildfire",
                        "country": "United Arab Emirates"
                    }
                },
                # Canadian Wildfires
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-114.0719, 51.0447]  # Calgary, Alberta
                    },
                    "properties": {
                        "title": "Alberta Forest Fire",
                        "severity": "High",
                        "acres_burned": 45000,
                        "containment": 15,
                        "color": "red",
                        "type": "wildfire",
                        "country": "Canada"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-123.1207, 49.2827]  # Vancouver, BC
                    },
                    "properties": {
                        "title": "British Columbia Mountain Fire",
                        "severity": "Extreme",
                        "acres_burned": 78000,
                        "containment": 5,
                        "color": "darkred",
                        "type": "wildfire",
                        "country": "Canada"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-106.3468, 52.1332]  # Saskatchewan
                    },
                    "properties": {
                        "title": "Saskatchewan Prairie Fire",
                        "severity": "Medium",
                        "acres_burned": 12000,
                        "containment": 40,
                        "color": "orange",
                        "type": "wildfire",
                        "country": "Canada"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-79.3832, 43.6532]  # Toronto, Ontario
                    },
                    "properties": {
                        "title": "Ontario Conservation Area Fire",
                        "severity": "Low",
                        "acres_burned": 850,
                        "containment": 75,
                        "color": "yellow",
                        "type": "wildfire",
                        "country": "Canada"
                    }
                }
            ]
        }
        
        # Filter by country
        filtered_data = self._filter_by_country(all_wildfires, country)
        
        self.cache[cache_key] = {
            "data": filtered_data,
            "timestamp": datetime.now()
        }
        
        return filtered_data
    
    async def get_weather_alerts(self, country: Country = Country.ALL) -> Dict:
        """Get weather alerts filtered by country"""
        cache_key = f"weather_alerts_{country.value}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        
        all_alerts = {
            "type": "FeatureCollection",
            "features": [
                # UAE Weather Alerts
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [55.2708, 25.2048]  # Dubai
                    },
                    "properties": {
                        "title": "Dust Storm Warning - Dubai",
                        "severity": "Medium",
                        "alert_type": "Dust Storm",
                        "color": "orange",
                        "type": "weather_alert",
                        "country": "United Arab Emirates"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [54.3773, 24.4539]  # Abu Dhabi
                    },
                    "properties": {
                        "title": "Extreme Heat Advisory - Abu Dhabi",
                        "severity": "High",
                        "alert_type": "Extreme Heat",
                        "color": "red",
                        "type": "weather_alert",
                        "country": "United Arab Emirates"
                    }
                },
                # Canadian Weather Alerts
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-75.6972, 45.4215]  # Ottawa
                    },
                    "properties": {
                        "title": "Severe Thunderstorm Watch - Ottawa",
                        "severity": "Medium",
                        "alert_type": "Thunderstorm",
                        "color": "orange",
                        "type": "weather_alert",
                        "country": "Canada"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-114.0719, 51.0447]  # Calgary
                    },
                    "properties": {
                        "title": "Blizzard Warning - Calgary",
                        "severity": "Extreme",
                        "alert_type": "Blizzard",
                        "color": "purple",
                        "type": "weather_alert",
                        "country": "Canada"
                    }
                }
            ]
        }
        
        filtered_data = self._filter_by_country(all_alerts, country)
        
        self.cache[cache_key] = {
            "data": filtered_data,
            "timestamp": datetime.now()
        }
        
        return filtered_data
    
    async def get_relief_centers(self, country: Country = Country.ALL) -> Dict:
        """Get relief center locations filtered by country"""
        all_centers = {
            "type": "FeatureCollection",
            "features": [
                # UAE Relief Centers
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [55.2708, 25.2048]  # Dubai
                    },
                    "properties": {
                        "name": "Dubai Emergency Response Center",
                        "capacity": 300,
                        "current_occupancy": 45,
                        "resources": ["Medical", "Food", "Shelter", "Transportation"],
                        "contact": "+971-4-123-4567",
                        "type": "relief_center",
                        "country": "United Arab Emirates"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [54.3773, 24.4539]  # Abu Dhabi
                    },
                    "properties": {
                        "name": "Abu Dhabi Crisis Management Center",
                        "capacity": 500,
                        "current_occupancy": 120,
                        "resources": ["Medical", "Food", "Shelter", "Communications"],
                        "contact": "+971-2-987-6543",
                        "type": "relief_center",
                        "country": "United Arab Emirates"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [56.3269, 25.3382]  # Sharjah
                    },
                    "properties": {
                        "name": "Sharjah Emergency Services Hub",
                        "capacity": 200,
                        "current_occupancy": 30,
                        "resources": ["Medical", "Food", "Shelter"],
                        "contact": "+971-6-555-0123",
                        "type": "relief_center",
                        "country": "United Arab Emirates"
                    }
                },
                # Canadian Relief Centers
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-75.6972, 45.4215]  # Ottawa
                    },
                    "properties": {
                        "name": "Ottawa Emergency Management Center",
                        "capacity": 800,
                        "current_occupancy": 250,
                        "resources": ["Medical", "Food", "Shelter", "Mental Health"],
                        "contact": "+1-613-555-0100",
                        "type": "relief_center",
                        "country": "Canada"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-114.0719, 51.0447]  # Calgary
                    },
                    "properties": {
                        "name": "Calgary Disaster Relief Station",
                        "capacity": 600,
                        "current_occupancy": 180,
                        "resources": ["Medical", "Food", "Shelter", "Pet Care"],
                        "contact": "+1-403-555-0200",
                        "type": "relief_center",
                        "country": "Canada"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-123.1207, 49.2827]  # Vancouver
                    },
                    "properties": {
                        "name": "Vancouver Emergency Response Hub",
                        "capacity": 1000,
                        "current_occupancy": 420,
                        "resources": ["Medical", "Food", "Shelter", "Transportation", "Translation"],
                        "contact": "+1-604-555-0300",
                        "type": "relief_center",
                        "country": "Canada"
                    }
                }
            ]
        }
        
        filtered_data = self._filter_by_country(all_centers, country)
        return filtered_data
    
    async def get_disaster_statistics(self, country: Country = Country.ALL) -> Dict:
        """Get aggregated disaster statistics filtered by country"""
        try:
            earthquakes = await self.get_earthquakes(country=country)
            wildfires = await self.get_wildfires(country=country)
            weather_alerts = await self.get_weather_alerts(country=country)
            
            stats = {
                "country": country.value,
                "country_name": COUNTRY_BOUNDS[country].name if country in COUNTRY_BOUNDS else "Global",
                "total_earthquakes": len(earthquakes["features"]),
                "severe_earthquakes": len([
                    f for f in earthquakes["features"] 
                    if f["properties"].get("mag", 0) >= 6.0
                ]),
                "total_wildfires": len(wildfires["features"]),
                "active_weather_alerts": len(weather_alerts["features"]),
                "last_updated": datetime.now().isoformat()
            }
            
            # Calculate average magnitude
            mags = [f["properties"].get("mag", 0) for f in earthquakes["features"]]
            stats["avg_earthquake_magnitude"] = sum(mags) / len(mags) if mags else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating statistics for {country.value}: {e}")
            return {}
    
    def get_country_bounds(self, country: Country) -> Optional[CountryBounds]:
        """Get geographical bounds for a country"""
        return COUNTRY_BOUNDS.get(country)
    
    def get_available_countries(self) -> List[Dict]:
        """Get list of available countries for filtering"""
        return [
            {
                "code": country.value,
                "name": bounds.name,
                "center": [bounds.center_lat, bounds.center_lon]
            }
            for country, bounds in COUNTRY_BOUNDS.items()
        ]

# Global service instance
disaster_service = DisasterDataService()