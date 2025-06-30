import streamlit as st
import pandas as pd
from datetime import datetime
import base64
from fpdf import FPDF
import os

# Set page configuration
st.set_page_config(page_title="Lab Report Generator", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .header {
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    .patient-info {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .report-section {
        margin-bottom: 30px;
    }
    .test-table {
        width: 100%;
        border-collapse: collapse;
    }
    .test-table th, .test-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .test-table th {
        background-color: #f2f2f2;
    }
    .footer {
        margin-top: 30px;
        font-size: 12px;
        text-align: center;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Report templates
REPORT_TYPES = {
    "Complete Blood Count (CBC)": "cbc_template.csv",
    "Liver Function Test (LFT)": "lft_template.csv",
    "Kidney Function Test (KFT)": "kft_template.csv",
    "Thyroid Function Test (TFT)": "tft_template.csv"
}

# Initialize session state
if 'patient_data' not in st.session_state:
    st.session_state.patient_data = {}
if 'report_data' not in st.session_state:
    st.session_state.report_data = {}

class LabReportPDF(FPDF):
    def __init__(self, logo_path=None):
        super().__init__()
        # Increased bottom margin to prevent footer overlap
        self.set_auto_page_break(auto=True, margin=60)  # Increased from 15 to 60
        self.logo_path = logo_path
        self.is_first_page = True
    
    def add_report_title(self, title):
        """
        Adds a standardized report title section to the PDF
        
        Args:
            title (str): The name of the report to be displayed
        """
        # Save current Y position
        y_before = self.get_y()
        
        # Set font for the title
        self.set_font('Arial', 'B', 14)
        
        # Calculate width for the underline
        title_width = self.get_string_width(title) + 6  # Add some padding
        
        # Add some space before the title if we're not at the top
        # if y_before > 30:  # Not at the very top of the page
        #     self.ln(8)
        
        # Add the title text
        self.cell(0, 10, title.upper(), 0, 1, 'C')
        
        # Add underline
        self.set_draw_color(0, 0, 0)  # Black color
        self.set_line_width(0.5)
        x = (self.w - title_width) / 2  # Center the underline
        self.line(x, self.get_y(), x + title_width, self.get_y())
        
        # Add space after the title
        self.ln(6)

        self.set_font('Arial', 'B', 9)
        self.set_fill_color(240, 240, 240)
        
        self.cell(60, 8, 'TEST', 0, 0, 'L', True)
        self.cell(30, 8, 'RESULT', 0, 0, 'C', True)
        self.cell(25, 8, 'UNITS', 0, 0, 'C', True)
        self.cell(75, 8, 'NORMAL VALUES', 0, 1, 'C', True)
        
        self.ln(2)
        
        # Return the Y position after adding the title
        return self.get_y()

    def header(self):
        # Reserve vertical space equivalent to what was used before
        self.ln(25)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    
    def footer(self):
        # Position footer 50mm from bottom
        self.set_y(-50)
        
        self.set_y(-40)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        
        # Footer content
        self.cell(0, 4, 'Bold Indicates Abnormal Values', 0, 1, 'C')
        self.ln(2)
        
        # # Doctor info
        # self.set_font('Arial', 'B', 10)
        # self.set_text_color(0, 0, 0)
        # self.cell(0, 4, 'Lab Technician', 0, 1, 'C')
        # self.cell(0, 4, 'Name ??', 0, 1, 'C')
        # self.cell(0, 4, 'M.D. M.B.B.S.', 0, 1, 'C')
        
        # self.set_font('Arial', '', 8)
        # self.cell(0, 4, '305 Goldcrest Business Park, LB.S Marg, Ghatkopar (West), Mumbai - 400086, India', 0, 1, 'C')
    
    def check_page_break(self, height_needed):
        """Check if we need a page break before adding content"""
        # Get current position and page height minus margins
        current_y = self.get_y()
        page_height = self.h - 60  # Account for footer space
        
        if current_y + height_needed > page_height:
            self.add_page()
            return True
        return False
    
    def add_report_section(self, title, height_estimate=20):
        """Add a new report section with proper page break handling"""
        # Check if we need a page break for the section title
        if self.check_page_break(height_estimate):
            pass  # Page break already handled
        
        # Report title
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, title.upper(), 0, 1, 'C')
        self.ln(3)

    def add_patient_info(self, patient_info):
        self.set_font('Arial', 'B', 9)
        
        # Left column
        self.cell(30, 5, 'LAB NO.', 0, 0)
        self.cell(5, 5, ':', 0, 0)
        self.cell(50, 5, patient_info['lab_no'], 0, 0)
        
        # Right column
        self.cell(30, 5, 'REG DATE', 0, 0)
        self.cell(5, 5, ':', 0, 0)
        self.cell(50, 5, patient_info['reg_date'], 0, 1)
        
        self.cell(30, 5, 'PATIENT NAME', 0, 0)
        self.cell(5, 5, ':', 0, 0)
        self.cell(50, 5, patient_info['patient_name'], 0, 0)
        
        self.cell(30, 5, 'SAMPLE DATE', 0, 0)
        self.cell(5, 5, ':', 0, 0)
        self.cell(50, 5, patient_info['sample_date'], 0, 1)
        
        self.cell(30, 5, 'REF. BY DR.', 0, 0)
        self.cell(5, 5, ':', 0, 0)
        self.cell(50, 5, patient_info['ref_by'], 0, 0)
        
        self.cell(30, 5, 'REPORT DATE', 0, 0)
        self.cell(5, 5, ':', 0, 0)
        self.cell(50, 5, patient_info['report_date'], 0, 1)
        
        self.cell(30, 5, 'SAMPLE COLL. AT', 0, 0)
        self.cell(5, 5, ':', 0, 0)
        self.cell(50, 5, patient_info['sample_collection'], 0, 0)
        
        self.cell(30, 5, 'SEX / AGE', 0, 0)
        self.cell(5, 5, ':', 0, 0)
        self.cell(50, 5, f"{patient_info['sex']} / {patient_info['age']} Years", 0, 1)
        
        self.ln(5)
        
        # Draw line separator
        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
    
    def add_test_table(self, data, section_title=None):
        if section_title:
            self.set_font('Arial', 'B', 10)
            self.cell(0, 6, section_title.upper(), 0, 1, 'L')
            self.ln(2)        
        # Table rows
        self.set_font('Arial', '', 9)
        
        for index, row in data.iterrows():
            result_str = str(row['Result']) if pd.notna(row['Result']) else ''
            lower_value, upper_value = None, None
            try:
                normal_values = row['Normal Values']
                lower_value = float(normal_values.split("-")[0])
                upper_value = float(normal_values.split("-")[1].split(" ")[1])
            except Exception as e:
                pass

            self.cell(60, 5, str(row['Test']), 0, 0, 'L')
            
            if result_str and result_str.strip():
                try:
                    if float(result_str) and lower_value and upper_value:
                        if float(result_str) < lower_value:
                            self.set_font('Arial', 'B', 9)
                            self.cell(30, 5, result_str, 0, 0, 'C')
                            self.set_font('Arial', '', 9)
                        elif float(result_str) > upper_value:
                            self.set_font('Arial', 'B', 9)
                            self.cell(30, 5, result_str, 0, 0, 'C')
                            self.set_font('Arial', '', 9)
                        else:
                            self.set_font('Arial', '    ', 9)
                            self.cell(30, 5, result_str, 0, 0, 'C')
                            self.set_font('Arial', '', 9)
                    else:
                        self.set_font('Arial', '    ', 9)
                        self.cell(30, 5, result_str, 0, 0, 'C')
                        self.set_font('Arial', '', 9)
                except:
                    self.set_font('Arial', '', 9)
                    self.cell(30, 5, result_str, 0, 0, 'C')
                    self.set_font('Arial', '', 9)
            else:
                self.cell(30, 5, result_str, 0, 0, 'C')
            
            self.cell(25, 5, str(row['Units']), 0, 0, 'C')
            self.cell(75, 5, str(row['Normal Values']), 0, 1, 'C')
        
        self.ln(5)


def generate_cbc_report(pdf, patient_info, report_data):
    data = report_data["Complete Blood Count (CBC)"]
    pdf.add_report_title("COMPLETE BLOOD COUNT(CBC)")

    def print_if_has_result(subset, section_title=None):
        subset = subset[subset['Result'].notna() & (subset['Result'].astype(str).str.strip() != '')]
        if not subset.empty:
            pdf.add_test_table(subset, section_title)

    # Basic CBC parameters
    basic_tests = ['Haemoglobin', 'RBC Count', 'PCV']
    basic_data = data[data['Test'].isin(basic_tests)]
    print_if_has_result(basic_data)

    # RBC INDICES section
    rbc_indices = ['MCV', 'MCH', 'MCHC', 'RDW']
    rbc_data = data[data['Test'].isin(rbc_indices)]
    print_if_has_result(rbc_data, "RBC INDICES")

    # TOTAL WBC COUNT section
    wbc_tests = ['Total WBC Count', 'Neutrophils', 'Lymphocytes', 'Eosinophils', 'Monocytes', 'Basophils']
    wbc_data = data[data['Test'].isin(wbc_tests)]
    print_if_has_result(wbc_data, "TOTAL WBC COUNT")

    # PLATELETS section
    platelet_tests = ['Platelet Count', 'Platelets on Smear']
    platelet_data = data[data['Test'].isin(platelet_tests)]
    print_if_has_result(platelet_data, "PLATELETS")

    # PERIPHERAL BLOOD SMEAR section
    smear_tests = ['RBC Morphology', 'WBCs on PS', 'RDWSD', 'RDWCV', 'MPV', 'P-LCR']
    smear_data = data[data['Test'].isin(smear_tests)]
    print_if_has_result(smear_data, "PERIPHERAL BLOOD SMEAR")

    # Add instrument information
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 5, "Test done on Nihon Kohden MEK- 6420K fully automated cell counter.", 0, 1)
    pdf.ln(5)

def generate_lft_report(pdf, patient_info, report_data):
    data = report_data["Liver Function Test (LFT)"]
    pdf.add_report_title("Liver Function Test (LFT)")

    def print_if_has_result(subset, section_title=None):
        subset = subset[subset['Result'].notna() & (subset['Result'].astype(str).str.strip() != '')]
        if not subset.empty:
            pdf.add_test_table(subset, section_title)

    # Basic CBC parameters
    basic_tests = ['Bilirubin Total', 'Bilirubin Direct', 'Bilirubin Indirect', 'S.G.O.T.', 'S.G.P.T.', 'Alkaline Phosphatase', 'Total Proteins', 'Albumin', 'Globulin', 'A / G Ratio', 'G.G.T.P.']
    basic_data = data[data['Test'].isin(basic_tests)]
    print_if_has_result(basic_data)

    # Add instrument information
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 5, "Test Done on semi automated analyser Micro Lab RX-50.", 0, 1)
    pdf.ln(5)


def create_pdf_report(patient_info, report_data, selected_reports, logo_path=None):
    pdf = LabReportPDF(logo_path)
    pdf.add_page()
    pdf.add_patient_info(patient_info)
    
    # Generate each selected report
    for report_name in selected_reports:
        if report_name == "Complete Blood Count (CBC)":
            generate_cbc_report(pdf, patient_info, report_data)
        elif report_name == "Liver Function Test (LFT)":
            generate_lft_report(pdf, patient_info, report_data)
        # elif report_name == "Kidney Function Test (KFT)":
        #     generate_kft_report(pdf, patient_info, report_data)
        # elif report_name == "Thyroid Function Test (TFT)":
        #     generate_tft_report(pdf, patient_info, report_data)
        
        # Add page break if more reports to come
        if report_name != selected_reports[-1]:
            pdf.add_page()
            pdf.add_patient_info(patient_info)  # Add patient info on each page
    
    # Save the PDF
    filename = f"{patient_info['patient_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

def load_report_template(report_name):
    if report_name == "Complete Blood Count (CBC)":
        data = {
            "Test": [
                "Haemoglobin", "RBC Count", "PCV", 
                "MCV", "MCH", "MCHC", "RDW",
                "Total WBC Count", "Neutrophils", "Lymphocytes", 
                "Eosinophils", "Monocytes", "Basophils",
                "Platelet Count", "Platelets on Smear",
                "RBC Morphology", "WBCs on PS", "RDWSD", "RDWCV", "MPV", "P-LCR"
            ],
            "Result": [""] * 21,
            "Units": [
                "g%", "million/cu.mm.", "%", 
                "fl", "pg", "%", "fl",
                "/cu.mm", "%", "%", 
                "%", "%", "%",
                "lak/cu.mm", "",
                "", "", "fl", "%", "fl", "%"
            ],
            "Normal Values": [
                "Male: 14 - 16 g%, Female: 12 - 14 g%", "4.0 - 6.0 million/cu.mm", "35 - 60 %",
                "80 - 99 fl", "27 - 31 pg", "32 - 37 %", "9 - 17 fl",
                "4000 - 10,000 /cu.mm", "40 - 70 %", "20 - 45 %",
                "00 - 06 %", "00 - 08 %", "00 - 01 %",
                "150000 - 450000 /lak cu.mm", "Adequate On Smear",
                "Normocytic, Normochromic", "Normal", "37 - 54 fl", "11 - 16 %", "9 - 13 fl", "13 - 43 %"
            ]
        }
        return pd.DataFrame(data)
    
    elif report_name == "Liver Function Test (LFT)":
        data = {
            "Test": ['Bilirubin Total', 'Bilirubin Direct', 'Bilirubin Indirect', 'S.G.O.T.', 'S.G.P.T.', 'Alkaline Phosphatase', 'Total Proteins', 'Albumin', 'Globulin', 'A / G Ratio', 'G.G.T.P.'],
            "Result": [""] * 11,
            "Units": ["mg/dl", "mg/dl", "mg/dl", "U/L", "IU/L", "IU/L", 
                     "gm/dl", "gm/dl", "gm/dl", "", "IU/L"],
            "Normal Values": ["0.1 - 1.2 mg/dl", "0.1 - 0.4 mg/dl", "0.1 - 0.7 mg/dl",
                             "0 - 46 U/L", "0 - 49 U/L", "15 - 112 IU/L",
                             "6.0 - 8.3 gm/dl", "3.2 - 5.0 gm/dl", "2.0 - 3.5 gm/dl", "1.0 - 2.3", "25 - 43 IU/L"]
        }
        return pd.DataFrame(data)
    
    elif report_name == "Kidney Function Test (KFT)":
        data = {
            "Test": ["Blood Urea", "Serum Creatinine", "Uric Acid", 
                    "Sodium", "Potassium", "Chloride"],
            "Result": [""] * 6,
            "Units": ["mg/dl", "mg/dl", "mg/dl", "mEq/L", "mEq/L", "mEq/L"],
            "Normal Values": ["15 - 45 mg/dl", "0.6 - 1.4 mg/dl", "2.4 - 7.0 mg/dl",
                             "135 - 155 mEq/L", "3.5 - 5.5 mEq/L", "98 - 107 mEq/L"]
        }
        return pd.DataFrame(data)
    
    elif report_name == "Thyroid Function Test (TFT)":
        data = {
            "Test": ["T3 (Triiodothyronine)", "T4 (Thyroxine)", "TSH"],
            "Result": [""] * 3,
            "Units": ["ng/ml", "μg/dl", "μIU/ml"],
            "Normal Values": ["0.8 - 2.0 ng/ml", "4.8 - 12.7 μg/dl", "0.27 - 4.2 μIU/ml"]
        }
        return pd.DataFrame(data)
    
    else:
        return pd.DataFrame({
            "Test": ["Test 1", "Test 2", "Test 3"],
            "Result": ["", "", ""],
            "Units": ["unit 1", "unit 2", "unit 3"],
            "Normal Values": ["normal 1", "normal 2", "normal 3"]
        })

def main():
    st.title("🔬 Lab Report Generator")
    st.markdown("---")
    
    # Step 1: Select Reports
    st.header("📋 Select Report Types")
    selected_reports = st.multiselect(
        "Choose the tests you want to include:",
        list(REPORT_TYPES.keys()),
        help="You can select multiple report types"
    )
    
    if selected_reports:
        # Step 2: Patient Information
        st.header("👤 Patient Information")
        st.markdown("Please fill in the patient details:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            lab_no = st.text_input("Lab Number:", value="2")
            patient_name = st.text_input("Patient Name:", value="MR. ")
            ref_by = st.text_input("Referred By:", value="DR. ")
            sample_collection = st.text_input("Sample Collection At:", value="CRYSTAL LAB")
            sex = st.selectbox("Sex:", ["Male", "Female", "Other"])
            age = st.number_input("Age (Years):", min_value=0, max_value=120, value=23)
        with col2:
            reg_date = st.date_input("Registration Date:", value=datetime.now())
            reg_time = st.time_input("Registration Time:", value=datetime.now().time())
            sample_date = st.date_input("Sample Date:", value=datetime.now())
            sample_time = st.time_input("Sample Time:", value=datetime.now().time())
            report_date = st.date_input("Report Date:", value=datetime.now())
            report_time = st.time_input("Report Time:", value=datetime.now().time())
            
        st.markdown("---")
            
        
        # Store patient info
        st.session_state.patient_data = {
            "lab_no": lab_no,
            "patient_name": patient_name.upper(),
            "ref_by": ref_by.upper(),
            "sample_collection": sample_collection.upper(),
            "reg_date": f"{reg_date.strftime('%d-%b-%Y')} {reg_time.strftime('%I:%M %p')}",
            "sample_date": f"{sample_date.strftime('%d-%b-%Y')} {sample_time.strftime('%I:%M %p')}",
            "report_date": f"{report_date.strftime('%d-%b-%Y')} {report_time.strftime('%I:%M %p')}",
            "sex": sex,
            "age": age
        }
        
        # Step 3: Enter Test Results
        st.header("🧪 Enter Test Results")
        st.markdown("Fill in the test results for each selected report:")
        
        for i, report_name in enumerate(selected_reports):
            with st.expander(f"📊 {report_name}", expanded=True):
                template_df = load_report_template(report_name)
                
                # Create editable dataframe
                edited_df = st.data_editor(
                    template_df,
                    column_config={
                        "Test": st.column_config.TextColumn(
                            "Test Name",
                            disabled=True,
                            width="large"
                        ),
                        "Result": st.column_config.TextColumn(
                            "Result",
                            width="medium",
                            help="Enter the test result value"
                        ),
                        "Units": st.column_config.TextColumn(
                            "Units",
                            disabled=True,
                            width="small"
                        ),
                        "Normal Values": st.column_config.TextColumn(
                            "Normal Range",
                            disabled=True,
                            width="medium"
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=(len(template_df) + 1) * 35 + 3 ,
                    key=f"editor_{i}"
                )
                
                st.session_state.report_data[report_name] = edited_df
        
        # Step 4: Generate Report
        st.header("📄 Generate Report")
        # st.markdown("Review and generate the final lab report:")
        
        # Logo path input
        logo_path = r"C:\Users\Admin\Pictures\Screenshots\Screenshot 2025-06-26 140637.png"
        
        # # Show summary
        # with st.expander("📋 Report Summary", expanded=False):
        #     st.write("**Patient:** ", st.session_state.patient_data['patient_name'])
        #     st.write("**Lab No:** ", st.session_state.patient_data['lab_no'])
        #     st.write("**Reports:** ", ", ".join(selected_reports))
        #     st.write("**Report Date:** ", st.session_state.patient_data['report_date'])
        #     if logo_path and logo_path != "/path/to/your/logo.png":
        #         st.write("**Logo:** ", logo_path)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔄 Generate PDF Report", type="primary", use_container_width=True):
                with st.spinner("Generating report..."):
                    try:
                        # Use logo path if provided and exists
                        logo_to_use = logo_path if (logo_path and logo_path != "/path/to/your/logo.png" and os.path.exists(logo_path)) else None
                        
                        pdf_filename = create_pdf_report(
                            st.session_state.patient_data,
                            st.session_state.report_data,
                            selected_reports,
                            logo_to_use
                        )
                        
                        st.success("✅ Report generated successfully!")
                        
                        # Provide download link
                        with open(pdf_filename, "rb") as pdf_file:
                            pdf_data = pdf_file.read()
                            b64_pdf = base64.b64encode(pdf_data).decode()
                            
                            href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_filename}" style="text-decoration: none;">'
                            href += '<button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">📥 Download PDF Report</button>'
                            href += '</a>'
                            
                            st.markdown(href, unsafe_allow_html=True)

                        
                        
                        # Clean up the file after creating download link
                        if os.path.exists(pdf_filename):
                            try:
                                os.remove(pdf_filename)
                            except:
                                pass  # File might still be in use
                                
                    except Exception as e:
                        st.error(f"❌ Error generating report: {str(e)}")
                        st.error("Please check your inputs and try again.")
        
        with col2:
            if st.button("🔄 Reset Form", use_container_width=True):
                # Clear session state
                st.session_state.patient_data = {}
                st.session_state.report_data = {}
                st.rerun()
        
        # Step 5: Preview Section
        st.header("👁️ Report Preview")
        if st.session_state.patient_data and st.session_state.report_data:
            with st.expander("📖 Preview Report Content", expanded=False):
                # Patient info preview
                st.subheader("Patient Information")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Lab No:** {st.session_state.patient_data['lab_no']}")
                    st.write(f"**Patient Name:** {st.session_state.patient_data['patient_name']}")
                    st.write(f"**Referred By:** {st.session_state.patient_data['ref_by']}")
                    st.write(f"**Sample Collection:** {st.session_state.patient_data['sample_collection']}")
                
                with col2:
                    st.write(f"**Registration Date:** {st.session_state.patient_data['reg_date']}")
                    st.write(f"**Sample Date:** {st.session_state.patient_data['sample_date']}")
                    st.write(f"**Report Date:** {st.session_state.patient_data['report_date']}")
                    st.write(f"**Sex/Age:** {st.session_state.patient_data['sex']} / {st.session_state.patient_data['age']} Years")
                
                st.markdown("---")
                
                # Test results preview
                for report_name in selected_reports:
                    st.subheader(f"📊 {report_name}")
                    if report_name in st.session_state.report_data:
                        df = st.session_state.report_data[report_name]
                        # Show only filled results
                        filled_df = df[df['Result'].str.strip() != ''].copy() if not df.empty else df
                        if not filled_df.empty:
                            st.dataframe(filled_df, use_container_width=True, hide_index=True)
                        else:
                            st.info("No results entered yet for this test.")
                    st.markdown("---")

    else:
        st.info("👆 Please select at least one report type to begin.")
        
        # Add some helpful information
        st.markdown("### 📋 Available Report Types:")
        for report_type in REPORT_TYPES.keys():
            st.markdown(f"• **{report_type}**")
        
        st.markdown("### ✨ Features:")
        st.markdown("""
        • **Professional PDF Generation** - Create lab reports with company branding
        • **Multiple Test Types** - Support for CBC, LFT, KFT, TFT and more
        • **Customizable Templates** - Easy to modify test parameters
        • **Patient Management** - Complete patient information tracking
        • **Download Ready** - Instant PDF download with proper formatting
        """)

if __name__ == "__main__":
    main()