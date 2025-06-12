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
The `export_monza_data.ipynb` notebook contains the data processing pipeline for:
- Data extraction
- Cleaning and transformation
- Feature engineering
- Export to processed formats

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request
