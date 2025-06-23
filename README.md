# Advanced Disaster Relief Dashboard 🌍

A comprehensive real-time disaster monitoring and relief coordination platform built with Streamlit. This dashboard provides emergency responders, government agencies, and relief organizations with critical information about natural disasters and resource management capabilities.

![Dashboard Preview](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)

## 🚀 Features

### Real-Time Disaster Monitoring
- **Earthquake Detection**: Live earthquake data with magnitude, depth, and severity analysis
- **Wildfire Tracking**: Active wildfire monitoring with containment status and affected areas
- **Weather Alerts**: Severe weather warnings and meteorological hazards
- **Interactive Mapping**: Dynamic folium-based maps with customizable layers

### Relief Operations Management
- **Relief Center Status**: Real-time capacity monitoring and resource tracking
- **Occupancy Analytics**: Visual indicators for shelter availability and utilization
- **Resource Allocation**: Inventory management for supplies and equipment
- **Contact Information**: Emergency contact details for coordination

### Advanced Analytics
- **Statistical Dashboard**: Key metrics and trend analysis
- **Data Visualization**: Interactive charts using Plotly
- **Historical Analysis**: Magnitude distribution and depth correlation
- **Risk Assessment**: Severity-based alert prioritization

### Regional Filtering
- **Global View**: Worldwide disaster monitoring
- **UAE Focus**: United Arab Emirates specific data
- **Canada Focus**: Canadian disaster information
- **Custom Regions**: Expandable for additional countries

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Mapping**: Folium with Leaflet.js
- **Charts**: Plotly Express & Graph Objects
- **Data Processing**: Pandas, NumPy
- **HTTP Requests**: Requests library
- **Styling**: Custom CSS with responsive design

## 📋 Prerequisites

- Python 3.8 or higher
- Active internet connection for API data
- Modern web browser (Chrome, Firefox, Safari, Edge)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/disaster-relief-dashboard.git
   cd disaster-relief-dashboard
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run dashboard.py
   ```

5. **Access the dashboard**
   - Open your browser and navigate to `http://localhost:8501`

## 📦 Dependencies

```txt
streamlit>=1.28.0
pandas>=1.5.0
requests>=2.28.0
folium>=0.14.0
streamlit-folium>=0.13.0
plotly>=5.15.0
numpy>=1.24.0
```

## 🔌 API Configuration

The dashboard connects to a disaster data API. Update the API endpoint in the configuration:

```python
API_BASE_URL = "https://disaster-dashboard-jgh7.onrender.com"
```

### API Endpoints
- `/earthquakes` - Earthquake data with filtering options
- `/wildfires` - Active wildfire information
- `/weather-alerts` - Severe weather warnings
- `/relief-centers` - Emergency shelter and resource data
- `/statistics` - Aggregated metrics and analytics

## 🎛️ Dashboard Controls

### Sidebar Features
- **Auto-refresh Toggle**: Enable/disable automatic data updates (30-second intervals)
- **Manual Refresh**: Force immediate data reload
- **Region Filter**: Switch between Global, UAE, and Canada views
- **Data Source Toggles**: Show/hide specific disaster types
- **Earthquake Filters**: Adjust magnitude thresholds and result limits
- **Map Style**: Toggle between light and dark map themes

### Main Interface
- **Interactive Map**: Click markers for detailed disaster information
- **Statistics Cards**: Key metrics at a glance
- **Alert Panel**: High-priority warnings and notifications
- **Relief Center Status**: Real-time capacity and resource information
- **Analytics Charts**: Magnitude distributions and correlation analysis
- **Data Tables**: Detailed tabular views with export capabilities

## 🗺️ Map Features

### Disaster Markers
- **Earthquakes**: Color-coded by magnitude with severity indicators
- **Wildfires**: Fire icons with containment percentage
- **Relief Centers**: Shelter icons with occupancy status
- **Weather Alerts**: Warning symbols for severe conditions

### Interactive Elements
- **Popup Windows**: Detailed information on click
- **Layer Control**: Toggle different data layers
- **Map Styles**: Light and dark theme options
- **Zoom Controls**: Navigate to specific regions
- **Full-screen Mode**: Expanded map view

## 📊 Analytics & Reporting

### Earthquake Analytics
- Magnitude distribution histograms
- Depth vs. magnitude scatter plots
- Severity classification charts
- Temporal trend analysis

### Relief Operations
- Capacity utilization metrics
- Resource availability tracking
- Occupancy rate indicators
- Contact information management

### Data Export
- CSV export functionality
- Printable report generation
- API data access
- Historical data archives

## 🔧 Customization

### Adding New Regions
Update the `COUNTRY_CONFIGS` dictionary:

```python
'new_country': {
    'name': 'Country Name',
    'center_lat': latitude,
    'center_lon': longitude,
    'zoom': zoom_level
}
```

### Custom Styling
Modify the CSS in the `st.markdown()` sections:

```python
st.markdown("""
<style>
    .custom-class {
        /* Your custom styles */
    }
</style>
""", unsafe_allow_html=True)
```

### API Integration
Add new data sources by extending the `fetch_data` method and creating corresponding map layers.

## 🚨 Emergency Response Integration

This dashboard is designed to integrate with emergency response protocols:

- **Real-time Alerts**: Automatic notifications for high-severity events
- **Resource Coordination**: Relief center capacity and resource tracking
- **Multi-agency Support**: Shareable interface for coordination between organizations
- **Mobile Responsive**: Accessible on tablets and smartphones for field operations

## 🔒 Security & Privacy

- No personal data collection or storage
- API calls use secure HTTPS connections
- No authentication required for public safety information
- Open-source codebase for transparency

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comments for complex functions
- Test new features thoroughly
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Contact

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check the wiki for detailed guides
- **Emergency Use**: This tool is supplementary to official emergency services
- **Updates**: Watch the repository for new features and improvements

## 🙏 Acknowledgments

- **Data Sources**: 
  - USGS Earthquake Hazards Program
  - NASA FIRMS (Fire Information for Resource Management System)
  - NOAA Weather Alerts
- **Mapping**: OpenStreetMap contributors
- **Libraries**: Streamlit, Folium, Plotly communities

**⚠️ Disclaimer**: This dashboard is for informational purposes and should supplement, not replace, official emergency services and disaster response protocols. Always follow guidance from local emergency management authorities.
