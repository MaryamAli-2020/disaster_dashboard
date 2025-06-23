import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List
import numpy as np

# Backwards compatibility fix
import collections
import collections.abc
collections.Iterable = collections.abc.Iterable

# Page configuration
st.set_page_config(
    page_title="Advanced Disaster Relief Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-low {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000"
REFRESH_INTERVAL = 30  # seconds

class DisasterDashboard:
    def __init__(self):
        # Country specific configurations
        self.COUNTRY_CONFIGS = {
            'uae': {
                'name': 'United Arab Emirates',
                'center_lat': 24.0,
                'center_lon': 54.0,
                'zoom': 7
            },
            'canada': {
                'name': 'Canada',
                'center_lat': 56.1304,
                'center_lon': -106.3468,
                'zoom': 4
            },
            'all': {
                'name': 'Global',
                'center_lat': 20.0,
                'center_lon': 0.0,
                'zoom': 2
            }
        }
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
        if 'data_cache' not in st.session_state:
            st.session_state.data_cache = {}
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        if 'selected_country' not in st.session_state:
            st.session_state.selected_country = 'all'
    
    def fetch_data(self, endpoint: str, use_cache: bool = True) -> Dict:
        """Fetch data from API with caching"""
        try:
            cache_key = endpoint
            now = datetime.now()
            
            # Check cache validity
            if (use_cache and cache_key in st.session_state.data_cache and 
                now - st.session_state.data_cache[cache_key]['timestamp'] < timedelta(seconds=REFRESH_INTERVAL)):
                return st.session_state.data_cache[cache_key]['data']
            
            # Fetch fresh data
            response = requests.get(f"{API_BASE_URL}/{endpoint}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Update cache
            st.session_state.data_cache[cache_key] = {
                'data': data,
                'timestamp': now
            }
            
            return data
            
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch data from {endpoint}: {str(e)}")
            return {}
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return {}
    
    def create_map(self, country: str = 'all') -> folium.Map:
        """Create base map with custom styling"""
        config = self.COUNTRY_CONFIGS[country]
        m = folium.Map(
            location=[config['center_lat'], config['center_lon']],
            zoom_start=config['zoom'],
            tiles='OpenStreetMap'
        )
        
        # Add dark mode tile layer option
        folium.TileLayer(
            tiles='CartoDB dark_matter',
            attr='CartoDB',
            name='Dark Mode',
            overlay=False,
            control=True
        ).add_to(m)
        
        return m
    
    def add_earthquakes_to_map(self, m: folium.Map, earthquake_data: Dict):
        """Add earthquake markers to map"""
        if not earthquake_data or 'features' not in earthquake_data:
            return
        
        for feature in earthquake_data['features']:
            if 'geometry' not in feature or 'properties' not in feature:
                continue
                
            coords = feature['geometry']['coordinates']
            props = feature['properties']
            
            # Determine marker properties based on severity
            mag = props.get('mag', 0)
            severity = props.get('severity', 'Unknown')
            color = props.get('color', 'blue')
            
            # Create custom icon based on magnitude
            if mag >= 7.0:
                icon = folium.Icon(color='darkred', icon='warning-sign', prefix='fa')
                radius = 15
            elif mag >= 6.0:
                icon = folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
                radius = 12
            elif mag >= 5.0:
                icon = folium.Icon(color='orange', icon='exclamation-circle', prefix='fa')
                radius = 10
            else:
                icon = folium.Icon(color=color, icon='circle', prefix='fa')
                radius = 8
            
            # Create popup content
            popup_content = f"""
            <div style="width: 200px;">
                <h4>{props.get('title', 'Unknown Event')}</h4>
                <p><strong>Magnitude:</strong> {mag}</p>
                <p><strong>Severity:</strong> {severity}</p>
                <p><strong>Depth:</strong> {props.get('depth', 'N/A')} km</p>
                <p><strong>Time:</strong> {props.get('formatted_time', 'N/A')}</p>
                <p><strong>Risk Level:</strong> {props.get('risk_level', 'N/A')}</p>
            </div>
            """
            
            folium.Marker(
                location=[coords[1], coords[0]],
                popup=folium.Popup(popup_content, max_width=250),
                icon=icon,
                tooltip=f"Magnitude {mag} - {severity}"
            ).add_to(m)
    
    def add_wildfires_to_map(self, m: folium.Map, wildfire_data: Dict):
        """Add wildfire markers to map"""
        if not wildfire_data or 'features' not in wildfire_data:
            return
        
        for feature in wildfire_data['features']:
            coords = feature['geometry']['coordinates']
            props = feature['properties']
            
            popup_content = f"""
            <div style="width: 200px;">
                <h4>{props.get('title', 'Wildfire')}</h4>
                <p><strong>Acres Burned:</strong> {props.get('acres_burned', 'N/A'):,}</p>
                <p><strong>Containment:</strong> {props.get('containment', 'N/A')}%</p>
                <p><strong>Severity:</strong> {props.get('severity', 'N/A')}</p>
            </div>
            """
            
            folium.Marker(
                location=[coords[1], coords[0]],
                popup=folium.Popup(popup_content, max_width=250),
                icon=folium.Icon(color='red', icon='fire', prefix='fa'),
                tooltip=f"Wildfire - {props.get('severity', 'Unknown')} Severity"
            ).add_to(m)
    
    def add_relief_centers_to_map(self, m: folium.Map, relief_data: Dict):
        """Add relief center markers to map"""
        if not relief_data or 'features' not in relief_data:
            return
        
        for feature in relief_data['features']:
            coords = feature['geometry']['coordinates']
            props = feature['properties']
            
            occupancy_rate = (props.get('current_occupancy', 0) / props.get('capacity', 1)) * 100
            
            popup_content = f"""
            <div style="width: 250px;">
                <h4>{props.get('name', 'Relief Center')}</h4>
                <p><strong>Capacity:</strong> {props.get('capacity', 'N/A')}</p>
                <p><strong>Current Occupancy:</strong> {props.get('current_occupancy', 'N/A')}</p>
                <p><strong>Occupancy Rate:</strong> {occupancy_rate:.1f}%</p>
                <p><strong>Resources:</strong> {', '.join(props.get('resources', []))}</p>
                <p><strong>Contact:</strong> {props.get('contact', 'N/A')}</p>
            </div>
            """
            
            # Color based on occupancy
            if occupancy_rate > 80:
                color = 'red'
            elif occupancy_rate > 60:
                color = 'orange'
            else:
                color = 'green'
            
            folium.Marker(
                location=[coords[1], coords[0]],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color=color, icon='home', prefix='fa'),
                tooltip=f"Relief Center - {occupancy_rate:.1f}% occupied"
            ).add_to(m)
    
    def create_earthquake_charts(self, earthquake_data: Dict):
        """Create earthquake analysis charts"""
        if not earthquake_data or 'features' not in earthquake_data:
            return None, None
        
        # Prepare data
        features = earthquake_data['features']
        df_data = []
        
        for feature in features:
            props = feature['properties']
            df_data.append({
                'magnitude': props.get('mag', 0),
                'depth': props.get('depth', 0),
                'severity': props.get('severity', 'Unknown'),
                'time': props.get('time', 0)
            })
        
        if not df_data:
            return None, None
            
        df = pd.DataFrame(df_data)
        
        # Magnitude distribution
        fig_mag = px.histogram(
            df, 
            x='magnitude', 
            title='Earthquake Magnitude Distribution',
            nbins=20,
            color_discrete_sequence=['#1f77b4']
        )
        fig_mag.update_layout(
            xaxis_title="Magnitude",
            yaxis_title="Count",
            showlegend=False
        )
        
        # Magnitude vs Depth scatter plot
        fig_scatter = px.scatter(
            df,
            x='depth',
            y='magnitude',
            color='severity',
            title='Earthquake Magnitude vs Depth',
            hover_data=['magnitude', 'depth']
        )
        fig_scatter.update_layout(
            xaxis_title="Depth (km)",
            yaxis_title="Magnitude"
        )
        
        return fig_mag, fig_scatter
    
    def display_statistics_cards(self, stats: Dict):
        """Display key statistics in cards"""
        if not stats:
            st.warning("No statistics available")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Earthquakes",
                value=stats.get('total_earthquakes', 0),
                delta=None
            )
        
        with col2:
            st.metric(
                label="Severe Earthquakes (M≥6.0)",
                value=stats.get('severe_earthquakes', 0),
                delta=None
            )
        
        with col3:
            st.metric(
                label="Active Wildfires",
                value=stats.get('total_wildfires', 0),
                delta=None
            )
        
        with col4:
            avg_mag = stats.get('avg_earthquake_magnitude', 0)
            st.metric(
                label="Avg Earthquake Magnitude",
                value=f"{avg_mag:.2f}" if avg_mag else "N/A",
                delta=None
            )
    
    def display_recent_alerts(self, earthquake_data: Dict, wildfire_data: Dict):
        """Display recent high-priority alerts"""
        alerts = []
        
        # High magnitude earthquakes
        if earthquake_data and 'features' in earthquake_data:
            for feature in earthquake_data['features']:
                props = feature['properties']
                mag = props.get('mag', 0)
                if mag >= 6.0:
                    alerts.append({
                        'type': 'Earthquake',
                        'severity': 'High' if mag >= 7.0 else 'Medium',
                        'message': f"M{mag} earthquake: {props.get('title', 'Unknown location')}",
                        'time': props.get('formatted_time', 'Unknown time')
                    })
        
        # High severity wildfires
        if wildfire_data and 'features' in wildfire_data:
            for feature in wildfire_data['features']:
                props = feature['properties']
                if props.get('severity') in ['High', 'Extreme']:
                    alerts.append({
                        'type': 'Wildfire',
                        'severity': props.get('severity', 'Unknown'),
                        'message': f"Wildfire: {props.get('title', 'Unknown location')} - {props.get('acres_burned', 0):,} acres",
                        'time': 'Active'
                    })
        
        if alerts:
            st.subheader("🚨 Recent High-Priority Alerts")
            for alert in alerts[:5]:
                severity_class = f"alert-{alert['severity'].lower()}"
                st.markdown(f"""
    <style>
        .alert-high {{ background-color: #ffebee; border-left: 4px solid #f44336; }}
        .alert-medium {{ background-color: #fff8e1; border-left: 4px solid #ff9800; }}
        .alert-low {{ background-color: #e8f5e9; border-left: 4px solid #4caf50; }}
        .alert-high, .alert-medium, .alert-low {{
            padding: 12px;
            margin: 10px 0;
            border-radius: 4px;
            color: #333333 !important;  /* Darker font color */
            font-family: sans-serif;
        }}
        .alert-high strong, .alert-medium strong, .alert-low strong {{
            color: #222222 !important;  /* Even darker for strong elements */
        }}
    </style>
    <div class="{severity_class}">
        <strong>{alert['type']} - {alert['severity']} Severity</strong><br>
        {alert['message']}<br>
        <small style="color: #555555;">Time: {alert['time']}</small>
    </div>
                """, unsafe_allow_html=True)

    def display_relief_center_status(self, relief_data: Dict):
        """Display relief center capacity status"""
        if not relief_data or 'features' not in relief_data:
            return
        
        # Add CSS to prevent text truncation
        st.markdown("""
        <style>
            .stMetric {
                min-width: 120px;
            }
            .stMetric > div {
                white-space: nowrap;
                overflow: visible;
            }
            .stText {
                white-space: normal !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.subheader("🏠 Relief Center Status")
        
        for feature in relief_data['features']:
            props = feature['properties']
            name = props.get('name', 'Unknown Center')
            capacity = props.get('capacity', 0)
            occupancy = props.get('current_occupancy', 0)
            occupancy_rate = (occupancy / capacity * 100) if capacity > 0 else 0
            
            # Adjust column ratios to give more space
            col1, col2, col3 = st.columns([3, 1.5, 1.5])
            
            with col1:
                st.write(f"**{name}**")
                resources = props.get('resources', [])
                # Display resources with wrapping
                st.markdown(f"<div style='white-space: normal;'>Resources: {', '.join(resources)}</div>", 
                        unsafe_allow_html=True)
            
            with col2:
                # Use markdown to prevent truncation
                st.markdown(f"**Capacity**  \n{occupancy}/{capacity}")
            
            with col3:
                color = "🔴" if occupancy_rate > 80 else "🟡" if occupancy_rate > 60 else "🟢"
                # Use markdown to prevent truncation
                st.markdown(f"**Status**  \n{color} {occupancy_rate:.0f}%")
            
    def run(self):
        """Main application runner"""
        # Header
        country = st.session_state.selected_country
        region_name = self.COUNTRY_CONFIGS[country]['name']
        st.markdown(f'<h1 class="main-header">Advanced Disaster Relief Dashboard - {region_name}</h1>', unsafe_allow_html=True)
        
        # Sidebar controls
        with st.sidebar:
            st.header("⚙️ Dashboard Controls")
            
            # Auto-refresh toggle
            auto_refresh = st.checkbox("Auto-refresh data", value=st.session_state.auto_refresh)
            st.session_state.auto_refresh = auto_refresh
            
            # Manual refresh button
            if st.button("🔄 Refresh Now"):
                st.session_state.data_cache = {}
                st.rerun()
            
            # Country selection
            st.subheader("🌏 Region Filter")
            country = st.selectbox(
                "Select Region",
                options=['all', 'uae', 'canada'],
                format_func=lambda x: self.COUNTRY_CONFIGS[x]['name'],
                key='selected_country'
            )
            
            # Data source filters
            st.subheader("Data Sources")
            show_earthquakes = st.checkbox("Show Earthquakes", value=True)
            show_wildfires = st.checkbox("Show Wildfires", value=True)
            show_weather = st.checkbox("Show Weather Alerts", value=True)
            show_relief = st.checkbox("Show Relief Centers", value=True)
            
            # Earthquake filters
            if show_earthquakes:
                st.subheader("Earthquake Filters")
                eq_limit = st.slider("Max Earthquakes", 10, 200, 50)
                min_magnitude = st.slider("Min Magnitude", 0.0, 8.0, 2.5, 0.1)
            else:
                eq_limit, min_magnitude = 50, 2.5
            
            # Map settings
            st.subheader("Map Settings")
            map_style = st.selectbox("Map Style", ["OpenStreetMap", "Dark Mode"])
            
            # Last update info
            st.subheader("ℹ️ Status")
            st.write(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
            
            # Auto-refresh timer
            if auto_refresh:
                time_since_refresh = (datetime.now() - st.session_state.last_refresh).seconds
                if time_since_refresh >= REFRESH_INTERVAL:
                    st.session_state.data_cache = {}
                    st.session_state.last_refresh = datetime.now()
                    st.rerun()
                
                progress = time_since_refresh / REFRESH_INTERVAL
                st.progress(min(progress, 1.0))
                st.write(f"Next refresh in: {REFRESH_INTERVAL - time_since_refresh}s")
        
        # Fetch data based on settings
        with st.spinner("Loading disaster data..."):
            data = {}
            
            if show_earthquakes:
                data['earthquakes'] = self.fetch_data(
                    f"earthquakes?limit={eq_limit}&min_magnitude={min_magnitude}&country={country}"
                )
            
            if show_wildfires:
                data['wildfires'] = self.fetch_data(f"wildfires?country={country}")
            
            if show_weather:
                data['weather_alerts'] = self.fetch_data(f"weather-alerts?country={country}")
            
            if show_relief:
                data['relief_centers'] = self.fetch_data(f"relief-centers?country={country}")
            
            # Get statistics
            stats = self.fetch_data(f"statistics?country={country}")

            # Create and populate map
            m = self.create_map(country)
        
        # Display statistics cards
        if stats:
            st.subheader(f"📊 Current Statistics - {region_name}")
            self.display_statistics_cards(stats)
            st.markdown("---")
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🗺️ Real-Time Disaster Map")
            # Create and populate map
            m = self.create_map(country)
            if show_earthquakes and data.get('earthquakes'):
                self.add_earthquakes_to_map(m, data['earthquakes'])
            if show_wildfires and data.get('wildfires'):
                self.add_wildfires_to_map(m, data['wildfires'])
            if show_relief and data.get('relief_centers'):
                self.add_relief_centers_to_map(m, data['relief_centers'])
            folium.LayerControl().add_to(m)
            map_data = st_folium(m, width=800, height=600)
        
        with col2:
            # Display alerts
            self.display_recent_alerts(
                data.get('earthquakes', {}),
                data.get('wildfires', {})
            )
            
            # Display relief center status
            if show_relief and data.get('relief_centers'):
                self.display_relief_center_status(data['relief_centers'])
        
        # Analytics section
        if show_earthquakes and data.get('earthquakes'):
            st.markdown("---")
            st.subheader("📊 Earthquake Analytics")
            
            chart_col1, chart_col2 = st.columns(2)
            
            with st.spinner("Generating earthquake analytics..."):
                fig_mag, fig_scatter = self.create_earthquake_charts(data['earthquakes'])
                
                if fig_mag and fig_scatter:
                    with chart_col1:
                        st.plotly_chart(fig_mag, use_container_width=True)
                    
                    with chart_col2:
                        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Data tables section
        with st.expander("📋 Detailed Data Tables"):
            tab1, tab2, tab3 = st.tabs(["Earthquakes", "Wildfires", "Relief Centers"])
            
            with tab1:
                if show_earthquakes and data.get('earthquakes'):
                    eq_features = data['earthquakes'].get('features', [])
                    if eq_features:
                        eq_df = pd.DataFrame([
                            {
                                'Title': f['properties'].get('title', 'N/A'),
                                'Magnitude': f['properties'].get('mag', 0),
                                'Depth (km)': f['properties'].get('depth', 0),
                                'Severity': f['properties'].get('severity', 'N/A'),
                                'Risk Level': f['properties'].get('risk_level', 'N/A'),
                                'Time': f['properties'].get('formatted_time', 'N/A')
                            }
                            for f in eq_features
                        ])
                        st.dataframe(eq_df, use_container_width=True)
                    else:
                        st.info("No earthquake data available")
            
            with tab2:
                if show_wildfires and data.get('wildfires'):
                    wf_features = data['wildfires'].get('features', [])
                    if wf_features:
                        wf_df = pd.DataFrame([
                            {
                                'Name': f['properties'].get('title', 'N/A'),
                                'Severity': f['properties'].get('severity', 'N/A'),
                                'Acres Burned': f['properties'].get('acres_burned', 0),
                                'Containment (%)': f['properties'].get('containment', 0)
                            }
                            for f in wf_features
                        ])
                        st.dataframe(wf_df, use_container_width=True)
                    else:
                        st.info("No wildfire data available")
            
            with tab3:
                if show_relief and data.get('relief_centers'):
                    rc_features = data['relief_centers'].get('features', [])
                    if rc_features:
                        rc_df = pd.DataFrame([
                            {
                                'Name': f['properties'].get('name', 'N/A'),
                                'Capacity': f['properties'].get('capacity', 0),
                                'Current Occupancy': f['properties'].get('current_occupancy', 0),
                                'Occupancy Rate (%)': round((f['properties'].get('current_occupancy', 0) / 
                                                          f['properties'].get('capacity', 1)) * 100, 1),
                                'Resources': ', '.join(f['properties'].get('resources', [])),
                                'Contact': f['properties'].get('contact', 'N/A')
                            }
                            for f in rc_features
                        ])
                        st.dataframe(rc_df, use_container_width=True)
                    else:
                        st.info("No relief center data available")
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666;">
            <p>Advanced Disaster Relief Dashboard | Real-time monitoring and resource management</p>
            <p>Data sources: USGS Earthquake Hazards Program, FIRMS, NOAA Weather Alerts</p>
        </div>
        """, unsafe_allow_html=True)

# Run the application
if __name__ == "__main__":
    dashboard = DisasterDashboard()
    dashboard.run()