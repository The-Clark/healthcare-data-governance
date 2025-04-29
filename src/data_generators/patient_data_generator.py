"""
Patient Data Generator

This module generates synthetic healthcare data that simulates NHS patient records.
It creates realistic but fake patient information that can be used for testing
the data governance framework without using real patient data.
"""

import os
import json
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import uuid
import random
import traceback

# Initialize faker
fake = Faker('en_GB')  # Using UK locale for realistic NHS data

class NHSPatientDataGenerator:
    """Generates synthetic NHS patient data for testing data governance frameworks."""
    
    def __init__(self, num_patients=1000, output_dir='data'):
        """
        Initialize the patient data generator.
        
        Args:
            num_patients (int): Number of patient records to generate
            output_dir (str): Directory to save the generated data
        """
        self.num_patients = num_patients
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # NHS specific data
        self.nhs_trusts = [
            "London North West University Healthcare NHS Trust",
            "Manchester University NHS Foundation Trust",
            "University Hospitals Birmingham NHS Foundation Trust",
            "Leeds Teaching Hospitals NHS Trust",
            "Oxford University Hospitals NHS Foundation Trust",
            "Newcastle upon Tyne Hospitals NHS Foundation Trust",
            "University College London Hospitals NHS Foundation Trust",
            "Guy's and St Thomas' NHS Foundation Trust",
            "Cambridge University Hospitals NHS Foundation Trust"
        ]
        
        self.departments = [
            "Emergency Care", "Cardiology", "Neurology", "Oncology", 
            "Pediatrics", "Surgery", "Orthopedics", "Obstetrics", 
            "Gynecology", "Psychiatry", "Radiology", "Pathology"
        ]
        
        self.conditions = [
            "Hypertension", "Type 2 Diabetes", "Asthma", "Coronary Artery Disease",
            "COPD", "Arthritis", "Depression", "Anxiety", "Hypothyroidism",
            "Hyperlipidemia", "Obesity", "Chronic Kidney Disease", "None"
        ]
        
        self.medications = [
            "Amlodipine", "Lisinopril", "Metformin", "Atorvastatin", "Albuterol",
            "Levothyroxine", "Omeprazole", "Sertraline", "Paracetamol", 
            "Ibuprofen", "Aspirin", "Gabapentin", "None"
        ]
        
        self.blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    
    def _generate_nhs_number(self):
        """Generate a realistic but fake NHS number."""
        # NHS numbers are 10 digits, with the 10th being a checksum
        # This generates a simplified version that looks realistic
        return f"{random.randint(400, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    
    def _generate_postcode(self):
        """Generate a UK postcode."""
        return fake.postcode()
    
    def _generate_date_of_birth(self):
        """Generate a realistic date of birth."""
        return fake.date_of_birth(minimum_age=0, maximum_age=100).strftime('%Y-%m-%d')
    
    def _generate_nhs_email(self, first_name, last_name, trust):
        """Generate an NHS email address."""
        trust_abbr = ''.join([word[0] for word in trust.split(' ') if word not in ['NHS', 'Foundation', 'Trust', 'University']])
        return f"{first_name.lower()}.{last_name.lower()}@{trust_abbr.lower()}.nhs.uk"
    
    def _generate_phone_number(self):
        """Generate a UK phone number."""
        return fake.phone_number()
    
    def _generate_patient_demographics(self):
        """Generate demographic information for patients."""
        patients = []
        
        for _ in range(self.num_patients):
            gender = random.choice(["Male", "Female"])
            first_name = fake.first_name_male() if gender == "Male" else fake.first_name_female()
            last_name = fake.last_name()
            
            patient = {
                "patient_id": str(uuid.uuid4()),
                "nhs_number": self._generate_nhs_number(),
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": self._generate_date_of_birth(),
                "gender": gender,
                "address": fake.address(),
                "postcode": self._generate_postcode(),
                "phone_number": self._generate_phone_number(),
                "email": fake.email(),
                "blood_type": random.choice(self.blood_types),
                "registered_gp": fake.name() + " MD",
                "emergency_contact": fake.name(),
                "emergency_contact_phone": self._generate_phone_number(),
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            patients.append(patient)
        
        # Convert to DataFrame
        df_patients = pd.DataFrame(patients)
        
        # Save to CSV
        patient_file = os.path.join(self.output_dir, 'patient_demographics.csv')
        df_patients.to_csv(patient_file, index=False)
        print(f"Generated {self.num_patients} patient demographic records: {patient_file}")
        
        return df_patients
    
    def _generate_patient_medical_records(self, patient_df):
        """Generate medical records for patients."""
        medical_records = []
    
        for _, patient in patient_df.iterrows():
            # Generate between 1-5 medical records per patient
            for _ in range(random.randint(1, 5)):
                visit_date = fake.date_between(start_date='-3y', end_date='today')
                primary_diagnosis = random.choice(self.conditions)
            
                record = {
                    "record_id": str(uuid.uuid4()),
                    "patient_id": patient["patient_id"],
                    "nhs_number": patient["nhs_number"],
                    "visit_date": visit_date.strftime('%Y-%m-%d'),
                    "trust_name": random.choice(self.nhs_trusts),
                    "department": random.choice(self.departments),
                    "primary_diagnosis": primary_diagnosis,
                    "secondary_diagnosis": random.choice(self.conditions) if random.random() > 0.5 else None,
                    "notes": self._generate_medical_note(primary_diagnosis),  # Use the new method
                    "attending_physician": fake.name() + " MD",
                    "medication_prescribed": random.choice(self.medications),
                    "follow_up_required": random.choice([True, False]),
                    "follow_up_date": (visit_date + timedelta(days=random.randint(14, 90))).strftime('%Y-%m-%d') if random.random() > 0.5 else None,
                    "created_at": visit_date.strftime('%Y-%m-%d %H:%M:%S'),
                    "updated_at": visit_date.strftime('%Y-%m-%d %H:%M:%S')
                }
            
                medical_records.append(record)
    
        # Convert to DataFrame
        df_records = pd.DataFrame(medical_records)
    
        # Save to CSV
        records_file = os.path.join(self.output_dir, 'patient_medical_records.csv')
        df_records.to_csv(records_file, index=False)
        print(f"Generated {len(df_records)} patient medical records: {records_file}")
    
        return df_records
    
    def _generate_medical_note(self, diagnosis):
        """Generate a realistic medical note based on diagnosis."""
        note_templates = [
            "Patient presents with symptoms of {diagnosis}. Physical examination reveals {finding}. Recommended {treatment}.",
            "Follow-up appointment for {diagnosis}. Patient reports {symptom}. Continue with current treatment plan.",
            "Initial consultation for {diagnosis}. Patient history includes {history}. Prescribed {medication}.",
            "Routine check-up. Patient diagnosed with {diagnosis}. Lab work ordered to monitor condition.",
            "Emergency admission for acute {diagnosis}. Patient stabilized and admitted for observation."
        ]
    
        findings = [
            "elevated blood pressure", "normal vital signs", "irregular heartbeat", 
            "wheezing", "tenderness in abdomen", "joint inflammation", 
            "normal range of motion", "limited mobility", "clear lungs"
        ]
    
        treatments = [
            "lifestyle modifications", "medication adjustment", "follow-up in 3 months",
            "physical therapy", "dietary changes", "increased physical activity",
            "stress management techniques", "regular monitoring", "specialist referral"
        ]
    
        symptoms = [
            "improvement", "no change", "worsening symptoms", 
            "side effects from medication", "good response to treatment",
            "occasional pain", "difficulty sleeping", "increased fatigue"
        ]
    
        history = [
            "family history of similar conditions", "no significant prior issues",
            "previous surgery", "allergies to multiple medications",
            "recurrent infections", "smoking history", "recent travel"
        ]
    
        medications = [
            "antibiotics", "pain management", "anti-inflammatory medication",
            "blood pressure medication", "insulin", "antidepressants",
            "cholesterol-lowering medication", "corticosteroids"
        ]
    
        template = random.choice(note_templates)
        return template.format(
            diagnosis=diagnosis,
            finding=random.choice(findings),
            treatment=random.choice(treatments),
            symptom=random.choice(symptoms),
            history=random.choice(history),
            medication=random.choice(medications)
        )

    def _generate_lab_results(self, patient_df, medical_records_df):
        """Generate laboratory test results."""
        lab_results = []
    
        # Print debug information
        print(f"Patient DF columns: {patient_df.columns.tolist()}")
        print(f"Medical records DF columns: {medical_records_df.columns.tolist()}")
    
        try:
            # Join patients with medical records - use safer merging approach with explicit suffixes
            merged_df = pd.merge(
                medical_records_df, 
                patient_df[["patient_id", "nhs_number"]], 
                on="patient_id",
                how="left",  # Ensure we keep all medical records
                suffixes=('_med', '_pat')  # Use clear suffixes
            )
        
            # Verify merge was successful
            print(f"Merged DF columns: {merged_df.columns.tolist()}")
            print(f"Merged DF shape: {merged_df.shape}")
        
            # Either use the existing nhs_number or one of the suffixed versions
            if 'nhs_number' in merged_df.columns:
                nhs_col = 'nhs_number'
            elif 'nhs_number_med' in merged_df.columns:
                nhs_col = 'nhs_number_med'
            elif 'nhs_number_x' in merged_df.columns:
                nhs_col = 'nhs_number_x'
            else:
                # As a last resort, try other potential column names
                potential_columns = [col for col in merged_df.columns if 'nhs_number' in col]
                nhs_col = potential_columns[0] if potential_columns else None
            
            print(f"Using NHS number column: {nhs_col}")
        
            for _, record in merged_df.iterrows():
                # 70% chance of having lab results for a visit
                if random.random() < 0.7:
                    # Generate between 1-3 lab tests per visit
                    for _ in range(random.randint(1, 3)):
                        # Randomly select a test type
                        test_type = random.choice([
                            "Complete Blood Count", "Comprehensive Metabolic Panel", 
                            "Lipid Panel", "Thyroid Panel", "Urinalysis", 
                            "HbA1c", "COVID-19 PCR", "Blood Culture"
                        ])
                    
                        # Generate random result values based on test type
                        if test_type == "Complete Blood Count":
                            result = {
                                "WBC": f"{random.uniform(4.0, 11.0):.1f} x10^9/L",
                                "RBC": f"{random.uniform(4.0, 5.5):.1f} x10^12/L",
                                "Hemoglobin": f"{random.uniform(12.0, 17.0):.1f} g/dL",
                                "Hematocrit": f"{random.uniform(36.0, 50.0):.1f}%",
                                "Platelets": f"{random.uniform(150.0, 450.0):.0f} x10^9/L"
                            }
                        elif test_type == "Lipid Panel":
                            result = {
                                "Total Cholesterol": f"{random.uniform(130.0, 250.0):.0f} mg/dL",
                                "LDL": f"{random.uniform(70.0, 160.0):.0f} mg/dL",
                                "HDL": f"{random.uniform(35.0, 80.0):.0f} mg/dL",
                                "Triglycerides": f"{random.uniform(40.0, 200.0):.0f} mg/dL"
                            }
                        else:
                            # Generic result for other test types
                            result = {
                                "value": f"{random.uniform(0.5, 10.0):.1f}",
                                "unit": random.choice(["mmol/L", "mg/dL", "U/L", "%"]),
                                "reference_range": f"{random.uniform(0.1, 5.0):.1f}-{random.uniform(5.1, 15.0):.1f}"
                            }
                    
                        # Use nhs_col if available, otherwise use a safe fallback
                        nhs_number = record[nhs_col] if nhs_col and nhs_col in record else "Unknown"
                    
                        lab_result = {
                            "result_id": str(uuid.uuid4()),
                            "record_id": record["record_id"],
                            "patient_id": record["patient_id"],
                            "nhs_number": nhs_number,
                            "test_type": test_type,
                            "test_date": record["visit_date"],
                            "result": json.dumps(result),
                            "abnormal_flag": random.choice([True, False]) if random.random() < 0.2 else False,
                            "ordering_physician": record["attending_physician"],
                            "lab_name": f"{random.choice(['Royal', 'University', 'Central', 'General'])} Hospital Laboratory",
                            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                    
                        lab_results.append(lab_result)
    
        except Exception as e:
            print(f"Error generating lab results: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
        # Convert to DataFrame
        df_lab_results = pd.DataFrame(lab_results) if lab_results else pd.DataFrame()
        
        # Save to CSV
        lab_file = os.path.join(self.output_dir, 'patient_lab_results.csv')
        df_lab_results.to_csv(lab_file, index=False)
        print(f"Generated {len(df_lab_results)} patient lab results: {lab_file}")
    
        return df_lab_results
    
    def _generate_patient_consent_records(self, patient_df):
        """Generate GDPR consent records for patients."""
        consent_records = []
        
        consent_types = [
            "Data Processing for Medical Care",
            "Share Data with Other NHS Trusts",
            "Research Use of Anonymized Data",
            "Contact for Clinical Trials",
            "Receive Health Newsletters"
        ]
        
        for _, patient in patient_df.iterrows():
            # Generate consent for each type
            for consent_type in consent_types:
                # 85% chance of consenting to medical care, varied for others
                consent_probability = 0.85 if consent_type == "Data Processing for Medical Care" else random.uniform(0.3, 0.7)
                
                consent_given = random.random() < consent_probability
                recorded_date = fake.date_between(start_date='-1y', end_date='today')
                
                consent = {
                    "consent_id": str(uuid.uuid4()),
                    "patient_id": patient["patient_id"],
                    "nhs_number": patient["nhs_number"],
                    "consent_type": consent_type,
                    "consent_given": consent_given,
                    "recorded_date": recorded_date.strftime('%Y-%m-%d'),
                    "recorded_by": fake.name(),
                    "consent_expiry_date": (recorded_date + timedelta(days=365*2)).strftime('%Y-%m-%d'),
                    "created_at": recorded_date.strftime('%Y-%m-%d %H:%M:%S'),
                    "updated_at": recorded_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                consent_records.append(consent)
        
        # Convert to DataFrame
        df_consent = pd.DataFrame(consent_records)
        
        # Save to CSV
        consent_file = os.path.join(self.output_dir, 'patient_consent_records.csv')
        df_consent.to_csv(consent_file, index=False)
        print(f"Generated {len(df_consent)} patient consent records: {consent_file}")
        
        return df_consent
    
    def _generate_staff_records(self):
        """Generate NHS staff records."""
        staff_records = []
        
        job_titles = [
            "General Practitioner", "Consultant", "Nurse", "Specialist Nurse",
            "Radiographer", "Pharmacist", "Physiotherapist", "Healthcare Assistant",
            "Administrator", "Receptionist", "Hospital Porter", "Laboratory Technician"
        ]
        
        for _ in range(self.num_patients // 10):  # Generate 1/10th as many staff as patients
            trust = random.choice(self.nhs_trusts)
            department = random.choice(self.departments)
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            staff = {
                "staff_id": str(uuid.uuid4()),
                "first_name": first_name,
                "last_name": last_name,
                "job_title": random.choice(job_titles),
                "department": department,
                "trust_name": trust,
                "nhs_email": self._generate_nhs_email(first_name, last_name, trust),
                "phone_extension": f"x{random.randint(1000, 9999)}",
                "start_date": fake.date_between(start_date='-10y', end_date='today').strftime('%Y-%m-%d'),
                "access_level": random.choice(["Basic", "Standard", "Elevated", "Admin"]),
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            staff_records.append(staff)
        
        # Convert to DataFrame
        df_staff = pd.DataFrame(staff_records)
        
        # Save to CSV
        staff_file = os.path.join(self.output_dir, 'nhs_staff_records.csv')
        df_staff.to_csv(staff_file, index=False)
        print(f"Generated {len(df_staff)} NHS staff records: {staff_file}")
        
        return df_staff
    
    def _generate_audit_logs(self, patient_df, staff_df):
        """Generate data access audit logs."""
        audit_logs = []
        
        actions = [
            "View Patient Record", "Update Patient Demographics", "View Test Results",
            "Add Medical Notes", "Prescribe Medication", "Download Medical History",
            "Edit Patient Consent", "Schedule Appointment", "Cancel Appointment"
        ]
        
        # Generate random number of audit logs
        num_logs = self.num_patients * 3  # 3 logs per patient on average
        
        for _ in range(num_logs):
            # Random patient and staff
            patient = patient_df.iloc[random.randint(0, len(patient_df)-1)]
            staff = staff_df.iloc[random.randint(0, len(staff_df)-1)]
            
            action = random.choice(actions)
            access_time = fake.date_time_between(start_date='-30d', end_date='now')
            
            # Determine if this was an unauthorized access (5% chance)
            authorized = random.random() > 0.05
            
            log = {
                "log_id": str(uuid.uuid4()),
                "timestamp": access_time.strftime('%Y-%m-%d %H:%M:%S'),
                "staff_id": staff["staff_id"],
                "staff_name": f"{staff['first_name']} {staff['last_name']}",
                "action": action,
                "resource_type": "Patient Record",
                "resource_id": patient["patient_id"],
                "nhs_number": patient["nhs_number"],
                "ip_address": fake.ipv4(),
                "system": random.choice(["Electronic Health Record", "Patient Portal", "Laboratory System", "Pharmacy System"]),
                "authorized": authorized,
                "access_reason": "Clinical Care" if authorized else "Unauthorized Access",
                "created_at": access_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            audit_logs.append(log)
        
        # Convert to DataFrame
        df_audit = pd.DataFrame(audit_logs)
        
        # Save to CSV
        audit_file = os.path.join(self.output_dir, 'data_access_audit_logs.csv')
        df_audit.to_csv(audit_file, index=False)
        print(f"Generated {len(df_audit)} data access audit logs: {audit_file}")
        
        return df_audit
    
    def generate_all_data(self):
        """Generate all types of NHS patient and related data."""
        print(f"Generating synthetic NHS data for {self.num_patients} patients...")
        
        # Generate data in sequence to maintain referential integrity
        patients = self._generate_patient_demographics()
        medical_records = self._generate_patient_medical_records(patients)
        lab_results = self._generate_lab_results(patients, medical_records)
        consent_records = self._generate_patient_consent_records(patients)
        staff = self._generate_staff_records()
        audit_logs = self._generate_audit_logs(patients, staff)
        
        print("Data generation complete!")
        
        # Return a dictionary of all generated dataframes
        return {
            "patients": patients,
            "medical_records": medical_records,
            "lab_results": lab_results,
            "consent_records": consent_records,
            "staff": staff,
            "audit_logs": audit_logs
        }

if __name__ == "__main__":
    # Generate 100 patients by default for testing
    generator = NHSPatientDataGenerator(num_patients=100)
    data = generator.generate_all_data()
