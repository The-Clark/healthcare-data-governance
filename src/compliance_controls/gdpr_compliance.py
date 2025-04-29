"""
GDPR Compliance Controls for NHS Data

This module implements compliance controls for GDPR requirements in healthcare data,
focusing on consent management, lawful processing, and data subject rights.
"""

import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import uuid
import re

class GDPRComplianceManager:
    """
    Manages GDPR compliance for healthcare data.
    
    This class provides tools for managing consent, implementing GDPR principles,
    and supporting data subject rights.
    """
    
    def __init__(self, data_dir='data', output_dir='data/compliance'):
        """
        Initialize the GDPR Compliance Manager.
        
        Args:
            data_dir (str): Directory containing the data files
            output_dir (str): Directory to save compliance results
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Define GDPR principles
        self.gdpr_principles = {
            "lawfulness": "Processing must be lawful, fair and transparent",
            "purpose_limitation": "Data collected for specified, explicit and legitimate purposes",
            "data_minimisation": "Data adequate, relevant and limited to what is necessary",
            "accuracy": "Data accurate and kept up to date",
            "storage_limitation": "Data kept in identifiable form only as long as necessary",
            "integrity_confidentiality": "Data processed securely with protection against unauthorized processing"
        }
        
        # Define lawful bases for processing
        self.lawful_bases = {
            "consent": "The data subject has given consent",
            "contract": "Processing necessary for contract with data subject",
            "legal_obligation": "Processing necessary for compliance with legal obligation",
            "vital_interests": "Processing necessary to protect vital interests",
            "public_task": "Processing necessary for task in public interest",
            "legitimate_interests": "Processing necessary for legitimate interests"
        }
        
        # Special category processing conditions for healthcare
        self.special_category_conditions = {
            "explicit_consent": "Explicit consent for special category data",
            "employment": "Processing necessary for employment obligations",
            "vital_interests": "Protect vital interests when subject cannot consent",
            "legitimate_activities": "Processing by not-for-profit bodies",
            "public_data": "Data manifestly made public by the data subject",
            "legal_claims": "Processing necessary for legal claims",
            "substantial_public_interest": "Processing necessary for reasons of substantial public interest",
            "health_social_care": "Processing necessary for healthcare or social care",
            "public_health": "Processing necessary for public health",
            "archiving": "Processing necessary for archiving in the public interest"
        }
        
        # Data subject rights
        self.data_subject_rights = {
            "information": "Right to be informed about collection and use of data",
            "access": "Right to access and receive copy of personal data",
            "rectification": "Right to have inaccurate data rectified",
            "erasure": "Right to have personal data erased (right to be forgotten)",
            "restrict_processing": "Right to restrict processing of personal data",
            "data_portability": "Right to obtain and reuse personal data",
            "object": "Right to object to processing",
            "automated_decisions": "Rights related to automated decision making and profiling"
        }
    
    def analyze_consent_records(self, consent_file='patient_consent_records.csv'):
        """
        Analyze consent records for GDPR compliance.
        
        Args:
            consent_file (str): Name of the consent records file
            
        Returns:
            dict: Consent analysis results
        """
        consent_path = os.path.join(self.data_dir, consent_file)
        if not os.path.exists(consent_path):
            return {
                "error": f"Consent file not found: {consent_path}",
                "status": "failed"
            }
        
        try:
            # Load consent records
            df_consent = pd.read_csv(consent_path)
            
            # Basic statistics
            total_records = len(df_consent)
            unique_patients = df_consent['patient_id'].nunique()
            
            # Consent by type
            consent_by_type = df_consent.groupby(['consent_type', 'consent_given']).size().unstack(fill_value=0)
            
            # Calculate consent rates
            consent_rates = {}
            for consent_type in consent_by_type.index:
                consented = consent_by_type.loc[consent_type, True] if True in consent_by_type.columns else 0
                declined = consent_by_type.loc[consent_type, False] if False in consent_by_type.columns else 0
                total = consented + declined
                consent_rates[consent_type] = {
                    "consented": int(consented),
                    "declined": int(declined),
                    "total": int(total),
                    "consent_rate": float(consented / total * 100) if total > 0 else 0.0
                }
            
            # Check for expired consent
            current_date = datetime.now().date()
            df_consent['recorded_date'] = pd.to_datetime(df_consent['recorded_date']).dt.date
            df_consent['consent_expiry_date'] = pd.to_datetime(df_consent['consent_expiry_date']).dt.date
            
            expired_consent = df_consent[df_consent['consent_expiry_date'] < current_date]
            expired_count = len(expired_consent)
            
            # Check for missing consent records
            # This assumes we should have consent records for all patients
            # In a real implementation, we would check against the full patient list
            
            # Create compliance report
            compliance_report = {
                "report_id": str(uuid.uuid4()),
                "report_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "file_analyzed": consent_file,
                "total_consent_records": total_records,
                "unique_patients": unique_patients,
                "consent_by_type": consent_rates,
                "expired_consent_records": expired_count,
                "expired_percentage": (expired_count / total_records * 100) if total_records > 0 else 0.0,
                "compliance_status": "Compliant" if expired_count == 0 else "Non-Compliant",
                "recommendations": []
            }
            
            # Generate recommendations
            if expired_count > 0:
                compliance_report["recommendations"].append(
                    f"Renew {expired_count} expired consent records as soon as possible."
                )
            
            # Check consent rates for all types
            low_consent_types = [
                consent_type for consent_type, stats in consent_rates.items() 
                if stats["consent_rate"] < 50.0
            ]
            
            if low_consent_types:
                compliance_report["recommendations"].append(
                    f"Review consent collection process for: {', '.join(low_consent_types)}."
                )
            
            # Save compliance report
            output_file = os.path.join(self.output_dir, f"consent_compliance_report.json")
            with open(output_file, 'w') as f:
                json.dump(compliance_report, f, indent=2)
            
            print(f"Consent compliance analysis complete. Results saved to {output_file}")
            
            return compliance_report
        
        except Exception as e:
            error_report = {
                "error": str(e),
                "status": "failed"
            }
            
            # Save error report
            output_file = os.path.join(self.output_dir, f"consent_compliance_error.json")
            with open(output_file, 'w') as f:
                json.dump(error_report, f, indent=2)
            
            print(f"Error analyzing consent compliance: {str(e)}. Error saved to {output_file}")
            
            return error_report
    
    def generate_dpia(self, processing_activities=None):
        """
        Generate a simplified Data Protection Impact Assessment (DPIA).
        
        Args:
            processing_activities (list): List of processing activities to assess
            
        Returns:
            dict: DPIA results
        """
        # Default processing activities if none provided
        if processing_activities is None:
            processing_activities = [
                "Collection of patient demographics",
                "Recording of medical history",
                "Processing of lab results",
                "Sharing data with other NHS trusts",
                "Research use of anonymized data"
            ]
        
        dpia = {
            "dpia_id": str(uuid.uuid4()),
            "created_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "system_name": "NHS Healthcare Data Governance Framework",
            "dpo_name": "Data Protection Officer",
            "processing_activities": {},
            "overall_risk_level": "Low",
            "approved": True
        }
        
        # Assess each processing activity
        risk_levels = []
        
        for activity in processing_activities:
            # Perform simplified risk assessment
            # In a real implementation, this would involve a much more detailed assessment
            data_sensitivity = "High" if "medical" in activity.lower() or "lab" in activity.lower() else "Medium"
            data_volume = "High" if "research" in activity.lower() else "Medium"
            data_subjects = "Vulnerable" if "patient" in activity.lower() else "Standard"
            
            # Determine risk level
            if data_sensitivity == "High" and data_subjects == "Vulnerable":
                risk_level = "High"
            elif data_sensitivity == "High" or data_subjects == "Vulnerable":
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            # Define mitigating measures
            mitigating_measures = [
                "Data minimization - only necessary data collected",
                "Access controls based on roles and responsibilities",
                "Data encryption in transit and at rest",
                "Regular data quality checks",
                "Audit trails for all data access",
                "Staff training on data protection"
            ]
            
            # Add specific measures based on activity
            if "sharing" in activity.lower():
                mitigating_measures.append("Data sharing agreements with appropriate safeguards")
            
            if "research" in activity.lower():
                mitigating_measures.append("Anonymization techniques applied before research use")
            
            # Determine residual risk after mitigation
            residual_risk = "Low" if risk_level == "Low" else "Medium"
            
            # Create activity assessment
            dpia["processing_activities"][activity] = {
                "description": activity,
                "legal_basis": "Public task - Healthcare provision" if "research" not in activity.lower() else "Consent",
                "data_types": "Patient identifiable data, medical records" if "medical" in activity.lower() else "Patient demographic data",
                "data_sensitivity": data_sensitivity,
                "data_volume": data_volume,
                "data_subjects": data_subjects,
                "initial_risk_level": risk_level,
                "mitigating_measures": mitigating_measures,
                "residual_risk": residual_risk
            }
            
            risk_levels.append(residual_risk)
        
        # Determine overall risk level
        if "High" in risk_levels:
            dpia["overall_risk_level"] = "High"
        elif "Medium" in risk_levels:
            dpia["overall_risk_level"] = "Medium"
        else:
            dpia["overall_risk_level"] = "Low"
        
        # Generate recommendations
        dpia["recommendations"] = [
            "Implement regular compliance monitoring",
            "Conduct annual DPIA reviews",
            "Maintain comprehensive audit trails",
            "Ensure staff receive regular data protection training"
        ]
        
        if dpia["overall_risk_level"] == "High":
            dpia["recommendations"].append("Consult with ICO before proceeding")
            dpia["approved"] = False
        
        # Save DPIA
        output_file = os.path.join(self.output_dir, f"data_protection_impact_assessment.json")
        with open(output_file, 'w') as f:
            json.dump(dpia, f, indent=2)
        
        print(f"DPIA generation complete. Results saved to {output_file}")
        
        return dpia
    
    def generate_privacy_notice(self):
        """
        Generate a template privacy notice for NHS data processing.
        
        Returns:
            dict: Privacy notice template
        """
        privacy_notice = {
            "notice_id": str(uuid.uuid4()),
            "created_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "version": "1.0",
            "organization": "NHS Healthcare Provider",
            "sections": {
                "introduction": {
                    "title": "Introduction",
                    "content": """
                    This Privacy Notice explains how we use your personal information, how it is collected, 
                    how it is held, and how it is processed. It also explains your rights under the law relating 
                    to your personal information. This Privacy Notice is provided in accordance with the UK General 
                    Data Protection Regulation (UK GDPR) and the Data Protection Act 2018.
                    """
                },
                "data_controller": {
                    "title": "Who is the Data Controller?",
                    "content": """
                    The [NHS Organisation Name] is the Data Controller for the personal information you provide.
                    Our Data Protection Officer can be contacted at: [DPO Contact Details].
                    """
                },
                "personal_information": {
                    "title": "What Personal Information Do We Collect?",
                    "content": """
                    We collect and process the following types of personal information:
                    
                    • Personal identifiers (name, NHS number, address, date of birth, etc.)
                    • Contact information (address, email, telephone number)
                    • Medical information (medical history, diagnoses, treatments, medications)
                    • Test results and medical reports
                    • Information about your appointments and visits
                    • Relevant information from other health professionals
                    • Information from your GP
                    • Photographs, video, audio recordings
                    • CCTV footage if you visit our premises
                    """
                },
                "special_categories": {
                    "title": "Special Categories of Personal Information",
                    "content": """
                    We also collect and process special categories of personal information that may include:
                    
                    • Details about your physical and mental health
                    • Genetic data and biometric data where processed to uniquely identify you
                    • Information about your race, ethnicity, sexual orientation, and religion
                    • Information about disabilities or other health conditions
                    """
                },
                "how_we_collect": {
                    "title": "How We Collect Your Personal Information",
                    "content": """
                    We collect personal information about you from the following sources:
                    
                    • Directly from you when you register with us, attend appointments, or contact us
                    • From your GP and other healthcare providers
                    • From third parties who are involved in your care
                    • From monitoring devices and medical equipment
                    """
                },
                "how_we_use": {
                    "title": "How We Use Your Personal Information",
                    "content": """
                    We use your personal information to:
                    
                    • Provide you with healthcare and treatment
                    • Ensure that we can contact you about your appointments
                    • Keep track of your treatment and monitor your health outcomes
                    • Review the care we provide to ensure it is of the highest standard
                    • Investigate complaints, legal claims, or adverse incidents
                    • Ensure our services can meet future needs
                    • Train and educate healthcare professionals
                    • Conduct research and development (with your consent where required)
                    • Prepare statistics on NHS performance
                    • Audit NHS services
                    """
                },
                "legal_basis": {
                    "title": "Legal Basis for Processing",
                    "content": """
                    We process your personal information under the following legal bases:
                    
                    • Article 6(1)(e) - Processing is necessary for the performance of a task carried out in the public interest
                    • Article 9(2)(h) - Processing is necessary for medical diagnosis, the provision of health treatment and management of healthcare systems
                    
                    For some activities, we rely on other legal bases, such as:
                    
                    • Article 6(1)(c) - Processing is necessary for compliance with a legal obligation
                    • Article 6(1)(d) - Processing is necessary to protect vital interests
                    • Article 6(1)(a) - You have given consent
                    
                    For special category data (such as health data), we also rely on:
                    
                    • Article 9(2)(h) - Processing for healthcare purposes
                    • Article 9(2)(i) - Processing for public health
                    • Article 9(2)(j) - Processing for archiving, research and statistics
                    • Article 9(2)(a) - Explicit consent, where required
                    """
                },
                "sharing": {
                    "title": "Sharing Your Personal Information",
                    "content": """
                    We may share your personal information with:
                    
                    • Other NHS organizations involved in your care
                    • Other healthcare providers (GPs, ambulance services, etc.)
                    • Social services and local authorities
                    • Education services
                    • Research organizations (with appropriate safeguards)
                    • Regulatory bodies such as the Care Quality Commission
                    
                    We will not share your information for marketing, insurance, or commercial purposes without your explicit consent.
                    """
                },
                "retention": {
                    "title": "How Long We Keep Your Personal Information",
                    "content": """
                    We keep your personal information in accordance with the NHS Records Management Code of Practice, which sets out how long we should keep different types of information.
                    
                    Generally, health records are kept for:
                    
                    • Adult health records: 8 years after last treatment
                    • Children's health records: Until the child is 25 (or 26 if they were 17 at conclusion of treatment)
                    • Maternity records: 25 years after the birth
                    • Mental health records: 20 years after no further treatment
                    """
                },
                "your_rights": {
                    "title": "Your Rights",
                    "content": """
                    Under data protection law, you have rights including:
                    
                    • Your right of access - You have the right to ask us for copies of your personal information.
                    • Your right to rectification - You have the right to ask us to rectify information you think is inaccurate or incomplete.
                    • Your right to erasure - You have the right to ask us to erase your personal information in certain circumstances.
                    • Your right to restriction of processing - You have the right to ask us to restrict the processing of your information in certain circumstances.
                    • Your right to object to processing - You have the right to object to the processing of your personal data in certain circumstances.
                    • Your right to data portability - You have the right to ask that we transfer the information you gave us to another organization, or to you, in certain circumstances.
                    
                    You are not required to pay any charge for exercising your rights. If you make a request, we have one month to respond to you.
                    """
                },
                "contact": {
                    "title": "How to Contact Us",
                    "content": """
                    To exercise any of your rights or if you have any questions about this Privacy Notice, please contact:
                    
                    [Data Protection Officer Contact Details]
                    
                    If you are unhappy with how we have used your data, you can complain to the Information Commissioner's Office:
                    
                    Information Commissioner's Office
                    Wycliffe House, Water Lane, Wilmslow, Cheshire, SK9 5AF
                    Helpline number: 0303 123 1113
                    ICO website: https://www.ico.org.uk
                    """
                }
            }
        }
        
        # Save privacy notice
        output_file = os.path.join(self.output_dir, f"privacy_notice_template.json")
        with open(output_file, 'w') as f:
            json.dump(privacy_notice, f, indent=2)
        
        # Also save as Markdown for readability
        markdown_content = f"# Privacy Notice - {privacy_notice['organization']}\n\n"
        markdown_content += f"Version: {privacy_notice['version']} | Created: {privacy_notice['created_date']}\n\n"
        
        for section_key, section in privacy_notice["sections"].items():
            markdown_content += f"## {section['title']}\n\n"
            markdown_content += section['content'].strip() + "\n\n"
        
        markdown_file = os.path.join(self.output_dir, f"privacy_notice_template.md")
        with open(markdown_file, 'w') as f:
            f.write(markdown_content)
        
        print(f"Privacy notice generation complete. Results saved to {output_file} and {markdown_file}")
        
        return privacy_notice
    
    def analyze_data_access_compliance(self, audit_file='data_access_audit_logs.csv'):
        """
        Analyze data access logs for compliance with GDPR principles.
        
        Args:
            audit_file (str): Name of the audit logs file
            
        Returns:
            dict: Compliance analysis results
        """
        audit_path = os.path.join(self.data_dir, audit_file)
        if not os.path.exists(audit_path):
            return {
                "error": f"Audit file not found: {audit_path}",
                "status": "failed"
            }
        
        try:
            # Load audit logs
            df_audit = pd.read_csv(audit_path)
            
            # Basic statistics
            total_accesses = len(df_audit)
            
            # Convert timestamp to datetime
            df_audit['timestamp'] = pd.to_datetime(df_audit['timestamp'])
            
            # Count authorized vs unauthorized access
            auth_counts = df_audit['authorized'].value_counts()
            authorized_count = int(auth_counts.get(True, 0))
            unauthorized_count = int(auth_counts.get(False, 0))
            
            # Calculate unauthorized access rate
            unauthorized_rate = (unauthorized_count / total_accesses) * 100 if total_accesses > 0 else 0
            
            # Get unauthorized access details
            unauthorized_details = []
            if unauthorized_count > 0:
                unauth_df = df_audit[df_audit['authorized'] == False]
                
                # Group by staff and count
                staff_unauth = unauth_df.groupby('staff_name').size().reset_index(name='count')
                staff_unauth = staff_unauth.sort_values('count', ascending=False)
                
                # Get top 10 staff with unauthorized access
                for _, row in staff_unauth.head(10).iterrows():
                    unauthorized_details.append({
                        "staff_name": row['staff_name'],
                        "unauthorized_count": int(row['count'])
                    })
            
            # Analyze access by time of day
            df_audit['hour'] = df_audit['timestamp'].dt.hour
            access_by_hour = df_audit.groupby('hour').size().reset_index(name='count')
            
            # Check for unusual access patterns (very late hours)
            late_hours = [22, 23, 0, 1, 2, 3, 4]
            late_hour_access = df_audit[df_audit['hour'].isin(late_hours)]
            late_hour_count = len(late_hour_access)
            
            # Check access by action type
            access_by_action = df_audit.groupby('action').size().reset_index(name='count')
            access_by_action = access_by_action.sort_values('count', ascending=False)
            
            # Create compliance report
            compliance_report = {
                "report_id": str(uuid.uuid4()),
                "report_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "file_analyzed": audit_file,
                "total_access_records": total_accesses,
                "authorized_count": authorized_count,
                "unauthorized_count": unauthorized_count,
                "unauthorized_rate": float(unauthorized_rate),
                "unauthorized_details": unauthorized_details,
                "late_hour_access_count": int(late_hour_count),
                "late_hour_access_rate": float((late_hour_count / total_accesses) * 100) if total_accesses > 0 else 0,
                "access_by_action": [
                    {"action": row['action'], "count": int(row['count'])}
                    for _, row in access_by_action.head(10).iterrows()
                ],
                "access_by_hour": [
                    {"hour": int(row['hour']), "count": int(row['count'])}
                    for _, row in access_by_hour.iterrows()
                ],
                "compliance_status": "Non-Compliant" if unauthorized_count > 0 else "Compliant",
                "recommendations": []
            }
            
            # Generate recommendations
            if unauthorized_count > 0:
                compliance_report["recommendations"].append(
                    f"Investigate {unauthorized_count} unauthorized access attempts and implement stricter access controls."
                )
            
            if late_hour_count > 0:
                compliance_report["recommendations"].append(
                    f"Review {late_hour_count} access attempts during late hours (10 PM - 5 AM) to ensure they are legitimate."
                )
            
            # Save compliance report
            output_file = os.path.join(self.output_dir, f"access_compliance_report.json")
            with open(output_file, 'w') as f:
                json.dump(compliance_report, f, indent=2)
            
            print(f"Access compliance analysis complete. Results saved to {output_file}")
            
            return compliance_report
        
        except Exception as e:
            error_report = {
                "error": str(e),
                "status": "failed"
            }
            
            # Save error report
            output_file = os.path.join(self.output_dir, f"access_compliance_error.json")
            with open(output_file, 'w') as f:
                json.dump(error_report, f, indent=2)
            
            print(f"Error analyzing access compliance: {str(e)}. Error saved to {output_file}")
            
            return error_report
    
    def run_compliance_assessment(self):
        """
        Run a comprehensive compliance assessment.
        
        Returns:
            dict: Overall compliance assessment
        """
        print("Running comprehensive GDPR compliance assessment...")
        
        # Run individual assessments
        consent_report = self.analyze_consent_records()
        dpia = self.generate_dpia()
        access_report = self.analyze_data_access_compliance()
        self.generate_privacy_notice()
        
        # Create overall assessment
        assessment = {
            "assessment_id": str(uuid.uuid4()),
            "assessment_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "assessment_name": "NHS Data Governance GDPR Compliance Assessment",
            "assessment_version": "1.0",
            "components": {
                "consent_management": {
                    "status": consent_report.get("compliance_status", "Unknown"),
                    "details": "Assessment of consent records and management practices"
                },
                "data_protection_impact": {
                    "status": "Compliant" if dpia.get("approved", False) else "Non-Compliant",
                    "details": "Data Protection Impact Assessment for processing activities"
                },
                "access_controls": {
                    "status": access_report.get("compliance_status", "Unknown"),
                    "details": "Assessment of data access patterns and security"
                },
                "privacy_information": {
                    "status": "Compliant",
                    "details": "Privacy notice creation and information management"
                }
            },
            "overall_status": "Compliant",
            "key_findings": [],
            "recommendations": []
        }
        
        # Determine overall status
        component_statuses = [comp["status"] for comp in assessment["components"].values()]
        if "Non-Compliant" in component_statuses:
            assessment["overall_status"] = "Non-Compliant"
        
        # Collect key findings and recommendations
        if "recommendations" in consent_report:
            assessment["recommendations"].extend(consent_report["recommendations"])
        
        if "recommendations" in dpia:
            assessment["recommendations"].extend(dpia["recommendations"])
        
        if "recommendations" in access_report:
            assessment["recommendations"].extend(access_report["recommendations"])
        
        # Add findings based on component statuses
        for component, details in assessment["components"].items():
            if details["status"] == "Non-Compliant":
                assessment["key_findings"].append(f"{component.replace('_', ' ').title()} requires immediate attention")
        
        # Add general recommendations if needed
        if not assessment["recommendations"]:
            assessment["recommendations"].append("Continue regular compliance monitoring")
            assessment["recommendations"].append("Conduct annual GDPR training for all staff")
        
        # Save overall assessment
        output_file = os.path.join(self.output_dir, f"overall_compliance_assessment.json")
        with open(output_file, 'w') as f:
            json.dump(assessment, f, indent=2)
        
        print(f"Comprehensive compliance assessment complete. Results saved to {output_file}")
        
        return assessment

if __name__ == "__main__":
    # Run compliance assessment
    compliance_manager = GDPRComplianceManager()
    overall_assessment = compliance_manager.run_compliance_assessment()
