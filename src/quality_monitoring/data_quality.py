"""
NHS Data Quality Monitoring

This module implements automated data quality monitoring for healthcare data,
providing validation, profiling, and quality scoring according to NHS standards.
"""

import os
import pandas as pd
import numpy as np
import json
import re
from datetime import datetime
import uuid

class NHSDataQualityMonitor:
    """
    Monitors and evaluates data quality for healthcare datasets according to NHS standards.
    
    This class provides tools for data profiling, validation, and quality scoring
    to ensure healthcare data meets necessary quality standards.
    """
    
    def __init__(self, data_dir='data', output_dir='data/quality'):
        """
        Initialize the NHS Data Quality Monitor.
        
        Args:
            data_dir (str): Directory containing the data files to monitor
            output_dir (str): Directory to save quality monitoring results
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Define quality dimensions based on NHS Data Quality Maturity Index
        self.quality_dimensions = {
            "completeness": "The degree to which required data is present",
            "validity": "The degree to which data conforms to defined formats and ranges",
            "consistency": "The degree to which data is consistent across datasets",
            "timeliness": "The degree to which data is up-to-date",
            "uniqueness": "The degree to which data is free from duplication",
            "accuracy": "The degree to which data correctly describes the real-world object"
        }
        
        # Define NHS data type patterns
        self.nhs_patterns = {
            "nhs_number": r'^\d{3}[-\s]?\d{3}[-\s]?\d{4}$',
            "uk_postcode": r'^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$',
            "uk_phone": r'^(?:(?:\+|00)44|0)(?:\d\s?){9,10}$',
            "date_of_birth": r'^\d{4}-\d{2}-\d{2}$',
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        }
        
    def _load_dataset(self, file_name):
        """
        Load a dataset for validation.
        
        Args:
            file_name (str): Name of the CSV file to load
            
        Returns:
            pd.DataFrame: Pandas DataFrame
        """
        file_path = os.path.join(self.data_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load the dataset
        df = pd.read_csv(file_path)
        return df
    
    def _get_dataset_rules(self, file_name, df):
        """
        Get appropriate validation rules for a specific dataset.
        
        Args:
            file_name (str): Name of the dataset file
            df (pd.DataFrame): The dataset
            
        Returns:
            dict: Dictionary of validation rules by column
        """
        # Basic rules that apply to all datasets
        common_rules = {
            "created_at": {
                "not_null": True,
                "match_strftime_format": "%Y-%m-%d %H:%M:%S"
            },
            "updated_at": {
                "match_strftime_format": "%Y-%m-%d %H:%M:%S"
            }
        }
        
        # Dataset-specific rules
        dataset_rules = {}
        
        # Patient demographics
        if "patient_demographics" in file_name:
            dataset_rules = {
                "patient_id": {
                    "not_null": True,
                    "unique": True
                },
                "nhs_number": {
                    "not_null": True,
                    "unique": True,
                    "match_regex": self.nhs_patterns["nhs_number"]
                },
                "first_name": {
                    "not_null": True,
                    "min_length": 1
                },
                "last_name": {
                    "not_null": True,
                    "min_length": 1
                },
                "date_of_birth": {
                    "not_null": True,
                    "match_regex": self.nhs_patterns["date_of_birth"]
                },
                "gender": {
                    "not_null": True,
                    "in_list": ["Male", "Female", "Other", "Unknown"]
                },
                "postcode": {
                    "not_null": True,
                    "match_regex": self.nhs_patterns["uk_postcode"]
                },
                "phone_number": {
                    "not_null": True
                },
                "email": {
                    "match_regex": self.nhs_patterns["email"]
                },
                "blood_type": {
                    "in_list": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", None]
                }
            }
        
        # Medical records
        elif "medical_records" in file_name:
            dataset_rules = {
                "record_id": {
                    "not_null": True,
                    "unique": True
                },
                "patient_id": {
                    "not_null": True
                },
                "nhs_number": {
                    "not_null": True,
                    "match_regex": self.nhs_patterns["nhs_number"]
                },
                "visit_date": {
                    "not_null": True,
                    "match_strftime_format": "%Y-%m-%d"
                },
                "trust_name": {
                    "not_null": True
                },
                "department": {
                    "not_null": True
                },
                "primary_diagnosis": {
                    "not_null": True
                },
                "attending_physician": {
                    "not_null": True
                }
            }
        
        # Lab results
        elif "lab_results" in file_name:
            dataset_rules = {
                "result_id": {
                    "not_null": True,
                    "unique": True
                },
                "record_id": {
                    "not_null": True
                },
                "patient_id": {
                    "not_null": True
                },
                "nhs_number": {
                    "not_null": True,
                    "match_regex": self.nhs_patterns["nhs_number"]
                },
                "test_type": {
                    "not_null": True
                },
                "test_date": {
                    "not_null": True,
                    "match_strftime_format": "%Y-%m-%d"
                },
                "result": {
                    "not_null": True
                }
            }
        
        # Consent records
        elif "consent" in file_name:
            dataset_rules = {
                "consent_id": {
                    "not_null": True,
                    "unique": True
                },
                "patient_id": {
                    "not_null": True
                },
                "nhs_number": {
                    "not_null": True,
                    "match_regex": self.nhs_patterns["nhs_number"]
                },
                "consent_type": {
                    "not_null": True
                },
                "consent_given": {
                    "not_null": True
                },
                "recorded_date": {
                    "not_null": True,
                    "match_strftime_format": "%Y-%m-%d"
                }
            }
        
        # Staff records
        elif "staff" in file_name:
            dataset_rules = {
                "staff_id": {
                    "not_null": True,
                    "unique": True
                },
                "first_name": {
                    "not_null": True
                },
                "last_name": {
                    "not_null": True
                },
                "job_title": {
                    "not_null": True
                },
                "department": {
                    "not_null": True
                },
                "trust_name": {
                    "not_null": True
                },
                "nhs_email": {
                    "not_null": True,
                    "match_regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.nhs\.uk$",
                    "unique": True
                }
            }
        
        # Audit logs
        elif "audit" in file_name:
            dataset_rules = {
                "log_id": {
                    "not_null": True,
                    "unique": True
                },
                "timestamp": {
                    "not_null": True,
                    "match_strftime_format": "%Y-%m-%d %H:%M:%S"
                },
                "staff_id": {
                    "not_null": True
                },
                "action": {
                    "not_null": True
                },
                "resource_type": {
                    "not_null": True
                },
                "resource_id": {
                    "not_null": True
                },
                "authorized": {
                    "not_null": True
                }
            }
        
        # Merge common rules with dataset-specific rules
        rules = {**common_rules}
        
        # Only add dataset rules for columns that actually exist
        for column, column_rules in dataset_rules.items():
            if column in df.columns:
                rules[column] = column_rules
        
        return rules
    
    def _validate_column(self, df, column, rules):
        """
        Validate a column against its rules.
        
        Args:
            df (pd.DataFrame): DataFrame containing the column
            column (str): Column name to validate
            rules (dict): Validation rules for the column
            
        Returns:
            dict: Validation results
        """
        validation_results = {
            "column": column,
            "rules_tested": [],
            "rules_passed": [],
            "rules_failed": [],
            "pass_percentage": 0.0
        }
        
        for rule, value in rules.items():
            validation_results["rules_tested"].append(rule)
            
            try:
                if rule == "not_null":
                    # Check for null values
                    nulls = df[column].isnull().sum()
                    passed = nulls == 0
                    if passed:
                        validation_results["rules_passed"].append(rule)
                    else:
                        validation_results["rules_failed"].append({
                            "rule": rule,
                            "unexpected_count": int(nulls),
                            "unexpected_percent": float(nulls / len(df) * 100)
                        })
                        
                elif rule == "unique":
                    # Check for duplicates
                    duplicates = len(df) - df[column].nunique()
                    passed = duplicates == 0
                    if passed:
                        validation_results["rules_passed"].append(rule)
                    else:
                        validation_results["rules_failed"].append({
                            "rule": rule,
                            "unexpected_count": int(duplicates),
                            "unexpected_percent": float(duplicates / len(df) * 100)
                        })
                        
                elif rule == "min_length":
                    # Check minimum length for string columns
                    # Convert to string and handle null values
                    str_series = df[column].astype(str)
                    str_series = str_series.replace('nan', '')
                    too_short = (str_series.str.len() < value).sum()
                    passed = too_short == 0
                    if passed:
                        validation_results["rules_passed"].append(rule)
                    else:
                        validation_results["rules_failed"].append({
                            "rule": rule,
                            "unexpected_count": int(too_short),
                            "unexpected_percent": float(too_short / len(df) * 100)
                        })
                        
                elif rule == "max_length":
                    # Check maximum length for string columns
                    str_series = df[column].astype(str)
                    str_series = str_series.replace('nan', '')
                    too_long = (str_series.str.len() > value).sum()
                    passed = too_long == 0
                    if passed:
                        validation_results["rules_passed"].append(rule)
                    else:
                        validation_results["rules_failed"].append({
                            "rule": rule,
                            "unexpected_count": int(too_long),
                            "unexpected_percent": float(too_long / len(df) * 100)
                        })
                        
                elif rule == "in_list":
                    # Check if values are in a specified list
                    invalid_values = df[~df[column].isin(value) & ~df[column].isnull()]
                    passed = len(invalid_values) == 0
                    if passed:
                        validation_results["rules_passed"].append(rule)
                    else:
                        validation_results["rules_failed"].append({
                            "rule": rule,
                            "unexpected_count": len(invalid_values),
                            "unexpected_percent": float(len(invalid_values) / len(df) * 100)
                        })
                        
                elif rule == "match_regex":
                    # Check if values match a regex pattern
                    # Convert to string and exclude nulls
                    str_series = df[column].astype(str)
                    non_null = df[~df[column].isnull()]
                    invalid_pattern = non_null[~str_series[non_null.index].str.match(value)]
                    passed = len(invalid_pattern) == 0
                    if passed:
                        validation_results["rules_passed"].append(rule)
                    else:
                        validation_results["rules_failed"].append({
                            "rule": rule,
                            "unexpected_count": len(invalid_pattern),
                            "unexpected_percent": float(len(invalid_pattern) / len(non_null) * 100)
                        })
                        
                elif rule == "match_strftime_format":
                    # Check if dates match a specified format
                    # Convert to string and exclude nulls
                    str_series = df[column].astype(str)
                    non_null = df[~df[column].isnull()]
                    
                    # Try to parse dates
                    invalid_dates = []
                    for idx, date_str in str_series[non_null.index].items():
                        try:
                            datetime.strptime(date_str, value)
                        except ValueError:
                            invalid_dates.append(idx)
                    
                    passed = len(invalid_dates) == 0
                    if passed:
                        validation_results["rules_passed"].append(rule)
                    else:
                        validation_results["rules_failed"].append({
                            "rule": rule,
                            "unexpected_count": len(invalid_dates),
                            "unexpected_percent": float(len(invalid_dates) / len(non_null) * 100)
                        })
                else:
                    continue
                
            except Exception as e:
                validation_results["rules_failed"].append({
                    "rule": rule,
                    "error": str(e)
                })
        
        # Calculate pass percentage
        if validation_results["rules_tested"]:
            validation_results["pass_percentage"] = (len(validation_results["rules_passed"]) / 
                                                   len(validation_results["rules_tested"])) * 100
        
        return validation_results
    
    def _create_data_profile(self, df, file_name):
        """
        Create a data profile for a dataset.
        
        Args:
            df (pd.DataFrame): Dataset to profile
            file_name (str): Name of the dataset file
            
        Returns:
            dict: Data profile
        """
        profile = {
            "file_name": file_name,
            "record_count": len(df),
            "column_count": len(df.columns),
            "profiled_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "profile_id": str(uuid.uuid4()),
            "columns": {}
        }
        
        for column in df.columns:
            column_profile = {
                "data_type": str(df[column].dtype),
                "count": len(df[column]),
                "null_count": df[column].isnull().sum(),
                "null_percentage": (df[column].isnull().sum() / len(df)) * 100 if len(df) > 0 else 0,
                "unique_count": df[column].nunique(),
                "unique_percentage": (df[column].nunique() / len(df)) * 100 if len(df) > 0 else 0
            }
            
            # Add additional metrics for numeric columns
            if np.issubdtype(df[column].dtype, np.number):
                column_profile.update({
                    "min": float(df[column].min()) if not df[column].isnull().all() else None,
                    "max": float(df[column].max()) if not df[column].isnull().all() else None,
                    "mean": float(df[column].mean()) if not df[column].isnull().all() else None,
                    "median": float(df[column].median()) if not df[column].isnull().all() else None,
                    "std": float(df[column].std()) if not df[column].isnull().all() else None
                })
            
            # Add string length metrics for string columns
            elif df[column].dtype == 'object':
                # Convert to string and calculate lengths
                str_lengths = df[column].astype(str).str.len()
                
                column_profile.update({
                    "min_length": int(str_lengths.min()) if not str_lengths.isnull().all() else None,
                    "max_length": int(str_lengths.max()) if not str_lengths.isnull().all() else None,
                    "mean_length": float(str_lengths.mean()) if not str_lengths.isnull().all() else None
                })
                
                # Get most frequent values (top 5)
                value_counts = df[column].value_counts().head(5).to_dict()
                column_profile["frequent_values"] = {str(k): int(v) for k, v in value_counts.items()}
            
            profile["columns"][column] = column_profile
        
        return profile
    
    def _calculate_quality_score(self, validation_results):
        """
        Calculate an overall quality score for a dataset.
        
        Args:
            validation_results (dict): Validation results for the dataset
            
        Returns:
            dict: Quality score information
        """
        # Initialize scores for each quality dimension
        dimension_scores = {
            "completeness": [],
            "validity": [],
            "uniqueness": [],
            "consistency": []
        }
        
        # Calculate scores for each column
        for column_result in validation_results["column_results"]:
            # Completeness: based on not_null validation
            if "not_null" in column_result["rules_tested"]:
                not_null_passed = "not_null" in column_result["rules_passed"]
                dimension_scores["completeness"].append(100 if not_null_passed else 0)
            
            # Validity: based on format validations (regex, in_list, etc.)
            validity_rules = ["match_regex", "in_list", "match_strftime_format"]
            validity_tested = [rule for rule in validity_rules if rule in column_result["rules_tested"]]
            if validity_tested:
                validity_passed = [rule for rule in validity_tested if rule in column_result["rules_passed"]]
                dimension_scores["validity"].append((len(validity_passed) / len(validity_tested)) * 100)
            
            # Uniqueness: based on unique validation
            if "unique" in column_result["rules_tested"]:
                unique_passed = "unique" in column_result["rules_passed"]
                dimension_scores["uniqueness"].append(100 if unique_passed else 0)
            
            # Consistency: all rules not covered by other dimensions
            all_other_rules = [r for r in column_result["rules_tested"] 
                              if r not in ["not_null", "unique"] + validity_rules]
            if all_other_rules:
                other_passed = [r for r in all_other_rules if r in column_result["rules_passed"]]
                dimension_scores["consistency"].append((len(other_passed) / len(all_other_rules)) * 100)
        
        # Calculate average scores for each dimension
        quality_scores = {}
        for dimension, scores in dimension_scores.items():
            if scores:
                quality_scores[dimension] = sum(scores) / len(scores)
            else:
                quality_scores[dimension] = None
        
        # Calculate overall quality score (weighted average of dimensions)
        weights = {
            "completeness": 0.4,  # Completeness is most important
            "validity": 0.3,
            "uniqueness": 0.15,
            "consistency": 0.15
        }
        
        weighted_sum = 0
        weight_sum = 0
        
        for dimension, score in quality_scores.items():
            if score is not None:
                weighted_sum += score * weights[dimension]
                weight_sum += weights[dimension]
        
        overall_score = weighted_sum / weight_sum if weight_sum > 0 else 0
        
        # Create quality score object
        quality_score = {
            "overall_score": overall_score,
            "dimension_scores": quality_scores,
            "score_interpretation": self._interpret_quality_score(overall_score),
            "weighted_dimensions": weights
        }
        
        return quality_score
    
    def _interpret_quality_score(self, score):
        """
        Interpret a quality score.
        
        Args:
            score (float): Quality score to interpret
            
        Returns:
            str: Interpretation of the score
        """
        if score >= 95:
            return "Excellent - Data meets the highest quality standards"
        elif score >= 85:
            return "Good - Data is reliable with minor quality issues"
        elif score >= 70:
            return "Adequate - Data is usable but has notable quality issues"
        elif score >= 50:
            return "Poor - Data has significant quality issues requiring attention"
        else:
            return "Critical - Data quality is severely compromised"
    
    def validate_dataset(self, file_name):
        """
        Validate a dataset against NHS data quality rules.
        
        Args:
            file_name (str): Name of the CSV file to validate
            
        Returns:
            dict: Validation results
        """
        try:
            # Load the dataset
            df = self._load_dataset(file_name)
            
            # Get validation rules for this dataset
            rules = self._get_dataset_rules(file_name, df)
            
            # Validate each column against its rules
            column_results = []
            for column, column_rules in rules.items():
                if column in df.columns:
                    result = self._validate_column(df, column, column_rules)
                    column_results.append(result)
            
            # Create data profile
            profile = self._create_data_profile(df, file_name)
            
            # Create validation results object
            validation_results = {
                "file_name": file_name,
                "validation_id": str(uuid.uuid4()),
                "validated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "record_count": len(df),
                "column_count": len(df.columns),
                "columns_validated": len(column_results),
                "column_results": column_results,
                "data_profile": profile
            }
            
            # Calculate quality score
            validation_results["quality_score"] = self._calculate_quality_score(validation_results)
            
            # Save validation results
            output_file = os.path.join(self.output_dir, f"{os.path.splitext(file_name)[0]}_quality.json")
            with open(output_file, 'w') as f:
                # Convert NumPy types to native Python types
                serializable_results = self._make_json_serializable(validation_results)
                json.dump(serializable_results, f, indent=2)
            
            print(f"Validation complete for {file_name}. Results saved to {output_file}")
            
            return validation_results
        
        except Exception as e:
            error_result = {
                "file_name": file_name,
                "validation_id": str(uuid.uuid4()),
                "validated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "error": str(e),
                "status": "failed"
            }
            
            # Save error result
            output_file = os.path.join(self.output_dir, f"{os.path.splitext(file_name)[0]}_quality_error.json")
            with open(output_file, 'w') as f:
                # Convert NumPy types to native Python types
                serializable_error = self._make_json_serializable(error_result)
                json.dump(serializable_error, f, indent=2)
            
            print(f"Error validating {file_name}: {str(e)}. Error saved to {output_file}")
            
            return error_result

    def _make_json_serializable(self, obj):
        """
        Convert object to JSON serializable format.
        Handle NumPy data types and other non-serializable objects.
    
        Args:
            obj: Object to convert
        
        Returns:
            JSON serializable object
        """
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(i) for i in obj]
        else:
            return obj
    
    def validate_all_datasets(self):
        """
        Validate all CSV datasets in the data directory.
        
        Returns:
            dict: Validation results for all datasets
        """
        all_results = {}
        
        # Get all CSV files in the data directory
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            print(f"No CSV files found in {self.data_dir}")
            return all_results
        
        print(f"Found {len(csv_files)} CSV files to validate")
        
        # Validate each dataset
        for file_name in csv_files:
            try:
                result = self.validate_dataset(file_name)
                all_results[file_name] = result
            except Exception as e:
                print(f"Error validating {file_name}: {str(e)}")
                all_results[file_name] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        # Create a summary report
        summary = {
            "total_datasets": len(all_results),
            "validation_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "datasets": {}
        }
        
        # Add each dataset's quality score to the summary
        for file_name, result in all_results.items():
            if "quality_score" in result:
                summary["datasets"][file_name] = {
                    "overall_score": result["quality_score"]["overall_score"],
                    "interpretation": result["quality_score"]["score_interpretation"],
                    "dimension_scores": result["quality_score"]["dimension_scores"]
                }
            else:
                summary["datasets"][file_name] = {
                    "error": result.get("error", "Unknown error"),
                    "status": "failed"
                }
        
        # Calculate average quality score across all datasets
        successful_datasets = [d for d in summary["datasets"].values() if "overall_score" in d]
        if successful_datasets:
            summary["average_quality_score"] = sum(d["overall_score"] for d in successful_datasets) / len(successful_datasets)
            summary["overall_interpretation"] = self._interpret_quality_score(summary["average_quality_score"])
        
        # Save summary report
        summary_file = os.path.join(self.output_dir, "quality_summary.json")
        with open(summary_file, 'w') as f:
            # Convert NumPy types to native Python types
            serializable_summary = self._make_json_serializable(summary)
            json.dump(serializable_summary, f, indent=2)
        
        print(f"Validation complete for all datasets. Summary saved to {summary_file}")
        
        return all_results

if __name__ == "__main__":
    # Validate all datasets in the data directory
    monitor = NHSDataQualityMonitor()
    all_validations = monitor.validate_all_datasets()
