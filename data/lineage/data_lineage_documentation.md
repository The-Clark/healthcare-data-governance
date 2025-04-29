# NHS Data Governance - Data Lineage Documentation

Version: 1.0 | Created: 2025-04-29 01:13:55

## Datasets

- patient_demographics
- patient_medical_records
- patient_lab_results
- patient_consent_records
- nhs_staff_records
- data_access_audit_logs

## Dataset Relationships

| Source Dataset | Relationship | Target Dataset | Joining Fields |
|---------------|-------------|---------------|---------------|
| patient_demographics | primary | patient_medical_records | patient_id, nhs_number |
| patient_demographics | primary | patient_lab_results | patient_id, nhs_number |
| patient_demographics | primary | patient_consent_records | patient_id, nhs_number |
| patient_medical_records | primary | patient_lab_results | record_id |
| nhs_staff_records | referenced_by | data_access_audit_logs | staff_id |
| nhs_staff_records | referenced_by | patient_demographics | last_name, first_name |
| nhs_staff_records | referenced_by | patient_medical_records | trust_name |
| patient_consent_records | primary | patient_demographics | nhs_number, patient_id |
| data_access_audit_logs | primary | nhs_staff_records | staff_id |
| data_access_audit_logs | referenced_by | patient_demographics | nhs_number |
| patient_demographics | primary | nhs_staff_records | last_name, first_name |
| patient_demographics | primary | data_access_audit_logs | nhs_number |
| patient_medical_records | primary | nhs_staff_records | trust_name |
| patient_medical_records | primary | patient_demographics | nhs_number, patient_id |
| patient_lab_results | referenced_by | patient_demographics | nhs_number, patient_id |
| patient_lab_results | referenced_by | patient_medical_records | record_id |

## Data Lineage Diagram

```mermaid
graph TD
    N0[patient_demographics]
    N1[patient_medical_records]
    N2[patient_lab_results]
    N3[patient_consent_records]
    N4[nhs_staff_records]
    N5[data_access_audit_logs]
    N0 ==>|patient_id, nhs_number| N1
    N0 ==>|patient_id, nhs_number| N2
    N0 ==>|patient_id, nhs_number| N3
    N0 ==>|last_name, first_name| N4
    N0 ==>|nhs_number| N5
    N1 ==>|record_id| N2
    N1 ==>|trust_name| N4
    N1 ==>|nhs_number, patient_id| N0
    N2 -.->-|nhs_number, patient_id| N0
    N2 -.->-|record_id| N1
    N3 ==>|nhs_number, patient_id| N0
    N4 -.->-|staff_id| N5
    N4 -.->-|last_name, first_name| N0
    N4 -.->-|trust_name| N1
    N5 ==>|staff_id| N4
    N5 -.->-|nhs_number| N0

```

## Data Flow Summary

Total access events: 300

### Resource Access Distribution

| Resource Type | Access Count | Percentage |
|--------------|-------------|------------|
| Patient Record | 300 | 100.0% |

## Impact Summary

### patient_demographics

- Downstream dependencies: 5
- Upstream dependencies: 5
- High impact dependencies: 2
- Medium impact dependencies: 2
- Low impact dependencies: 1

### patient_medical_records

- Downstream dependencies: 5
- Upstream dependencies: 5
- High impact dependencies: 1
- Medium impact dependencies: 1
- Low impact dependencies: 3

### patient_lab_results

- Downstream dependencies: 5
- Upstream dependencies: 5
- High impact dependencies: 1
- Medium impact dependencies: 2
- Low impact dependencies: 2

### patient_consent_records

- Downstream dependencies: 5
- Upstream dependencies: 5
- High impact dependencies: 1
- Medium impact dependencies: 1
- Low impact dependencies: 3

### nhs_staff_records

- Downstream dependencies: 5
- Upstream dependencies: 5
- High impact dependencies: 1
- Medium impact dependencies: 1
- Low impact dependencies: 3

### data_access_audit_logs

- Downstream dependencies: 5
- Upstream dependencies: 5
- High impact dependencies: 1
- Medium impact dependencies: 1
- Low impact dependencies: 3

