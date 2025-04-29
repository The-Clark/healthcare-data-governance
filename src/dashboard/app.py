"""
NHS Data Governance Dashboard

This module provides a Streamlit dashboard for visualizing and monitoring
the data governance framework for NHS healthcare data.
"""

import os
import sys
import pandas as pd
import numpy as np
import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import glob

# Add parent directory to path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from other modules
from classification.data_classifier import NHSDataClassifier
from quality_monitoring.data_quality import NHSDataQualityMonitor

# Constants
DATA_DIR = 'data'
CLASSIFICATION_DIR = 'data/classified'
QUALITY_DIR = 'data/quality'

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CLASSIFICATION_DIR, exist_ok=True)
os.makedirs(QUALITY_DIR, exist_ok=True)

# Set page configuration
st.set_page_config(
    page_title="NHS Data Governance Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

def color_classification(val):
    colors = {
        "PUBLIC": "background-color: #ABEBC6",      # Light green
        "INTERNAL": "background-color: #AED6F1",    # Light blue
        "CONFIDENTIAL": "background-color: #FAD7A0", # Light orange
        "RESTRICTED": "background-color: #F5B7B1"    # Light red
    }
    return colors.get(val, "")

def color_compliance_status(val):
    colors = {
        "Complete": "background-color: #ABEBC6",       # Light green
        "In Progress": "background-color: #FAD7A0",    # Light orange
        "Not Started": "background-color: #F5B7B1"     # Light red
    }
    return colors.get(val, "")

def color_pass_rate(val):
    rate = float(val.strip('%'))
    if rate == 100:
        return "background-color: #ABEBC6"  # Light green
    elif rate >= 80:
        return "background-color: #AED6F1"  # Light blue
    elif rate >= 60:
        return "background-color: #FAD7A0"  # Light orange
    else:
        return "background-color: #F5B7B1"  # Light red
    
# Load data and reports
@st.cache(ttl=300, allow_output_mutation=True)  # Cache for 5 minutes
def load_data_files():
    """Load list of data files"""
    return [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]

@st.cache(ttl=300, allow_output_mutation=True)
def load_classification_summary():
    """Load classification summary if it exists"""
    summary_path = os.path.join(CLASSIFICATION_DIR, "classification_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            return json.load(f)
    return None

@st.cache(ttl=300, allow_output_mutation=True)
def load_quality_summary():
    """Load quality summary if it exists"""
    summary_path = os.path.join(QUALITY_DIR, "quality_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            return json.load(f)
    return None

@st.cache(ttl=300, allow_output_mutation=True)
def load_dataset_classification(file_name):
    """Load classification report for a specific dataset"""
    classification_path = os.path.join(CLASSIFICATION_DIR, f"{os.path.splitext(file_name)[0]}_classification.json")
    if os.path.exists(classification_path):
        with open(classification_path, 'r') as f:
            return json.load(f)
    return None

@st.cache(ttl=300, allow_output_mutation=True)
def load_dataset_quality(file_name):
    """Load quality report for a specific dataset"""
    quality_path = os.path.join(QUALITY_DIR, f"{os.path.splitext(file_name)[0]}_quality.json")
    if os.path.exists(quality_path):
        with open(quality_path, 'r') as f:
            return json.load(f)
    return None

@st.cache(ttl=300, allow_output_mutation=True)
def load_dataset(file_name):
    """Load a dataset"""
    file_path = os.path.join(DATA_DIR, file_name)
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return None

def run_data_classification():
    """Run data classification on all datasets"""
    with st.spinner("Classifying data... This may take a moment."):
        classifier = NHSDataClassifier(data_dir=DATA_DIR, output_dir=CLASSIFICATION_DIR)
        classifier.classify_all_datasets()
        st.success("Data classification complete!")
        st.experimental_rerun()

def run_data_quality_check():
    """Run data quality check on all datasets"""
    with st.spinner("Checking data quality... This may take a moment."):
        monitor = NHSDataQualityMonitor(data_dir=DATA_DIR, output_dir=QUALITY_DIR)
        monitor.validate_all_datasets()
        st.success("Data quality check complete!")
        st.experimental_rerun()

# Sidebar
st.sidebar.image("/Users/dee/Desktop/Projects/healthcare-data-governance/National_Health_Service_(England)_logo.svg.png", width=300)
st.sidebar.title("NHS Data Governance")

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    ["Executive Summary", "Data Classification", "Data Quality", "GDPR Compliance", "Data Lineage"]
)

# Button to run data classification/quality check
st.sidebar.subheader("Data Governance Tools")
with st.sidebar.expander("Run Data Governance Tools"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Run Classification", key="run_classification"):
            run_data_classification()
    with col2:
        if st.button("Run Quality Check", key="run_quality"):
            run_data_quality_check()

# Load data files
data_files = load_data_files()
if not data_files:
    st.warning("No data files found in the data directory. Please generate or upload data files.")
    st.stop()

# Load summaries
classification_summary = load_classification_summary()
quality_summary = load_quality_summary()

# Executive Summary Page
if page == "Executive Summary":
    st.title("NHS Data Governance Executive Summary")
    
    # Dashboard last updated
    now = datetime.now().strftime("%d %B %Y, %H:%M:%S")
    st.caption(f"Dashboard last updated: {now}")
    
    # Overview metrics
    st.subheader("Data Governance Overview")
    
    # Create three columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Datasets", len(data_files))
    
    with col2:
        if classification_summary:
            restricted_count = classification_summary["classification_summary"].get("RESTRICTED", 0)
            st.metric("Restricted Datasets", restricted_count, 
                     delta=f"{restricted_count/len(data_files)*100:.1f}%" if len(data_files) > 0 else "0%")
        else:
            st.metric("Restricted Datasets", "N/A")
    
    with col3:
        if quality_summary and "average_quality_score" in quality_summary:
            st.metric("Avg. Quality Score", f"{quality_summary['average_quality_score']:.1f}%")
        else:
            st.metric("Avg. Quality Score", "N/A")
            
    with col4:
        if classification_summary:
            # Calculate average PII density if it exists
            if "average_pii_density" in classification_summary:
                st.metric("Avg. PII Density", f"{classification_summary['average_pii_density']:.1f}%")
            else:
                st.metric("Avg. PII Density", "N/A")
        else:
            st.metric("Avg. PII Density", "N/A")
    
    # Two-column layout for charts
    col1, col2 = st.columns(2)
    
    # Data Classification Chart
    with col1:
        st.subheader("Data Classification Distribution")
        if classification_summary:
            # Prepare data for chart
            classes = list(classification_summary["classification_summary"].keys())
            counts = list(classification_summary["classification_summary"].values())
            
            # Create a color map with red for RESTRICTED
            color_map = {
                "PUBLIC": "green",
                "INTERNAL": "blue",
                "CONFIDENTIAL": "orange",
                "RESTRICTED": "red"
            }
            colors = [color_map.get(cls, "gray") for cls in classes]
            
            # Create pie chart
            fig = go.Figure(data=[go.Pie(
                labels=classes,
                values=counts,
                marker_colors=colors,
                hole=0.4
            )])
            fig.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No classification data available. Run the data classification tool to see results.")
    
    # Data Quality Chart
    with col2:
        st.subheader("Data Quality by Dimension")
        if quality_summary and "datasets" in quality_summary:
            # Extract quality dimensions from the first dataset that has them
            dimensions = None
            for dataset_info in quality_summary["datasets"].values():
                if "dimension_scores" in dataset_info:
                    dimensions = dataset_info["dimension_scores"]
                    break
            
            if dimensions:
                # Prepare data for radar chart
                categories = list(dimensions.keys())
                
                # Calculate average scores for each dimension
                avg_scores = []
                for category in categories:
                    scores = [
                        dataset_info["dimension_scores"].get(category, 0) 
                        for dataset_info in quality_summary["datasets"].values() 
                        if "dimension_scores" in dataset_info
                    ]
    
                    # Filter out None values before calculating the average
                    valid_scores = [score for score in scores if score is not None]
                    if valid_scores:
                        avg_scores.append(sum(valid_scores) / len(valid_scores))
                    else:
                        avg_scores.append(0)
                
                # Create radar chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=avg_scores,
                    theta=categories,
                    fill='toself',
                    name='Average Score',
                    line_color='rgb(31, 119, 180)'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )
                    ),
                    margin=dict(l=40, r=40, t=20, b=40),
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No dimension data available in quality summary.")
        else:
            st.info("No quality data available. Run the data quality check tool to see results.")
    
    # Dataset Overview
    st.subheader("Dataset Overview")
    
    # Create a dataframe with dataset info
    dataset_info = []
    
    for file_name in data_files:
        info = {
            "Dataset": file_name,
            "Records": "Unknown",
            "Classification": "Unknown",
            "Quality Score": "Unknown",
            "Risk Level": "Unknown"
        }
        
        # Add classification info if available
        classification = load_dataset_classification(file_name)
        if classification:
            info["Classification"] = classification.get("overall_classification", "Unknown")
            info["Risk Level"] = classification.get("overall_risk_score", "Unknown")
        
        # Add quality info if available
        quality = load_dataset_quality(file_name)
        if quality and "quality_score" in quality:
            info["Quality Score"] = f"{quality['quality_score']['overall_score']:.1f}%"
            info["Records"] = quality.get("record_count", "Unknown")
        
        dataset_info.append(info)
    
    # Create dataframe and display
    if dataset_info:
        df_info = pd.DataFrame(dataset_info)
        
        # Apply conditional formatting for classification
        def color_classification(val):
            colors = {
                "PUBLIC": "background-color: #ABEBC6",      # Light green
                "INTERNAL": "background-color: #AED6F1",    # Light blue
                "CONFIDENTIAL": "background-color: #FAD7A0", # Light orange
                "RESTRICTED": "background-color: #F5B7B1"    # Light red
            }
            return colors.get(val, "")
        
        # Display with styling
        st.dataframe(df_info.reset_index(drop=True).style.map(color_classification, subset=["Classification"]))
    else:
        st.info("No datasets found.")
    
    # Compliance at a glance
    st.subheader("GDPR Compliance Status")
    
    # Create a simulated compliance status based on classification and quality
    compliance_status = {
        "Data Protection Impact Assessment": {
            "status": "Complete" if classification_summary else "Not Started", 
            "last_updated": datetime.now().strftime("%Y-%m-%d") if classification_summary else "N/A"
        },
        "Data Classification": {
            "status": "Complete" if classification_summary else "Not Started",
            "last_updated": classification_summary["classification_date"] if classification_summary else "N/A"
        },
        "Data Quality Assessment": {
            "status": "Complete" if quality_summary else "Not Started",
            "last_updated": quality_summary["validation_date"] if quality_summary else "N/A"
        },
        "Privacy Notice": {"status": "Complete", "last_updated": "2023-01-15"},
        "Consent Management": {"status": "In Progress", "last_updated": "2023-03-20"},
        "Data Subject Rights Process": {"status": "Complete", "last_updated": "2023-02-10"},
        "Data Breach Response Plan": {"status": "Complete", "last_updated": "2023-01-30"}
    }
    
    # Convert to dataframe
    df_compliance = pd.DataFrame.from_dict(compliance_status, orient='index')
    df_compliance.reset_index(inplace=True)
    df_compliance.columns = ["Requirement", "Status", "Last Updated"]
    
    # Apply conditional formatting
    def color_compliance_status(val):
        colors = {
            "Complete": "background-color: #ABEBC6",       # Light green
            "In Progress": "background-color: #FAD7A0",    # Light orange
            "Not Started": "background-color: #F5B7B1"     # Light red
        }
        return colors.get(val, "")
    
    # Display with styling
    st.dataframe(df_compliance.reset_index(drop=True).style.map(color_compliance_status, subset=["Status"]))

# Data Classification Page
elif page == "Data Classification":
    st.title("NHS Data Classification")
    
    # Button to run classification
    if st.button("Run Data Classification", key="run_classification_main"):
        run_data_classification()
    
    # Display classification summary
    if classification_summary:
        st.subheader("Classification Summary")
        st.caption(f"Last classified: {classification_summary.get('classification_date', 'Unknown')}")
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Datasets", classification_summary.get("total_datasets", 0))
        
        with col2:
            restricted = classification_summary["classification_summary"].get("RESTRICTED", 0)
            st.metric("RESTRICTED", restricted)
        
        with col3:
            confidential = classification_summary["classification_summary"].get("CONFIDENTIAL", 0)
            st.metric("CONFIDENTIAL", confidential)
        
        with col4:
            public_internal = (classification_summary["classification_summary"].get("PUBLIC", 0) + 
                              classification_summary["classification_summary"].get("INTERNAL", 0))
            st.metric("PUBLIC/INTERNAL", public_internal)
        
        # Create classification distribution chart
        st.subheader("Classification Distribution")
        
        # Prepare data for chart
        classes = list(classification_summary["classification_summary"].keys())
        counts = list(classification_summary["classification_summary"].values())
        
        # Create bar chart
        fig = px.bar(
            x=classes, 
            y=counts,
            color=classes,
            color_discrete_map={
                "PUBLIC": "green",
                "INTERNAL": "blue",
                "CONFIDENTIAL": "orange",
                "RESTRICTED": "red"
            },
            labels={"x": "Classification Level", "y": "Number of Datasets"}
        )
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Select a dataset to view detailed classification
    st.subheader("Dataset Classification Details")
    selected_dataset = st.selectbox("Select a dataset", data_files)
    
    # Load and display classification for selected dataset
    classification = load_dataset_classification(selected_dataset)
    if classification:
        # Display classification info
        st.markdown(f"**Overall Classification:** `{classification.get('overall_classification', 'Unknown')}`")
        st.markdown(f"**Risk Score:** `{classification.get('overall_risk_score', 'Unknown')}`")
        st.markdown(f"**Handling Requirements:** {classification.get('handling_requirements', 'Unknown')}")
        st.markdown(f"**PII Density:** {classification.get('pii_density', 0):.1f}%")
        
        # Display column classification table
        st.subheader("Column Classification")
        
        if "columns" in classification:
            # Convert columns data to dataframe
            columns_data = []
            for col in classification["columns"]:
                columns_data.append({
                    "Column Name": col["column_name"],
                    "Classification": col["classification"],
                    "Is PII": "Yes" if col["is_pii"] else "No",
                    "Is Clinical": "Yes" if col["is_clinical"] else "No",
                    "Risk Score": col["risk_score"],
                    "Handling Requirements": col["handling_requirements"]
                })
            
            df_columns = pd.DataFrame(columns_data)
            
            # Apply conditional formatting for classification
            def color_classification(val):
                colors = {
                    "PUBLIC": "background-color: #ABEBC6",      # Light green
                    "INTERNAL": "background-color: #AED6F1",    # Light blue
                    "CONFIDENTIAL": "background-color: #FAD7A0", # Light orange
                    "RESTRICTED": "background-color: #F5B7B1"    # Light red
                }
                return colors.get(val, "")
            
            # Display with styling
            st.dataframe(df_columns.reset_index(drop=True).style.map(color_classification, subset=["Classification"]))
            
            # Create a pie chart of column classifications
            class_counts = df_columns["Classification"].value_counts().to_dict()
            
            # Prepare data for chart
            pie_classes = list(class_counts.keys())
            pie_counts = list(class_counts.values())
            
            # Create a color map
            color_map = {
                "PUBLIC": "green",
                "INTERNAL": "blue",
                "CONFIDENTIAL": "orange",
                "RESTRICTED": "red"
            }
            colors = [color_map.get(cls, "gray") for cls in pie_classes]
            
            # Create pie chart
            fig = go.Figure(data=[go.Pie(
                labels=pie_classes,
                values=pie_counts,
                marker_colors=colors
            )])
            fig.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No column classification data available.")
    else:
        st.info("No classification data available for this dataset. Run the data classification tool to see results.")

# Data Quality Page
elif page == "Data Quality":
    st.title("NHS Data Quality Monitoring")
    
    # Button to run quality check
    if st.button("Run Data Quality Check", key="run_quality_main"):
        run_data_quality_check()
    
    # Display quality summary
    if quality_summary:
        st.subheader("Quality Summary")
        st.caption(f"Last checked: {quality_summary.get('validation_date', 'Unknown')}")
        
        # Display summary metrics
        col1, col2 = st.columns(2)
        
        with col1:
            if "average_quality_score" in quality_summary:
                st.metric("Average Quality Score", f"{quality_summary['average_quality_score']:.1f}%")
                st.markdown(f"**Interpretation:** {quality_summary.get('overall_interpretation', '')}")
        
        with col2:
            if "datasets" in quality_summary:
                # Count datasets by quality category
                quality_categories = {
                    "Excellent": 0,
                    "Good": 0,
                    "Adequate": 0,
                    "Poor": 0,
                    "Critical": 0
                }
                
                for dataset_info in quality_summary["datasets"].values():
                    if "overall_score" in dataset_info:
                        score = dataset_info["overall_score"]
                        if score >= 95:
                            quality_categories["Excellent"] += 1
                        elif score >= 85:
                            quality_categories["Good"] += 1
                        elif score >= 70:
                            quality_categories["Adequate"] += 1
                        elif score >= 50:
                            quality_categories["Poor"] += 1
                        else:
                            quality_categories["Critical"] += 1
                
                # Create a horizontal bar chart
                fig = go.Figure()
                
                categories = list(quality_categories.keys())
                counts = list(quality_categories.values())
                colors = ["green", "lightgreen", "yellow", "orange", "red"]
                
                fig.add_trace(go.Bar(
                    y=categories,
                    x=counts,
                    orientation='h',
                    marker_color=colors,
                    text=counts,
                    textposition='auto'
                ))
                
                fig.update_layout(
                    title="Datasets by Quality Category",
                    xaxis_title="Number of Datasets",
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=200
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Display dimension scores chart
        if "datasets" in quality_summary:
            # Extract quality dimensions and calculate averages
            dimensions = None
            dimension_scores = {}
            
            for dataset_info in quality_summary["datasets"].values():
                if "dimension_scores" in dataset_info:
                    dimensions = dataset_info["dimension_scores"].keys()
                    for dim, score in dataset_info["dimension_scores"].items():
                        if dim not in dimension_scores:
                            dimension_scores[dim] = []
                        if score is not None:  # Only add non-None scores
                            dimension_scores[dim].append(score)
            
            if dimensions:
                # Calculate averages
                avg_scores = {}
                for dim, scores in dimension_scores.items():
                    if scores:  # Only calculate if there are scores
                        avg_scores[dim] = sum(scores) / len(scores)
                    else:
                        avg_scores[dim] = 0
                
                # Create bar chart
                fig = px.bar(
                    x=list(avg_scores.keys()),
                    y=list(avg_scores.values()),
                    labels={"x": "Quality Dimension", "y": "Average Score (%)"},
                    color=list(avg_scores.keys()),
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                fig.update_layout(
                    title="Average Scores by Quality Dimension",
                    yaxis_range=[0, 100],
                    margin=dict(l=20, r=20, t=40, b=40)
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Select a dataset to view detailed quality info
    st.subheader("Dataset Quality Details")
    selected_dataset = st.selectbox("Select a dataset", data_files, key="quality_dataset_select")
    
    # Load and display quality info for selected dataset
    quality = load_dataset_quality(selected_dataset)
    if quality and "quality_score" in quality:
        # Display quality info
        st.markdown(f"**Overall Quality Score:** `{quality['quality_score']['overall_score']:.1f}%`")
        st.markdown(f"**Interpretation:** {quality['quality_score']['score_interpretation']}")
        
        # Display dimension scores
        st.subheader("Quality Dimensions")
        
        # Create a bar chart of dimension scores
        dimensions = quality['quality_score']['dimension_scores']
        
        # Filter out None values
        dimensions = {k: v for k, v in dimensions.items() if v is not None}
        
        # Prepare data for chart
        dim_names = list(dimensions.keys())
        dim_scores = list(dimensions.values())
        
        # Create bar chart
        fig = px.bar(
            x=dim_names,
            y=dim_scores,
            color=dim_names,
            labels={"x": "Dimension", "y": "Score (%)"},
            color_discrete_sequence=px.colors.qualitative.Plotly,
            text=[f"{score:.1f}%" for score in dim_scores]
        )
        fig.update_layout(
            yaxis_range=[0, 100],
            margin=dict(l=20, r=20, t=20, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display column validation details
        st.subheader("Column Validation Results")
        
        if "column_results" in quality:
            # Convert column results to dataframe
            column_data = []
            for col in quality["column_results"]:
                column_data.append({
                    "Column": col["column"],
                    "Rules Tested": len(col["rules_tested"]),
                    "Rules Passed": len(col["rules_passed"]),
                    "Rules Failed": len(col["rules_failed"]),
                    "Pass Rate": f"{col['pass_percentage']:.1f}%"
                })
            
            df_columns = pd.DataFrame(column_data)
            
            # Apply conditional formatting for pass rate
            def color_pass_rate(val):
                rate = float(val.strip('%'))
                if rate == 100:
                    return "background-color: #ABEBC6"  # Light green
                elif rate >= 80:
                    return "background-color: #AED6F1"  # Light blue
                elif rate >= 60:
                    return "background-color: #FAD7A0"  # Light orange
                else:
                    return "background-color: #F5B7B1"  # Light red
            
            # Display with styling
            try:
                # Use the correct styling function for pass rate
                st.dataframe(df_columns.reset_index(drop=True).style.map(color_pass_rate, subset=["Pass Rate"]))
            except Exception as e:
                # Fallback if styling fails
                st.error(f"Error styling validation results: {str(e)}")
                st.dataframe(df_columns.reset_index(drop=True))
            
            # Display failed rules for each column
            st.subheader("Failed Validation Rules")
            
            for col in quality["column_results"]:
                if col["rules_failed"]:
                    with st.expander(f"{col['column']} - {len(col['rules_failed'])} failed rules"):
                        for failed in col["rules_failed"]:
                            rule = failed.get("rule", "Unknown")
                            if isinstance(failed, dict) and "unexpected_percent" in failed:
                                st.markdown(f"- **{rule}**: {failed['unexpected_percent']:.1f}% of values failed.")
                            elif isinstance(failed, dict) and "error" in failed:
                                st.markdown(f"- **{rule}**: Error - {failed['error']}")
                            else:
                                st.markdown(f"- **{rule}**: Failed")
        else:
            st.info("No column validation data available.")
        
        # Display data profile
        if "data_profile" in quality:
            st.subheader("Data Profile")
            
            profile = quality["data_profile"]
            
            # Display basic profile info
            st.markdown(f"**Records:** {profile.get('record_count', 'Unknown')}")
            st.markdown(f"**Columns:** {profile.get('column_count', 'Unknown')}")
            
            # Display column profiles
            if "columns" in profile:
                # Create tabs for different profile aspects
                tab1, tab2, tab3 = st.tabs(["Completeness", "Data Types", "Column Details"])
                
                with tab1:
                    # Completeness - null percentages
                    completeness_data = []
                    for col_name, col_profile in profile["columns"].items():
                        completeness_data.append({
                            "Column": col_name,
                            "Null %": col_profile.get("null_percentage", 0)
                        })
                    
                    df_completeness = pd.DataFrame(completeness_data)
                    df_completeness = df_completeness.sort_values("Null %", ascending=False)
                    
                    # Create a horizontal bar chart
                    fig = px.bar(
                        df_completeness,
                        y="Column",
                        x="Null %",
                        orientation='h',
                        color="Null %",
                        color_continuous_scale=["green", "yellow", "red"],
                        title="Data Completeness (Null %)",
                        labels={"Null %": "Percentage of Null Values"}
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    # Data types distribution
                    dtype_counts = {}
                    for col_name, col_profile in profile["columns"].items():
                        dtype = col_profile.get("data_type", "Unknown")
                        if dtype in dtype_counts:
                            dtype_counts[dtype] += 1
                        else:
                            dtype_counts[dtype] = 1
                    
                    # Create a pie chart
                    fig = px.pie(
                        values=list(dtype_counts.values()),
                        names=list(dtype_counts.keys()),
                        title="Column Data Types"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab3:
                    # Detailed column profiles
                    selected_column = st.selectbox(
                        "Select a column to view detailed profile",
                        list(profile["columns"].keys())
                    )
                    
                    if selected_column:
                        col_profile = profile["columns"][selected_column]
                        
                        # Display profile info
                        st.markdown(f"**Data Type:** {col_profile.get('data_type', 'Unknown')}")
                        st.markdown(f"**Null Count:** {col_profile.get('null_count', 0)} ({col_profile.get('null_percentage', 0):.1f}%)")
                        st.markdown(f"**Unique Count:** {col_profile.get('unique_count', 0)} ({col_profile.get('unique_percentage', 0):.1f}%)")
                        
                        # Display numeric stats if available
                        if "min" in col_profile:
                            st.subheader("Numeric Statistics")
                            stats_col1, stats_col2 = st.columns(2)
                            
                            with stats_col1:
                                st.markdown(f"**Min:** {col_profile.get('min', 'N/A')}")
                                st.markdown(f"**Max:** {col_profile.get('max', 'N/A')}")
                                st.markdown(f"**Mean:** {col_profile.get('mean', 'N/A')}")
                            
                            with stats_col2:
                                st.markdown(f"**Median:** {col_profile.get('median', 'N/A')}")
                                st.markdown(f"**Std Dev:** {col_profile.get('std', 'N/A')}")
                        
                        # Display string stats if available
                        if "min_length" in col_profile:
                            st.subheader("String Statistics")
                            stats_col1, stats_col2 = st.columns(2)
                            
                            with stats_col1:
                                st.markdown(f"**Min Length:** {col_profile.get('min_length', 'N/A')}")
                                st.markdown(f"**Max Length:** {col_profile.get('max_length', 'N/A')}")
                            
                            with stats_col2:
                                st.markdown(f"**Mean Length:** {col_profile.get('mean_length', 'N/A')}")
                        
                        # Display frequency distribution if available
                        if "frequent_values" in col_profile:
                            st.subheader("Most Frequent Values")
                            
                            # Convert to dataframe
                            freq_data = [
                                {"Value": k, "Count": v}
                                for k, v in col_profile["frequent_values"].items()
                            ]
                            
                            df_freq = pd.DataFrame(freq_data)
                            
                            # Create a bar chart
                            fig = px.bar(
                                df_freq,
                                x="Value",
                                y="Count",
                                title="Frequency Distribution",
                                labels={"Value": "Value", "Count": "Frequency"}
                            )
                            st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No column profile data available.")
    else:
        st.info("No quality data available for this dataset. Run the data quality check tool to see results.")

# GDPR Compliance Page
elif page == "GDPR Compliance":
    st.title("GDPR Compliance Controls")
    
    # GDPR Principles
    st.subheader("GDPR Principles & Controls")
    
    # Create tabs for different GDPR principles
    tabs = st.tabs([
        "Lawfulness & Transparency", 
        "Purpose Limitation", 
        "Data Minimisation", 
        "Accuracy",
        "Storage Limitation",
        "Integrity & Confidentiality"
    ])
    
    # Tab 1: Lawfulness & Transparency
    with tabs[0]:
        st.subheader("Controls Implementation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Data Processing Register")
            st.markdown("""
            - Data processing activities documented
            - Legal basis established for all processing
            - Special category data identified
            - Processing map implemented
            """)
            
            # Simulated control status
            control_status = {
                "Documentation Status": "Complete",
                "Last Updated": "2023-02-15",
                "Risk Level": "Low"
            }
            
            for key, value in control_status.items():
                st.markdown(f"**{key}:** {value}")
        
        with col2:
            st.markdown("### Privacy Notices")
            st.markdown("""
            - Comprehensive privacy notices implemented
            - Clear language used for all audiences
            - Processing purposes clearly stated
            - Data subject rights explained
            """)
            
            # Example privacy notice stats
            notice_stats = {
                "Implementation Status": "Complete",
                "Last Updated": "2023-01-10",
                "Readability Score": "Good"
            }
            
            for key, value in notice_stats.items():
                st.markdown(f"**{key}:** {value}")
        
        # Consent Records Analysis
        st.subheader("Consent Records Analysis")
        
        # Load consent data if available
        consent_file = "patient_consent_records.csv"
        
        if consent_file in data_files:
            df_consent = load_dataset(consent_file)
            
            if df_consent is not None:
                # Analyze consent data
                consent_stats = df_consent.groupby(["consent_type", "consent_given"]).size().unstack()
                
                # Convert to percentage
                consent_pct = consent_stats.div(consent_stats.sum(axis=1), axis=0) * 100
                
                # Create a stacked bar chart
                consent_types = consent_pct.index.tolist()
                consent_yes = consent_pct[True].tolist() if True in consent_pct.columns else [0] * len(consent_types)
                consent_no = consent_pct[False].tolist() if False in consent_pct.columns else [0] * len(consent_types)
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    y=consent_types,
                    x=consent_yes,
                    name='Consent Given',
                    orientation='h',
                    marker=dict(color='green')
                ))
                
                fig.add_trace(go.Bar(
                    y=consent_types,
                    x=consent_no,
                    name='Consent Declined',
                    orientation='h',
                    marker=dict(color='red')
                ))
                
                fig.update_layout(
                    barmode='stack',
                    title="Consent Status by Type",
                    xaxis_title="Percentage",
                    yaxis_title="Consent Type",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display consent records sample
                with st.expander("View Sample Consent Records"):
                    st.dataframe(df_consent.sample(min(10, len(df_consent))).reset_index(drop=True))
            else:
                st.info("Failed to load consent records data.")
        else:
            st.info("No consent records data available. Generate data to see consent analysis.")
    
    # Tab 2: Purpose Limitation
    with tabs[1]:
        st.markdown("""
        ### Purpose Limitation Controls
    
        Purpose limitation ensures that personal data is collected for specified, explicit, and legitimate purposes and not further processed in a manner incompatible with those purposes.
    
        **Implemented Controls:**
    
        1. **Purpose Definition**
           - All data processing activities have documented purposes
           - Purposes are specific, explicit, and legitimate
           - Secondary uses are evaluated for compatibility
    
        2. **Purpose Management**
           - Regular review of processing purposes
           - Mechanisms to enforce purpose limitations
           - Technical controls to prevent function creep
    
        3. **Documentation**
           - Purpose limitation policies established
           - Staff training on purpose limitation
           - Audit trail for purpose reviews
        """)
    
        # Simulated purpose limitation metrics
        st.subheader("Purpose Documentation Status")
    
        purpose_metrics = pd.DataFrame({
            "Data Category": ["Patient Demographics", "Medical Records", "Staff Records", "Audit Logs", "Lab Results"],
            "Purposes Documented": ["Yes", "Yes", "Yes", "Yes", "Yes"],
            "Compatible Use Only": ["Yes", "Yes", "Yes", "Yes", "Partial"],
            "Last Reviewed": ["2023-03-15", "2023-03-15", "2023-02-10", "2023-01-20", "2023-03-01"]
        })
    
        # Display the metrics table without styling (simplest approach)
        st.dataframe(purpose_metrics.reset_index(drop=True))
    
    # Tab 3: Data Minimisation
    with tabs[2]:
        st.markdown("""
        ### Data Minimisation Controls
        
        Data minimisation ensures that personal data is adequate, relevant and limited to what is necessary in relation to the purposes for which they are processed.
        
        **Implemented Controls:**
        
        1. **Data Collection Reviews**
           - Regular assessment of data fields collected
           - Justification for all data elements
           - Removal of unnecessary data fields
        
        2. **Retention Controls**
           - Automated data deletion after retention period
           - Regular data purging processes
           - Archiving strategy for historical data
        
        3. **Data Reduction Techniques**
           - Pseudonymisation where possible
           - Aggregation for statistical purposes
           - Data masking for development/testing
        """)
        
        # Display data minimisation analysis based on classification
        st.subheader("Data Fields Analysis")
        
        # Get classification data for all datasets
        all_columns = []
        for file_name in data_files:
            classification = load_dataset_classification(file_name)
            if classification and "columns" in classification:
                for col in classification["columns"]:
                    all_columns.append({
                        "Dataset": file_name,
                        "Column": col["column_name"],
                        "Classification": col["classification"],
                        "Is PII": "Yes" if col["is_pii"] else "No",
                        "Is Clinical": "Yes" if col["is_clinical"] else "No",
                        "Risk Score": col["risk_score"]
                    })
        
        if all_columns:
            df_all_columns = pd.DataFrame(all_columns)
            
            # Count columns by dataset and classification
            pivot = pd.crosstab(df_all_columns["Dataset"], df_all_columns["Classification"])
            
            # Calculate totals
            pivot["Total"] = pivot.sum(axis=1)
            pivot.loc["Total"] = pivot.sum()
            
            # Display pivot table
            st.dataframe(pivot)
            
            # Create a stacked bar chart of column classifications by dataset
            pivot_chart = pivot.drop("Total", axis=0).drop("Total", axis=1)
            
            datasets = pivot_chart.index.tolist()
            fig = go.Figure()
            
            for classification in pivot_chart.columns:
                fig.add_trace(go.Bar(
                    name=classification,
                    x=datasets,
                    y=pivot_chart[classification],
                    marker_color={
                        "PUBLIC": "green",
                        "INTERNAL": "blue",
                        "CONFIDENTIAL": "orange",
                        "RESTRICTED": "red"
                    }.get(classification, "gray")
                ))
            
            fig.update_layout(
                barmode='stack',
                title="Data Field Classification by Dataset",
                xaxis_title="Dataset",
                yaxis_title="Number of Columns",
                legend_title="Classification"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # PII and Clinical data analysis
            pii_clinical = pd.crosstab(
                df_all_columns["Dataset"], 
                [df_all_columns["Is PII"], df_all_columns["Is Clinical"]]
            )
            
            st.subheader("PII and Clinical Data Analysis")
            st.dataframe(pii_clinical)
            
            # Recommendations based on analysis
            st.subheader("Data Minimisation Recommendations")
            
            # Count of high-risk columns
            high_risk_count = len(df_all_columns[df_all_columns["Risk Score"] >= 2])
            
            recommendations = [
                f"Review {high_risk_count} high-risk columns for necessity",
                "Implement data masking for PII in non-production environments",
                "Establish automated archiving for data older than retention period",
                "Consider pseudonymisation for research and analytics use cases"
            ]
            
            for rec in recommendations:
                st.markdown(f"- {rec}")
        else:
            st.info("No classification data available. Run the data classification tool to see data minimisation analysis.")
    
    # Tab 4: Accuracy
    with tabs[3]:
        st.markdown("""
        ### Data Accuracy Controls
        
        The accuracy principle requires that personal data is accurate and, where necessary, kept up to date. Every reasonable step must be taken to ensure that inaccurate data is erased or rectified without delay.
        
        **Implemented Controls:**
        
        1. **Data Quality Framework**
           - Automated data validation rules
           - Regular data quality assessments
           - Data correction processes
        
        2. **Input Controls**
           - Validation at point of entry
           - Format standardization
           - Duplicate detection
        
        3. **Maintenance Procedures**
           - Regular data cleansing
           - Update mechanisms
           - Data subject verification processes
        """)
        
        # Display data quality results if available
        st.subheader("Data Quality Metrics")
        
        if quality_summary and "datasets" in quality_summary:
            # Create a table of quality scores by dataset
            quality_table = []
            
            for file_name, dataset_info in quality_summary["datasets"].items():
                if "overall_score" in dataset_info:
                    # Get dimension scores
                    completeness = dataset_info["dimension_scores"].get("completeness", "N/A")
                    validity = dataset_info["dimension_scores"].get("validity", "N/A")
                    consistency = dataset_info["dimension_scores"].get("consistency", "N/A")
                    
                    quality_table.append({
                        "Dataset": file_name,
                        "Overall Score": f"{dataset_info['overall_score']:.1f}%",
                        "Completeness": f"{completeness:.1f}%" if isinstance(completeness, (int, float)) else completeness,
                        "Validity": f"{validity:.1f}%" if isinstance(validity, (int, float)) else validity,
                        "Consistency": f"{consistency:.1f}%" if isinstance(consistency, (int, float)) else consistency
                    })
            
            if quality_table:
                df_quality = pd.DataFrame(quality_table)
                st.dataframe(df_quality.reset_index(drop=True))
                
                # Create a radar chart comparing datasets
                if len(quality_table) > 1:
                    st.subheader("Dataset Quality Comparison")
                    
                    # Extract data for chart
                    datasets = [row["Dataset"] for row in quality_table]
                    
                    # Create one trace per dataset
                    fig = go.Figure()
                    
                    for row in quality_table:
                        # Extract dimension scores
                        scores = []
                        for dimension in ["Completeness", "Validity", "Consistency"]:
                            value = row.get(dimension)
                            if value is not None and value != "N/A" and isinstance(value, str):
                                try:
                                    scores.append(float(value.strip('%')))
                                except (ValueError, AttributeError):
                                    scores.append(0)
                            else:
                                scores.append(0)
                        
                        fig.add_trace(go.Scatterpolar(
                            r=scores,
                            theta=["Completeness", "Validity", "Consistency"],
                            fill='toself',
                            name=row["Dataset"]
                        ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100]
                            )
                        ),
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No quality metrics available.")
        else:
            st.info("No quality data available. Run the data quality check tool to see data accuracy metrics.")
    
    # Tab 5: Storage Limitation
    with tabs[4]:
        st.markdown("""
        ### Storage Limitation Controls
        
        Storage limitation requires that personal data is kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the data is processed.
        
        **Implemented Controls:**
        
        1. **Retention Policies**
           - Documented retention periods for all data types
           - Legal basis for retention periods
           - Regular retention reviews
        
        2. **Data Deletion**
           - Automated deletion processes
           - Secure deletion methods
           - Deletion verification
        
        3. **Archiving Strategy**
           - Criteria for archiving vs deletion
           - Secure archive storage
           - Retrieval processes for archived data
        """)
        
        # Display simulated retention schedule
        st.subheader("Data Retention Schedule")
        
        retention_schedule = pd.DataFrame({
            "Data Category": ["Patient Demographics", "Medical Records", "Consent Records", "Audit Logs", "Staff Records"],
            "Retention Period": ["8 years after last treatment", "8 years after last treatment", "8 years after consent withdrawn", "3 years", "6 years after employment ends"],
            "Legal Basis": ["NHS Records Management Code", "NHS Records Management Code", "GDPR Compliance", "System Security", "Employment Law"],
            "Deletion Method": ["Secure Deletion", "Secure Deletion", "Secure Deletion", "Secure Deletion", "Secure Deletion"],
            "Automated": ["Yes", "Yes", "Yes", "Yes", "Yes"]
        })
        
        st.dataframe(retention_schedule.reset_index(drop=True))
        
        # Simulated data age analysis
        st.subheader("Data Age Analysis")
        
        # Check if we have medical records to analyze
        medical_file = "patient_medical_records.csv"
        if medical_file in data_files:
            df_medical = load_dataset(medical_file)
            
            if df_medical is not None and "created_at" in df_medical.columns:
                # Convert to datetime
                df_medical["created_at"] = pd.to_datetime(df_medical["created_at"])
                
                # Calculate age in days
                now = pd.Timestamp.now()
                df_medical["age_days"] = (now - df_medical["created_at"]).dt.days
                
                # Create age buckets
                df_medical["age_bucket"] = pd.cut(
                    df_medical["age_days"],
                    bins=[0, 30, 90, 180, 365, 730, float('inf')],
                    labels=["< 30 days", "30-90 days", "90-180 days", "180-365 days", "1-2 years", "> 2 years"]
                )
                
                # Count by age bucket
                age_counts = df_medical["age_bucket"].value_counts().sort_index()
                
                # Create a bar chart
                fig = px.bar(
                    x=age_counts.index,
                    y=age_counts.values,
                    labels={"x": "Age", "y": "Number of Records"},
                    color=age_counts.index,
                    color_discrete_sequence=px.colors.sequential.Viridis,
                    title="Data Age Distribution"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display retention compliance status
                st.subheader("Retention Compliance Status")
                
                # For demonstration, assuming records older than 2 years need review
                records_to_review = len(df_medical[df_medical["age_days"] > 730])
                
                metrics = {
                    "Records to Review": records_to_review,
                    "Retention Automation Status": "Implemented",
                    "Last Retention Audit": "2023-01-15",
                    "Compliance Status": "Compliant" if records_to_review == 0 else "Review Needed"
                }
                
                for key, value in metrics.items():
                    st.markdown(f"**{key}:** {value}")
            else:
                st.info("Medical records data does not contain creation dates for age analysis.")
        else:
            st.info("No medical records data available for age analysis.")
    
    # Tab 6: Integrity & Confidentiality
    with tabs[5]:
        st.markdown("""
        ### Integrity & Confidentiality Controls
        
        The integrity and confidentiality principle requires that personal data is processed in a manner that ensures appropriate security, including protection against unauthorised or unlawful processing and against accidental loss, destruction or damage.
        
        **Implemented Controls:**
        
        1. **Access Controls**
           - Role-based access control
           - Principle of least privilege
           - Regular access reviews
        
        2. **Data Protection**
           - Encryption at rest and in transit
           - Data masking for sensitive information
           - Secure backup procedures
        
        3. **Monitoring & Audit**
           - User activity logging
           - Breach detection systems
           - Regular security audits
        """)
        
        # Display security metrics based on audit logs
        st.subheader("Security Monitoring Metrics")
        
        # Check if we have audit logs to analyze
        audit_file = "data_access_audit_logs.csv"
        if audit_file in data_files:
            df_audit = load_dataset(audit_file)
            
            if df_audit is not None:
                # Convert timestamp to datetime
                df_audit["timestamp"] = pd.to_datetime(df_audit["timestamp"])
                
                # Count authorized vs unauthorized access
                auth_counts = df_audit["authorized"].value_counts()
                
                # Create a pie chart
                fig = px.pie(
                    names=["Authorized", "Unauthorized"],
                    values=[auth_counts.get(True, 0), auth_counts.get(False, 0)],
                    title="Access Authorization Status",
                    color_discrete_sequence=["green", "red"]
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Count actions
                    action_counts = df_audit["action"].value_counts().head(5)
                    
                    # Create a bar chart
                    fig = px.bar(
                        x=action_counts.index,
                        y=action_counts.values,
                        labels={"x": "Action", "y": "Count"},
                        title="Top 5 Actions"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Unauthorized access details
                if auth_counts.get(False, 0) > 0:
                    st.subheader("Unauthorized Access Details")
                    
                    unauth_access = df_audit[df_audit["authorized"] == False]
                    
                    # Group by staff and count
                    staff_unauth = unauth_access.groupby("staff_name").size().reset_index(name="count")
                    staff_unauth = staff_unauth.sort_values("count", ascending=False)
                    
                    # Display table of unauthorized access
                    st.dataframe(staff_unauth.reset_index(drop=True))
                
                # Security metrics
                st.subheader("Security Status")
                
                total_accesses = len(df_audit)
                unauthorized_rate = auth_counts.get(False, 0) / total_accesses * 100 if total_accesses > 0 else 0
                
                metrics = {
                    "Total Access Attempts": total_accesses,
                    "Unauthorized Access Rate": f"{unauthorized_rate:.2f}%",
                    "Encryption Status": "Implemented (AES-256)",
                    "Last Security Audit": "2023-02-10",
                    "Data Breach Incidents": "0 in last 12 months"
                }
                
                for key, value in metrics.items():
                    st.markdown(f"**{key}:** {value}")
            else:
                st.info("Failed to load audit logs data.")
        else:
            st.info("No audit logs data available for security analysis.")
    
    # GDPR Rights Management
    st.subheader("Data Subject Rights Management")
    
    # Create mock data subject rights requests
    dsr_requests = pd.DataFrame({
        "Request ID": ["DSR-2023-001", "DSR-2023-002", "DSR-2023-003", "DSR-2023-004", "DSR-2023-005"],
        "Request Type": ["Access", "Erasure", "Rectification", "Access", "Restriction"],
        "Date Received": ["2023-01-10", "2023-01-15", "2023-02-05", "2023-02-20", "2023-03-01"],
        "Status": ["Completed", "Completed", "In Progress", "Completed", "In Progress"],
        "Time to Complete": ["25 days", "28 days", "N/A", "20 days", "N/A"]
    })
    
    st.dataframe(dsr_requests.reset_index(drop=True))
    
    # DSR statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Requests", len(dsr_requests))
    
    with col2:
        completed = len(dsr_requests[dsr_requests["Status"] == "Completed"])
        st.metric("Completed", completed, f"{completed/len(dsr_requests)*100:.0f}%")
    
    with col3:
        # Calculate average completion time (only for completed requests)
        completed_times = [int(t.split()[0]) for t in dsr_requests[dsr_requests["Status"] == "Completed"]["Time to Complete"]]
        avg_time = sum(completed_times) / len(completed_times) if completed_times else 0
        st.metric("Avg. Completion Time", f"{avg_time:.1f} days")
    
    # Request type distribution
    request_counts = dsr_requests["Request Type"].value_counts()
    
    # Create pie chart
    fig = px.pie(
        names=request_counts.index,
        values=request_counts.values,
        title="Data Subject Requests by Type"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Data Lineage Page
elif page == "Data Lineage":
    st.title("Data Lineage & Flow")
    
    st.markdown("""
    Data lineage tracking provides visibility into how data flows through systems, how it's transformed,
    and who accesses it. This is critical for both governance and compliance.
    """)
    
    # Simple data flow diagram
    st.subheader("NHS Data Flow Diagram")
    
    # Create a Mermaid diagram
    mermaid_code = """
    graph TD
        A[Patient Registration] -->|Patient Demographics| B[Electronic Health Record]
        B -->|Medical Records| C[Treatment & Care]
        C -->|Lab Orders| D[Laboratory Systems]
        D -->|Lab Results| B
        B -->|Anonymized Data| E[Research Database]
        B -->|Billing Data| F[Finance Systems]
        B -->|Audit Logs| G[Security Monitoring]
        H[Staff Systems] -->|Access Controls| B
        I[External NHS Trust] <-->|Shared Care Records| B
    """
    
    st.markdown(f"```mermaid\n{mermaid_code}\n```")
    
    # Dataset relationships
    st.subheader("Dataset Relationships")
    
    # Create a table showing relationships between datasets
    relationship_data = [
        {"Source Dataset": "patient_demographics.csv", "Relationship": "Primary", "Target Dataset": "patient_medical_records.csv", "Joining Fields": "patient_id, nhs_number"},
        {"Source Dataset": "patient_demographics.csv", "Relationship": "Primary", "Target Dataset": "patient_lab_results.csv", "Joining Fields": "patient_id, nhs_number"},
        {"Source Dataset": "patient_demographics.csv", "Relationship": "Primary", "Target Dataset": "patient_consent_records.csv", "Joining Fields": "patient_id, nhs_number"},
        {"Source Dataset": "patient_medical_records.csv", "Relationship": "Primary", "Target Dataset": "patient_lab_results.csv", "Joining Fields": "record_id"},
        {"Source Dataset": "nhs_staff_records.csv", "Relationship": "Referenced by", "Target Dataset": "data_access_audit_logs.csv", "Joining Fields": "staff_id"}
    ]
    
    st.dataframe(pd.DataFrame(relationship_data).reset_index(drop=True))
    
    # Data transformation lineage
    st.subheader("Data Transformations")
    
    # Create a more detailed Mermaid diagram for a specific dataset
    st.markdown("#### Patient Data Flow")
    
    mermaid_detail = """
    graph TD
        A[Patient Registration Form] -->|Manual Entry| B[patient_demographics.csv]
        B -->|Classification| C[RESTRICTED Classification]
        B -->|Quality Check| D[Data Quality Assessment]
        B -->|Access Control| E[Role-Based Access]
        B -->|Join with| F[patient_medical_records.csv]
        F -->|ETL Process| G[Reporting Database]
        F -->|Anonymization| H[Research Dataset]
        I[Consent Form] -->|Digitization| J[patient_consent_records.csv]
        J -->|Controls| B
        K[Medical Systems] -->|Data Integration| F
        L[Laboratory Systems] -->|Results Import| M[patient_lab_results.csv]
        M -->|Linked to| F
    """
    
    st.markdown(f"```mermaid\n{mermaid_detail}\n```")
    
    # Data lineage tracking
    st.subheader("Data Lineage Controls")
    
    lineage_controls = [
        "**Metadata Repository**: Centralized storage of data definitions, relationships, and transformations",
        "**Data Cataloging**: Documentation of all datasets with ownership and classification",
        "**Transformation Logging**: Tracking of all data transformations and processing",
        "**Audit Trail**: Comprehensive logging of data access and modifications",
        "**Impact Analysis**: Tools to assess the impact of changes to data structures"
    ]
    
    for control in lineage_controls:
        st.markdown(f"- {control}")
    
    # Data access patterns
    st.subheader("Data Access Patterns")
    
    # Check if we have audit logs to analyze
    audit_file = "data_access_audit_logs.csv"
    if audit_file in data_files:
        df_audit = load_dataset(audit_file)
        
        if df_audit is not None:
            # Convert timestamp to datetime
            df_audit["timestamp"] = pd.to_datetime(df_audit["timestamp"])
            
            # Extract hour of day
            df_audit["hour"] = df_audit["timestamp"].dt.hour
            
            # Count access by hour
            hour_counts = df_audit.groupby("hour").size()
            
            # Fill in missing hours
            all_hours = pd.DataFrame({"hour": range(24)})
            hour_counts = all_hours.merge(
                hour_counts.reset_index().rename(columns={0: "count"}),
                on="hour",
                how="left"
            ).fillna(0)
            
            # Create a line chart
            fig = px.line(
                hour_counts,
                x="hour",
                y="count",
                labels={"hour": "Hour of Day", "count": "Number of Accesses"},
                title="Data Access by Hour of Day",
                markers=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Count access by resource type
            resource_counts = df_audit["resource_type"].value_counts()
            
            # Create a bar chart
            fig = px.bar(
                x=resource_counts.index,
                y=resource_counts.values,
                labels={"x": "Resource Type", "y": "Number of Accesses"},
                title="Data Access by Resource Type"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a chord diagram for data flow
            st.subheader("Data Flow Visualization")
            
            st.markdown("""
            The following diagram shows the flow of data access between staff roles and data resources.
            This visualization helps identify common access patterns and potential anomalies.
            
            *Note: This is a simplified representation for demonstration purposes.*
            """)
            
            # Create a placeholder image for the chord diagram
            st.image("https://miro.medium.com/max/720/1*YjFY1pKl5BEjrgkEYuFGAA.png", 
                    caption="Data Flow Visualization (placeholder)")
        else:
            st.info("Failed to load audit logs data.")
    else:
        st.info("No audit logs data available for access pattern analysis.")

if __name__ == "__main__":
    # This will run when the script is executed directly
    pass
