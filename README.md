# RacinglinAI Project

## Project Overview
A data analysis and visualization project focused on racing data, featuring Jupyter notebooks for data processing and a Streamlit web application for interactive exploration.

## Project Structure
```
RacinglinAi/
├── data/               # Processed data files
├── notebooks/          # Jupyter notebooks (e.g., export_monza_data.ipynb)
├── reports/            # Analysis reports
├── streamlit_app.py    # Streamlit application
└── requirements.txt    # Python dependencies
```

## Getting Started

### Prerequisites
- Python 3.8+
- pip package manager

### Installation
1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate environment:
   - Mac/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`

## Usage
- Run Streamlit app: `streamlit run streamlit_app.py`
- Launch Jupyter: `jupyter notebook`

## Data Processing
Our data pipeline now processes all 2023 Formula 1 races:

### Notebooks:
- `export_all_race_data_2023.ipynb`: Processes all 2023 Grand Prix data including:
  - Lap time analysis
  - Sector timing breakdowns
  - Driver performance metrics
  - Generates unified dataset (`all_races_combined_with_sectors.csv`)

### Processed Data Includes:
- 20+ individual race datasets
- Combined dataset with sector analysis
- Cleaned and normalized timing data

### Current Progress:
- Completed data extraction for all 2023 races
- Implemented sector-based performance analysis
- Developed unified data schema across all races
- Streamlit visualization app in development

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request
