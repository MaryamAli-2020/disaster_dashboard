from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import asyncio
from datetime import datetime
import logging
from contextlib import asynccontextmanager

# Import your disaster service
from backend.services.disaster_data import disaster_service, Country

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Disaster Relief API")
    yield
    # Shutdown
    logger.info("Shutting down Disaster Relief API")
    await disaster_service.client.aclose()

app = FastAPI(
    title="Advanced Disaster Relief & Resource API",
    description="Real-time disaster monitoring and resource management system with country filtering",
    version="2.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "message": "Advanced Disaster Relief API with Country Filtering",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "supported_countries": ["uae", "canada", "all"]
    }

@app.get("/countries", tags=["Configuration"])
async def get_available_countries():
    """Get list of available countries for filtering"""
    try:
        countries = disaster_service.get_available_countries()
        return JSONResponse(content={
            "countries": countries,
            "total": len(countries)
        })
    except Exception as e:
        logger.error(f"Error fetching countries: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch available countries")

@app.get("/earthquakes", tags=["Disasters"])
async def get_earthquakes(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of earthquakes to return"),
    min_magnitude: float = Query(2.5, ge=0, le=10, description="Minimum earthquake magnitude"),
    country: str = Query("all", description="Country filter: 'uae', 'canada', or 'all'")
):
    """
    Get recent earthquake data from USGS with severity classifications, filtered by country
    """
    try:
        # Validate country parameter
        try:
            country_enum = Country(country.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid country '{country}'. Supported: uae, canada, all"
            )
        
        data = await disaster_service.get_earthquakes(
            limit=limit, 
            min_magnitude=min_magnitude,
            country=country_enum
        )
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching earthquakes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch earthquake data")

@app.get("/wildfires", tags=["Disasters"])
async def get_wildfires(
    country: str = Query("all", description="Country filter: 'uae', 'canada', or 'all'")
):
    """
    Get active wildfire information filtered by country
    """
    try:
        # Validate country parameter
        try:
            country_enum = Country(country.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid country '{country}'. Supported: uae, canada, all"
            )
        
        data = await disaster_service.get_wildfires(country=country_enum)
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching wildfires: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch wildfire data")

@app.get("/weather-alerts", tags=["Disasters"])
async def get_weather_alerts(
    country: str = Query("all", description="Country filter: 'uae', 'canada', or 'all'")
):
    """
    Get active weather alerts and warnings filtered by country
    """
    try:
        # Validate country parameter
        try:
            country_enum = Country(country.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid country '{country}'. Supported: uae, canada, all"
            )
        
        data = await disaster_service.get_weather_alerts(country=country_enum)
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching weather alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch weather alert data")

@app.get("/relief-centers", tags=["Resources"])
async def get_relief_centers(
    country: str = Query("all", description="Country filter: 'uae', 'canada', or 'all'")
):
    """
    Get relief center locations and capacity information filtered by country
    """
    try:
        # Validate country parameter
        try:
            country_enum = Country(country.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid country '{country}'. Supported: uae, canada, all"
            )
        
        data = await disaster_service.get_relief_centers(country=country_enum)
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching relief centers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch relief center data")

@app.get("/all-disasters", tags=["Disasters"])
async def get_all_disasters(
    include_earthquakes: bool = Query(True, description="Include earthquake data"),
    include_wildfires: bool = Query(True, description="Include wildfire data"),
    include_weather: bool = Query(True, description="Include weather alerts"),
    include_relief: bool = Query(True, description="Include relief centers"),
    earthquake_limit: int = Query(25, ge=1, le=100),
    min_magnitude: float = Query(2.5, ge=0, le=10),
    country: str = Query("all", description="Country filter: 'uae', 'canada', or 'all'")
):
    """
    Get all disaster data in a single request, filtered by country
    """
    try:
        # Validate country parameter
        try:
            country_enum = Country(country.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid country '{country}'. Supported: uae, canada, all"
            )
        
        tasks = []
        task_types = []
        
        if include_earthquakes:
            tasks.append(disaster_service.get_earthquakes(earthquake_limit, min_magnitude, country_enum))
            task_types.append("earthquakes")
        if include_wildfires:
            tasks.append(disaster_service.get_wildfires(country_enum))
            task_types.append("wildfires")
        if include_weather:
            tasks.append(disaster_service.get_weather_alerts(country_enum))
            task_types.append("weather_alerts")
        if include_relief:
            tasks.append(disaster_service.get_relief_centers(country_enum))
            task_types.append("relief_centers")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        response = {
            "country": country,
            "country_name": disaster_service.get_country_bounds(country_enum).name if country_enum != Country.ALL else "Global"
        }
        
        for i, task_type in enumerate(task_types):
            if not isinstance(results[i], Exception):
                response[task_type] = results[i]
            else:
                logger.error(f"Error fetching {task_type}: {results[i]}")
                response[task_type] = {"type": "FeatureCollection", "features": []}
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching all disasters: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch disaster data")

@app.get("/statistics", tags=["Analytics"])
async def get_statistics(
    country: str = Query("all", description="Country filter: 'uae', 'canada', or 'all'")
):
    """
    Get aggregated disaster statistics and metrics filtered by country
    """
    try:
        # Validate country parameter
        try:
            country_enum = Country(country.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid country '{country}'. Supported: uae, canada, all"
            )
        
        stats = await disaster_service.get_disaster_statistics(country=country_enum)
        return JSONResponse(content=stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")

@app.get("/earthquake/{event_id}", tags=["Disasters"])
async def get_earthquake_details(
    event_id: str,
    country: str = Query("all", description="Country filter for search scope")
):
    """
    Get detailed information about a specific earthquake event
    """
    try:
        # Validate country parameter
        try:
            country_enum = Country(country.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid country '{country}'. Supported: uae, canada, all"
            )
        
        earthquakes = await disaster_service.get_earthquakes(limit=200, country=country_enum)
        
        for feature in earthquakes["features"]:
            if feature["id"] == event_id:
                return JSONResponse(content=feature)
        
        raise HTTPException(status_code=404, detail="Earthquake event not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching earthquake details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch earthquake details")

@app.get("/country-bounds/{country}", tags=["Configuration"])
async def get_country_bounds(country: str):
    """
    Get geographical bounds for a specific country
    """
    try:
        try:
            country_enum = Country(country.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid country '{country}'. Supported: uae, canada"
            )
        
        if country_enum == Country.ALL:
            raise HTTPException(status_code=400, detail="Cannot get bounds for 'all' countries")
        
        bounds = disaster_service.get_country_bounds(country_enum)
        if not bounds:
            raise HTTPException(status_code=404, detail="Country bounds not found")
        
        return JSONResponse(content={
            "country": country,
            "name": bounds.name,
            "code": bounds.code,
            "bounds": {
                "min_lat": bounds.min_lat,
                "max_lat": bounds.max_lat,
                "min_lon": bounds.min_lon,
                "max_lon": bounds.max_lon
            },
            "center": {
                "lat": bounds.center_lat,
                "lon": bounds.center_lon
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching country bounds: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch country bounds")

@app.post("/alert", tags=["Alerts"])
async def create_alert(background_tasks: BackgroundTasks):
    """
    Create a new disaster alert (placeholder for future implementation)
    """
    # This would integrate with notification systems
    background_tasks.add_task(log_alert_creation)
    return {"message": "Alert creation initiated", "status": "processing"}

def log_alert_creation():
    """Background task for logging alert creation"""
    logger.info("New disaster alert created")

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check with service status"""
    try:
        # Test database/service connections
        stats = await disaster_service.get_disaster_statistics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "earthquake_api": "operational",
                "cache": "operational",
                "statistics": "operational" if stats else "degraded"
            },
            "supported_countries": ["uae", "canada", "all"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)