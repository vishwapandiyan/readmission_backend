"""
HL7 v2 ADT (Admission, Discharge, Transfer) Message Processing Service
Supports ADT^A01, ADT^A02, ADT^A03, and ADT^A08 messages.
"""
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime
import re
import logging
from app.models.schemas import PatientFeatures
from app.models.ehr_models import HL7ParsedData
from app.core.config import settings

logger = logging.getLogger(__name__)


# LOINC Code Mapping to Clinical Features
LOINC_MAP = {
    "718-7": "hemoglobin",        # Hemoglobin [Mass/volume] in Blood
    "20509-6": "hemoglobin",      # Hemoglobin [Mass/volume] in Blood by calculation
    "HGB": "hemoglobin",
    "2160-0": "creatinine",       # Creatinine [Mass/volume] in Serum or Plasma
    "38483-4": "creatinine",      # Creatinine [Mass/volume] in Blood
    "CREAT": "creatinine",
    "2345-7": "glucose",          # Glucose [Mass/volume] in Serum or Plasma
    "2339-0": "glucose",          # Glucose [Mass/volume] in Blood
    "GLU": "glucose",
    "4548-4": "hba1c",            # Hemoglobin A1c/Hemoglobin.total in Blood
    "17856-6": "hba1c",           # Hemoglobin A1c/Hemoglobin.total in Blood by HPLC
    "A1C": "hba1c",
    "HBA1C": "hba1c",
    "6690-2": "wbc_count",        # Leukocytes [#/volume] in Blood by Automated count
    "26464-8": "wbc_count",       # Leukocytes [#/volume] in Blood
    "WBC": "wbc_count",
    "1975-2": "total_bilirubin",  # Bilirubin.total [Mass/volume] in Serum or Plasma
    "BILI": "total_bilirubin",
    "39156-5": "bmi",             # Body mass index (BMI) [Ratio]
    "BMI": "bmi",
}

# ICD-10 Code prefixes mapping to chronic condition flags
ICD10_MAP = {
    "E10": "diabetes_flag",
    "E11": "diabetes_flag",
    "E13": "diabetes_flag",
    "250": "diabetes_flag",
    "I50": "heart_failure_flag",
    "428": "heart_failure_flag",
    "J44": "copd_flag",
    "496": "copd_flag",
    "N18": "ckd_flag",
    "585": "ckd_flag",
    "C": "cancer_flag",           # C00-C97 malignant neoplasms
    "140": "cancer_flag",
    "208": "cancer_flag",
    "F01": "dementia_flag",
    "F03": "dementia_flag",
    "G30": "dementia_flag",       # Alzheimer's disease
    "290": "dementia_flag",
}


class HL7v2Service:
    """Service to parse, validate, and process HL7 v2 ADT messages"""

    @classmethod
    def parse_message(cls, raw_message: str) -> Tuple[HL7ParsedData, PatientFeatures, str]:
        """
        Parse raw HL7 v2 message text and extract clinical features.
        Returns: (HL7ParsedData, PatientFeatures, ACK string)
        """
        # Normalize segment line breaks
        lines = [line.strip() for line in re.split(r'[\r\n]+', raw_message) if line.strip()]
        
        segments: Dict[str, List[List[str]]] = {}
        for line in lines:
            parts = line.split("|")
            seg_type = parts[0]
            if seg_type not in segments:
                segments[seg_type] = []
            segments[seg_type].append(parts)

        # 1. Parse MSH (Message Header)
        msh = segments.get("MSH", [[]])[0]
        sending_app = msh[2] if len(msh) > 2 else "UNKNOWN_EHR"
        sending_facility = msh[3] if len(msh) > 3 else "UNKNOWN_FACILITY"
        message_type = msh[8] if len(msh) > 8 else "ADT^A03"
        message_control_id = msh[9] if len(msh) > 9 else f"MSG{int(datetime.utcnow().timestamp())}"

        # 2. Parse PID (Patient Identification)
        pid = segments.get("PID", [[]])[0]
        raw_patient_id = pid[3] if len(pid) > 3 else f"P{int(datetime.utcnow().timestamp())}"
        # Handle composite patient ID e.g. P12345^^^MRN
        patient_id = raw_patient_id.split("^")[0] if raw_patient_id else "P_UNKNOWN"
        
        # Name: PID-5 (Last^First^Middle)
        full_name = None
        if len(pid) > 5 and pid[5]:
            name_parts = pid[5].split("^")
            last = name_parts[0] if len(name_parts) > 0 else ""
            first = name_parts[1] if len(name_parts) > 1 else ""
            full_name = f"{first} {last}".strip() or None

        # DOB: PID-7 (YYYYMMDD)
        age = 65  # Default clinical average
        if len(pid) > 7 and pid[7]:
            dob_str = pid[7][:8]
            try:
                dob = datetime.strptime(dob_str, "%Y%m%d")
                today = datetime.utcnow()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                age = max(18, min(120, age))
            except Exception:
                pass

        # Sex: PID-8 (M/F/O) -> 1 for Male, 0 for Female
        sex = 1
        if len(pid) > 8 and pid[8]:
            sex = 1 if pid[8].upper().startswith("M") else 0

        # 3. Parse PV1 (Patient Visit)
        pv1 = segments.get("PV1", [[]])[0]
        
        # Admission Type: PV1-4 (E=Emergency, U=Urgent, L=Elective)
        admission_type = "emergency"
        if len(pv1) > 4 and pv1[4]:
            raw_adm = pv1[4].lower()
            if "elect" in raw_adm or raw_adm == "l":
                admission_type = "elective"
            elif "urg" in raw_adm or raw_adm == "u":
                admission_type = "urgent"
            else:
                admission_type = "emergency"

        # Discharge Destination: PV1-36
        discharge_destination = "home"
        if len(pv1) > 36 and pv1[36]:
            raw_dest = pv1[36].lower()
            if "snf" in raw_dest or "nursing" in raw_dest:
                discharge_destination = "nursing_home"
            elif "rehab" in raw_dest:
                discharge_destination = "rehab"
            elif "other" in raw_dest:
                discharge_destination = "other"

        # Length of stay: PV1-44 (Admit Date) and PV1-45 (Discharge Date)
        length_of_stay_days = 4
        if len(pv1) > 45 and pv1[44] and pv1[45]:
            try:
                admit_dt = datetime.strptime(pv1[44][:8], "%Y%m%d")
                disch_dt = datetime.strptime(pv1[45][:8], "%Y%m%d")
                los = (disch_dt - admit_dt).days
                length_of_stay_days = max(1, los)
            except Exception:
                pass

        # ICU Stay flag: Check PV1-3 (Assigned Location)
        icu_stay = False
        if len(pv1) > 3 and pv1[3]:
            loc_str = pv1[3].upper()
            if "ICU" in loc_str or "CCU" in loc_str or "INTENSIVE" in loc_str:
                icu_stay = True

        # 4. Parse DG1 (Diagnoses)
        dg1_list = segments.get("DG1", [])
        diagnoses: List[str] = []
        conditions_found = {
            "diabetes_flag": 0,
            "heart_failure_flag": 0,
            "copd_flag": 0,
            "ckd_flag": 0,
            "cancer_flag": 0,
            "dementia_flag": 0,
        }

        for dg in dg1_list:
            if len(dg) > 3 and dg[3]:
                diag_code_part = dg[3].split("^")[0].replace(".", "").upper()
                diag_desc = dg[3].split("^")[1] if "^" in dg[3] else dg[3]
                diagnoses.append(f"{diag_code_part}: {diag_desc}")
                
                # Check against ICD-10 prefix map
                for prefix, flag_name in ICD10_MAP.items():
                    if diag_code_part.startswith(prefix):
                        conditions_found[flag_name] = 1

        # Calculate comorbidity index based on conditions found
        comorbidity_index = sum(conditions_found.values()) * 2

        # 5. Parse OBX (Observation Results / Labs / Vitals)
        obx_list = segments.get("OBX", [])
        labs_extracted: Dict[str, float] = {
            "hemoglobin": 13.0,
            "creatinine": 1.1,
            "glucose": 115.0,
            "hba1c": 6.2,
            "wbc_count": 7.5,
            "total_bilirubin": 0.8,
            "bmi": 27.5,
        }

        for obx in obx_list:
            if len(obx) > 5:
                test_code = obx[3].split("^")[0].upper() if len(obx) > 3 else ""
                raw_val = obx[5]
                try:
                    val = float(raw_val)
                    # Check in LOINC map
                    if test_code in LOINC_MAP:
                        target_field = LOINC_MAP[test_code]
                        labs_extracted[target_field] = val
                    else:
                        # Check description substring
                        desc = obx[3].lower()
                        if "hemo" in desc or "hgb" in desc:
                            labs_extracted["hemoglobin"] = val
                        elif "creat" in desc:
                            labs_extracted["creatinine"] = val
                        elif "gluc" in desc:
                            labs_extracted["glucose"] = val
                        elif "a1c" in desc:
                            labs_extracted["hba1c"] = val
                        elif "wbc" in desc or "leuk" in desc:
                            labs_extracted["wbc_count"] = val
                        elif "bili" in desc:
                            labs_extracted["total_bilirubin"] = val
                        elif "bmi" in desc:
                            labs_extracted["bmi"] = val
                except (ValueError, TypeError):
                    continue

        # 6. Parse Medications (RXA / RXE / AL1)
        rx_list = segments.get("RXA", []) + segments.get("RXE", []) + segments.get("RXO", [])
        med_count = max(len(rx_list), 6)  # Default average 6 if no rx segment
        polypharmacy = 1 if med_count >= 5 else 0
        high_risk_meds = 1 if (conditions_found["heart_failure_flag"] or conditions_found["diabetes_flag"]) else 0

        # Construct HL7ParsedData
        parsed_data = HL7ParsedData(
            message_type=message_type,
            message_control_id=message_control_id,
            sending_application=sending_app,
            sending_facility=sending_facility,
            patient_id=patient_id,
            full_name=full_name,
            age=age,
            sex=sex,
            admission_type=admission_type,
            discharge_destination=discharge_destination,
            length_of_stay_days=length_of_stay_days,
            diagnoses=diagnoses,
            labs=labs_extracted,
            medication_count=med_count,
            polypharmacy=bool(polypharmacy),
            high_risk_medications=bool(high_risk_meds),
            icu_stay=icu_stay
        )

        # Construct PatientFeatures for ML prediction
        mapped_features = PatientFeatures(
            age=age,
            sex=sex,
            bmi=labs_extracted.get("bmi", 27.5),
            insurance_type="Medicare" if age >= 65 else "Private",
            comorbidity_index=comorbidity_index,
            diabetes_flag=conditions_found["diabetes_flag"],
            heart_failure_flag=conditions_found["heart_failure_flag"],
            copd_flag=conditions_found["copd_flag"],
            ckd_flag=conditions_found["ckd_flag"],
            cancer_flag=conditions_found["cancer_flag"],
            dementia_flag=conditions_found["dementia_flag"],
            previous_admissions_12m=2 if comorbidity_index >= 4 else 0,
            previous_er_visits_12m=2 if comorbidity_index >= 4 else 1,
            prior_30_day_readmission_flag=1 if comorbidity_index >= 6 else 0,
            admission_type=admission_type,
            length_of_stay_days=length_of_stay_days,
            icu_stay_flag=1 if icu_stay else 0,
            discharge_destination=discharge_destination,
            medication_count_at_discharge=med_count,
            polypharmacy_flag=polypharmacy,
            high_risk_medication_flag=high_risk_meds,
            hemoglobin=labs_extracted.get("hemoglobin", 13.0),
            creatinine=labs_extracted.get("creatinine", 1.1),
            glucose=labs_extracted.get("glucose", 115.0),
            hba1c=labs_extracted.get("hba1c", 6.2),
            wbc_count=labs_extracted.get("wbc_count", 7.5),
            total_bilirubin=labs_extracted.get("total_bilirubin", 0.8),
            follow_up_within_7_days_flag=1,
            total_charges_index_stay=length_of_stay_days * 3500.0,
            drg_code="291"
        )

        # 7. Generate HL7 v2 ACK (Acknowledgement)
        ack_message = cls.generate_ack(
            message_control_id=message_control_id,
            receiving_app=sending_app,
            receiving_facility=sending_facility,
            ack_code="AA",
            ack_text="Message accepted and processed for readmission scoring"
        )

        return parsed_data, mapped_features, ack_message

    @classmethod
    def generate_ack(
        cls,
        message_control_id: str,
        receiving_app: str,
        receiving_facility: str,
        ack_code: str = "AA",
        ack_text: str = "Message accepted successfully"
    ) -> str:
        """Generate standard HL7 v2 ACK response message"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        ack_ctrl_id = f"ACK{int(datetime.utcnow().timestamp())}"
        
        msh_seg = f"MSH|^~\\&|{settings.HL7_RECEIVING_APPLICATION}|{settings.HL7_RECEIVING_FACILITY}|{receiving_app}|{receiving_facility}|{timestamp}||ACK|{ack_ctrl_id}|P|2.5"
        msa_seg = f"MSA|{ack_code}|{message_control_id}|{ack_text}"
        
        return f"{msh_seg}\r{msa_seg}\r"

    @classmethod
    def get_sample_adt_messages(cls) -> Dict[str, str]:
        """Return ready-to-test sample HL7 v2 ADT messages"""
        return {
            "ADT_A03_Discharge_High_Risk": (
                "MSH|^~\\&|EPIC_EHR|METRO_HOSPITAL|READMISSION_AI|HOSPITAL_SYS|20260813120000||ADT^A03|MSG984210|P|2.5\r"
                "PID|1||P98421^^^MRN||JOHNSON^ROBERT^M||19490214|M|||742 EVERGREEN TERR^^BOSTON^MA^02115||(555)987-6543\r"
                "PV1|1|I|MED^402^2||||1084^MARTINEZ^ELENA|||||||||||EMERGENCY|V87412|||||||||||||||||||||||||20260803080000|20260813120000\r"
                "DG1|1|I10|I50.9^Heart failure unspecified^I10\r"
                "DG1|2|I10|E11.65^Type 2 diabetes with hyperglycemia^I10\r"
                "DG1|3|I10|N18.4^Chronic kidney disease stage 4^I10\r"
                "DG1|4|I10|J44.1^COPD with acute exacerbation^I10\r"
                "OBX|1|NM|718-7^Hemoglobin^LN||10.1|g/dL|12.0-17.5|L|||F\r"
                "OBX|2|NM|2160-0^Creatinine^LN||2.4|mg/dL|0.6-1.3|H|||F\r"
                "OBX|3|NM|2345-7^Glucose^LN||195|mg/dL|70-99|H|||F\r"
                "OBX|4|NM|4548-4^Hemoglobin A1c^LN||9.1|%|4.0-5.6|H|||F\r"
                "OBX|5|NM|6690-2^WBC^LN||11.8|10*3/uL|4.0-11.0|H|||F\r"
                "OBX|6|NM|1975-2^Total Bilirubin^LN||1.2|mg/dL|0.2-1.2|N|||F\r"
                "OBX|7|NM|39156-5^BMI^LN||31.2|kg/m2|18.5-24.9|H|||F\r"
            ),
            "ADT_A01_Admit_Low_Risk": (
                "MSH|^~\\&|CERNER_EHR|CITY_CLINIC|READMISSION_AI|HOSPITAL_SYS|20260813120000||ADT^A01|MSG10234|P|2.5\r"
                "PID|1||P10234^^^MRN||WILLIAMS^EMILY^||19880722|F|||450 PARK AVE^^NEW YORK^NY^10022||(555)234-5678\r"
                "PV1|1|I|SURG^101^1||||2041^CHEN^DAVID|||||||||||ELECTIVE|V99120|||||||||||||||||||||||||20260812080000|\r"
                "DG1|1|I10|K35.80^Unspecified acute appendicitis^I10\r"
                "OBX|1|NM|718-7^Hemoglobin^LN||13.8|g/dL|12.0-15.5|N|||F\r"
                "OBX|2|NM|2160-0^Creatinine^LN||0.8|mg/dL|0.5-1.1|N|||F\r"
                "OBX|3|NM|2345-7^Glucose^LN||92|mg/dL|70-99|N|||F\r"
                "OBX|4|NM|4548-4^Hemoglobin A1c^LN||5.2|%|4.0-5.6|N|||F\r"
                "OBX|5|NM|6690-2^WBC^LN||7.1|10*3/uL|4.0-11.0|N|||F\r"
                "OBX|6|NM|1975-2^Total Bilirubin^LN||0.6|mg/dL|0.2-1.2|N|||F\r"
                "OBX|7|NM|39156-5^BMI^LN||22.4|kg/m2|18.5-24.9|N|||F\r"
            )
        }


hl7_service = HL7v2Service()
