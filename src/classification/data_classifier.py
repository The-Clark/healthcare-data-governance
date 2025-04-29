"""
NHS Data Classification System

This module implements an automated classification system for healthcare data,
identifying sensitive information and assigning appropriate classification levels
according to NHS data security standards.
"""

import os
import pandas as pd
import numpy as np
import re
import json
from datetime import datetime
import uuid

class NHSDataClassifier:
    """
    Classifies healthcare data according to NHS information governance standards.
    
    This classifier identifies different types of healthcare data and assigns
    appropriate sensitivity classifications and handling requirements.
    """
    
    def __init__(self, data_dir='data', output_dir='data/classified'):
        """
        Initialize the NHS Data Classifier.
        
        Args:
            data_dir (str): Directory containing the raw data files
            output_dir (str): Directory to save the classification results
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Define classification levels based on NHS Data Security standards
        # Source: https://digital.nhs.uk/data-and-information/looking-after-information/data-security-and-information-governance
        self.classification_levels = {
            "PUBLIC": {
                "description": "Information that can be made public without restrictions",
                "handling": "No special handling required",
                "examples": ["Public health information", "Service locations", "General guidance"],
                "risk_score": 0
            },
            "INTERNAL": {
                "description": "Non-sensitive information for internal use only",
                "handling": "Can be shared with NHS staff but not externally",
                "examples": ["Internal procedures", "Staff directories", "Non-sensitive operational data"],
                "risk_score": 1
            },
            "CONFIDENTIAL": {
                "description": "Sensitive information with limited access",
                "handling": "Access restricted to authorized personnel with legitimate need",
                "examples": ["De-identified patient data", "Staff records", "Business sensitive information"],
                "risk_score": 2
            },
            "RESTRICTED": {
                "description": "Highly sensitive personal or clinical information",
                "handling": "Strict access controls, encryption required, audit logging mandatory",
                "examples": ["Patient identifiable data", "Health records", "Special category data"],
                "risk_score": 3
            }
        }
        
        # Define PII (Personally Identifiable Information) fields
        self.pii_fields = [
            "first_name", "last_name", "date_of_birth", "address", "postcode",
            "phone_number", "email", "nhs_number", "patient_id"
        ]
        
        # Define clinical fields (special category data under GDPR)
        self.clinical_fields = [
            "diagnosis", "condition", "medication", "test_type", "result",
            "blood_type", "primary_diagnosis", "secondary_diagnosis", "notes"
        ]
        
        # Define pattern matchers for sensitive data
        self.patterns = {
            "nhs_number": r'\d{3}[-\s]?\d{3}[-\s]?\d{4}',
            "uk_postcode": r'[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}',
            "uk_phone": r'(?:(?:\+|00)44|0)(?:\d\s?){9,10}',
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "date": r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}'
        }
    
    def _identify_pii_in_text(self, text):
        """
        Identify PII in free text fields using regex patterns.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Dictionary of identified PII types and their counts
        """
        if not isinstance(text, str):
            return {}
        
        found_pii = {}
        
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                found_pii[pii_type] = len(matches)
        
        return found_pii
    
    def _classify_column(self, column_name, sample_values):
        """
        Classify a data column based on its name and sample values.
        
        Args:
            column_name (str): Name of the column
            sample_values (list): Sample values from the column
            
        Returns:
            dict: Classification information
        """
        # Check if column name is in PII fields
        is_pii = any(pii_field in column_name.lower() for pii_field in self.pii_fields)
        
        # Check if column name is in clinical fields
        is_clinical = any(clinical_field in column_name.lower() for clinical_field in self.clinical_fields)
        
        # Check sample values for PII patterns
        contains_pii = False
        pii_types = set()
        
        for value in sample_values:
            if isinstance(value, str):
                found_pii = self._identify_pii_in_text(value)
                if found_pii:
                    contains_pii = True
                    pii_types.update(found_pii.keys())
        
        # Determine classification level
        if is_clinical or (is_pii and contains_pii):
            classification = "RESTRICTED"
        elif is_pii or contains_pii:
            classification = "CONFIDENTIAL"
        elif column_name.lower() in ["created_at", "updated_at", "staff_id", "department", "trust_name"]:
            classification = "INTERNAL"
        else:
            classification = "PUBLIC"
        
        return {
            "column_name": column_name,
            "is_pii": is_pii,
            "is_clinical": is_clinical,
            "contains_pii": contains_pii,
            "pii_types": list(pii_types),
            "classification": classification,
            "risk_score": self.classification_levels[classification]["risk_score"],
            "handling_requirements": self.classification_levels[classification]["handling"]
        }
    
    def classify_dataset(self, file_name):
        """
        Classify an entire dataset based on its columns and content.
        
        Args:
            file_name (str): Name of the CSV file to classify
            
        Returns:
            dict: Classification results
        """
        file_path = os.path.join(self.data_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load the dataset
        df = pd.read_csv(file_path)
        
        # Overall dataset classification info
        dataset_info = {
            "file_name": file_name,
            "record_count": len(df),
            "column_count": len(df.columns),
            "classified_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "classification_id": str(uuid.uuid4()),
            "columns": []
        }
        
        # Classify each column
        highest_risk_score = 0
        for column in df.columns:
            # Get sample values (up to 100)
            sample_values = df[column].dropna().sample(min(100, len(df))).tolist()
            
            # Classify the column
            column_classification = self._classify_column(column, sample_values)
            dataset_info["columns"].append(column_classification)
            
            # Track highest risk score
            if column_classification["risk_score"] > highest_risk_score:
                highest_risk_score = column_classification["risk_score"]
        
        # Overall dataset classification is based on highest risk column
        for classification, details in self.classification_levels.items():
            if details["risk_score"] == highest_risk_score:
                dataset_info["overall_classification"] = classification
                dataset_info["overall_risk_score"] = highest_risk_score
                dataset_info["handling_requirements"] = details["handling"]
                break
        
        # Count columns by classification
        classification_counts = {}
        for column in dataset_info["columns"]:
            classification = column["classification"]
            if classification in classification_counts:
                classification_counts[classification] += 1
            else:
                classification_counts[classification] = 1
        
        dataset_info["classification_counts"] = classification_counts
        
        # Calculate PII density (percentage of columns with PII)
        pii_columns = sum(1 for column in dataset_info["columns"] if column["is_pii"] or column["contains_pii"])
        dataset_info["pii_density"] = (pii_columns / len(df.columns)) * 100
        
        # Save classification results
        output_file = os.path.join(self.output_dir, f"{os.path.splitext(file_name)[0]}_classification.json")
        with open(output_file, 'w') as f:
            json.dump(dataset_info, f, indent=2)
        
        print(f"Classification complete for {file_name}. Results saved to {output_file}")
        
        return dataset_info
    
    def classify_all_datasets(self):
        """
        Classify all CSV datasets in the data directory.
        
        Returns:
            dict: Classification results for all datasets
        """
        all_results = {}
        
        # Get all CSV files in the data directory
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            print(f"No CSV files found in {self.data_dir}")
            return all_results
        
        print(f"Found {len(csv_files)} CSV files to classify")
        
        # Classify each dataset
        for file_name in csv_files:
            try:
                result = self.classify_dataset(file_name)
                all_results[file_name] = result
            except Exception as e:
                print(f"Error classifying {file_name}: {str(e)}")
        
        # Create a summary report
        summary = {
            "total_datasets": len(all_results),
            "classification_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "classification_summary": {}
        }
        
        # Summarize classifications across all datasets
        for classification in self.classification_levels.keys():
            summary["classification_summary"][classification] = sum(
                1 for result in all_results.values() 
                if result.get("overall_classification") == classification
            )
        
        # Calculate overall PII density
        if all_results:
            summary["average_pii_density"] = sum(
                result.get("pii_density", 0) for result in all_results.values()
            ) / len(all_results)
        
        # Save summary report
        summary_file = os.path.join(self.output_dir, "classification_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Classification complete for all datasets. Summary saved to {summary_file}")
        
        return all_results

if __name__ == "__main__":
    # Classify all datasets in the data directory
    classifier = NHSDataClassifier()
    all_classifications = classifier.classify_all_datasets()
