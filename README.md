# Healthcare Data Governance Framework

A comprehensive healthcare data governance framework implementing NHS standards for data classification, quality monitoring, and compliance. This project demonstrates best practices for managing healthcare data with proper governance controls.

## Project Overview

This framework provides a complete solution for healthcare organisations to effectively govern their data assets while maintaining compliance with NHS standards and GDPR requirements. It includes:

- **Automated Data Classification System**: Identifies and categorizes sensitive healthcare data
- **Data Quality Monitoring**: Ensures accuracy and completeness of patient information
- **NHS Compliance Controls**: Implements required security and privacy measures
- **Data Lineage Tracking**: Visualizes how data flows through healthcare systems
- **Governance Dashboards**: Provides visibility into data quality and compliance metrics

## Architecture

The framework consists of several integrated components:

- **Data Sources Layer**: Connects to synthetic healthcare data (simulating Patient Records, Hospital Administrative Data, Clinical Systems)
- **Governance Layer**: Implements classification, quality checks, and compliance controls
- **Visibility Layer**: Provides dashboards and reporting for stakeholders

## Getting Started

### Prerequisites

- Python 3.8+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/YourUsername/healthcare-data-governance.git
cd healthcare-data-governance

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Generate synthetic data
python src/data_generators/patient_data_generator.py

# Start the dashboard
streamlit run src/dashboard/app.py
```

## Features

### 1. Data Classification

- Automatically identifies Personal Identifiable Information (PII)
- Classifies data according to NHS Data Security standards
- Assigns risk scores to different data categories

### 2. Data Quality Monitoring

- Validates data against predefined healthcare data standards
- Monitors data completeness, accuracy, and consistency
- Generates data quality scorecards

### 3. Compliance Controls

- Implements GDPR requirements for healthcare data
- Provides audit trails for data access and modifications
- Manages patient consent records

### 4. Data Lineage

- Tracks data from source to consumption
- Visualizes data transformations and dependencies
- Enables impact analysis for potential changes

## 📊 Dashboard

The integrated Streamlit dashboard provides:

- Executive summary of data governance metrics
- Data quality monitoring reports
- Compliance status indicators
- Data classification statistics

## Technology Stack

- **Backend**: Python, Flask
- **Database**: SQLite
- **Data Processing**: Pandas, NumPy, Great Expectations
- **Frontend/Dashboard**: Streamlit
- **Visualization**: Plotly, Matplotlib

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📚 Documentation

For more detailed documentation:

- [Architecture Overview](docs/architecture.md)
- [NHS Compliance Requirements](docs/nhs_compliance.md)
- [Implementation Guide](docs/implementation_guide.md)