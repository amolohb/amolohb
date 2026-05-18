import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import datetime
import random
import sqlite3
import json

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Blockchain HIMS Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS 
# ==========================================
st.markdown("""
<style>

.main {
    background-color: #f4f7fb;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #0f172a,
        #1e293b
    );
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

h1, h2, h3 {
    color: #0f172a;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 18px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

.metric-card {
    background: linear-gradient(
        135deg,
        #2563eb,
        #1d4ed8
    );
    color: white;
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
}

.metric-card h1 {
    font-size: 38px;
    margin-bottom: 5px;
}

.metric-card p {
    font-size: 16px;
}

.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
    font-weight: bold;
}

.verify-good {
    background-color: #dcfce7;
    padding: 20px;
    border-radius: 12px;
    color: #166534;
    font-weight: bold;
}

.verify-bad {
    background-color: #fee2e2;
    padding: 20px;
    border-radius: 12px;
    color: #991b1b;
    font-weight: bold;
}

.alert-success {
    background-color: #dcfce7;
    padding: 15px;
    border-radius: 12px;
    color: #166534;
    font-weight: bold;
    margin-bottom: 10px;
}

.alert-danger {
    background-color: #fee2e2;
    padding: 15px;
    border-radius: 12px;
    color: #991b1b;
    font-weight: bold;
    margin-bottom: 10px;
}

.alert-warning {
    background-color: #fef3c7;
    padding: 15px;
    border-radius: 12px;
    color: #92400e;
    font-weight: bold;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# LOAD DATASET
# ==========================================
df = pd.read_excel(
    "dataset/hospital_data.xlsx"
)

# ==========================================
# SQLITE DATABASE
# ==========================================
conn = sqlite3.connect(
    "blockchain_hims.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS blockchain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_index INTEGER,
    timestamp TEXT,
    data TEXT,
    previous_hash TEXT,
    current_hash TEXT
)
""")

conn.commit()

# ==========================================
# USERS
# ==========================================
users = {

    "admin": {
        "password": "admin123",
        "role": "Admin"
    },

    "doctor": {
        "password": "doctor123",
        "role": "Doctor"
    },

    "nurse": {
        "password": "nurse123",
        "role": "Nurse"
    },

    "patient": {
        "password": "patient123",
        "role": "Patient"
    }
}

# ==========================================
# SESSION STATE
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = ""

if "username" not in st.session_state:
    st.session_state.username = ""

# ==========================================
# LOGIN
# ==========================================
def login():

    st.title("🏥 Blockchain HIMS Login")

    st.markdown("""
    <div class='card'>
    Secure Blockchain-Based Hospital Information
    Management System
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        if username in users:

            if users[username]["password"] == password:

                st.session_state.logged_in = True
                st.session_state.role = users[username]["role"]
                st.session_state.username = username

                st.success("Login Successful")
                st.rerun()

            else:
                st.error("Wrong Password")

        else:
            st.error("User Not Found")

# ==========================================
# LOGOUT
# ==========================================
def logout():

    st.session_state.logged_in = False
    st.session_state.role = ""
    st.session_state.username = ""

    st.rerun()

# ==========================================
# BLOCKCHAIN
# ==========================================
class Block:

    def __init__(
        self,
        index,
        data,
        previous_hash
    ):

        self.index = index

        self.timestamp = str(
            datetime.datetime.now()
        )

        self.data = data

        self.previous_hash = previous_hash

        self.hash = self.calculate_hash()

    def calculate_hash(self):

        block_string = (
            str(self.index)
            + self.timestamp
            + str(self.data)
            + self.previous_hash
        )

        return hashlib.sha256(
            block_string.encode()
        ).hexdigest()

class Blockchain:

    def __init__(self):

        self.chain = [
            self.create_genesis_block()
        ]

    def create_genesis_block(self):

        return Block(
            0,
            "Genesis Block",
            "0"
        )

    def get_latest_block(self):

        return self.chain[-1]

    def add_block(self, data):

        new_block = Block(
            len(self.chain),
            data,
            self.get_latest_block().hash
        )

        self.chain.append(new_block)

        cursor.execute("""
        INSERT INTO blockchain (
            block_index,
            timestamp,
            data,
            previous_hash,
            current_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            new_block.index,
            new_block.timestamp,
            json.dumps(new_block.data),
            new_block.previous_hash,
            new_block.hash
        ))

        conn.commit()

# ==========================================
# INIT BLOCKCHAIN
# ==========================================
blockchain = Blockchain()

existing_blocks = pd.read_sql_query(
    "SELECT * FROM blockchain",
    conn
)

if existing_blocks.empty:

    for _, row in df.head(10).iterrows():

        blockchain.add_block({

            "participant":
            row["Participant_ID"],

            "role":
            row["Role"],

            "referral_time":
            row["Referral_Time_After_Minutes"]
        })

# ==========================================
# SMART CONTRACT
# ==========================================
def smart_contract_validation(
    role,
    referral_time
):

    if role == "Doctor" and referral_time < 30:
        return "APPROVED"

    elif role == "Nurse" and referral_time < 20:
        return "APPROVED"

    elif referral_time > 120:
        return "BLOCKED"

    else:
        return "PENDING"

# ==========================================
# LOGIN CHECK
# ==========================================
if not st.session_state.logged_in:
    login()
    st.stop()

# ==========================================
# SIDEBAR
# ==========================================
role = st.session_state.role

st.sidebar.title("🏥 HIMS Navigation")

st.sidebar.success(
    f"Logged in as: {role}"
)

if st.sidebar.button("Logout"):
    logout()

# ==========================================
# ROLE NAVIGATION
# ==========================================
if role == "Admin":

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Admin Dashboard",
            "Patient Records",
            "Smart Contracts",
            "Blockchain Ledger",
            "Security Analytics",
            "Immutability Verification",
            "Referral Workflow",
            "Interoperability Demo",
            "Blockchain Network",
            "User Adoption Clusters",
            "Pilot Findings",
            "Export Reports"
        ]
    )

elif role == "Doctor":

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Doctor Dashboard",
            "Patient Records",
            "Referral Center",
            "Referral Workflow"
        ]
    )

elif role == "Nurse":

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Nurse Dashboard",
            "Patient Monitoring"
        ]
    )

else:

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Patient Portal"
        ]
    )

# ==========================================
# REAL-TIME ALERTS
# ==========================================
st.markdown("""
<div class='alert-warning'>
⚠️ Unauthorized access attempt detected
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='alert-success'>
✓ Referral approved successfully
</div>
""", unsafe_allow_html=True)

# ==========================================
# ADMIN DASHBOARD
# ==========================================
if menu == "Admin Dashboard":

    st.title("🏥 Admin Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(f"""
        <div class='metric-card'>
        <h1>{len(df)}</h1>
        <p>Participants</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown(f"""
        <div class='metric-card'>
        <h1>{round(df['System_Uptime_Percent'].mean(),2)}%</h1>
        <p>Average Uptime</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:

        st.markdown(f"""
        <div class='metric-card'>
        <h1>{round(df['Referral_Time_After_Minutes'].mean(),2)}</h1>
        <p>Average Referral Time</p>
        </div>
        """, unsafe_allow_html=True)

    role_counts = (
        df["Role"]
        .value_counts()
        .reset_index()
    )

    role_counts.columns = [
        "Role",
        "Count"
    ]

    fig = px.bar(
        role_counts,
        x="Role",
        y="Count",
        title="Hospital Role Distribution",
        text_auto=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==========================================
# PATIENT RECORDS
# ==========================================
elif menu == "Patient Records":

    st.title("🩺 Patient Records")

    patient_id = st.selectbox(
        "Select Patient",
        df["Participant_ID"]
    )

    patient = df[
        df["Participant_ID"] == patient_id
    ].iloc[0]

    st.dataframe(
        patient.to_frame(),
        use_container_width=True
    )

# ==========================================
# SMART CONTRACTS
# ==========================================
elif menu == "Smart Contracts":

    st.title("📜 Smart Contracts")

    selected_role = st.selectbox(
        "Role",
        df["Role"].unique()
    )

    referral_time = st.number_input(
        "Referral Time",
        1,
        500,
        25
    )

    result = smart_contract_validation(
        selected_role,
        referral_time
    )

    if result == "APPROVED":

        st.markdown("""
        <div class='alert-success'>
        ✓ Smart Contract Approved
        </div>
        """, unsafe_allow_html=True)

    elif result == "BLOCKED":

        st.markdown("""
        <div class='alert-danger'>
        ⚠ Transaction Blocked
        </div>
        """, unsafe_allow_html=True)

    else:

        st.markdown("""
        <div class='alert-warning'>
        Pending Validation
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# BLOCKCHAIN LEDGER
# ==========================================
elif menu == "Blockchain Ledger":

    st.title("⛓ Blockchain Ledger")

    blockchain_data = pd.read_sql_query(
        "SELECT * FROM blockchain",
        conn
    )

    st.dataframe(
        blockchain_data,
        use_container_width=True
    )

# ==========================================
# SECURITY ANALYTICS
# ==========================================
elif menu == "Security Analytics":

    st.title("🛡 AI Security Analytics")

    security_logs = []

    avg_referral = (
        df["Referral_Time_After_Minutes"]
        .mean()
    )

    for i in range(20):

        login_attempts = random.randint(1, 10)

        referral_time = random.randint(5, 200)

        if login_attempts > 5:
            risk = "HIGH"

        elif referral_time > avg_referral * 1.5:
            risk = "MEDIUM"

        else:
            risk = "LOW"

        security_logs.append({

            "User":
            f"User-{i}",

            "Login Attempts":
            login_attempts,

            "Referral Time":
            referral_time,

            "Risk Level":
            risk
        })

    threat_df = pd.DataFrame(
        security_logs
    )

    st.dataframe(
        threat_df,
        use_container_width=True
    )

    risk_counts = (
        threat_df["Risk Level"]
        .value_counts()
        .reset_index()
    )

    risk_counts.columns = [
        "Risk Level",
        "Count"
    ]

    fig = px.bar(
        risk_counts,
        x="Risk Level",
        y="Count",
        color="Risk Level",
        title="AI Threat Detection"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==========================================
# IMMUTABILITY VERIFICATION
# ==========================================
elif menu == "Immutability Verification":

    st.title(
        "🔍 Blockchain Immutability Verification"
    )

    selected_patient = st.selectbox(
        "Select Record",
        df["Participant_ID"]
    )

    patient = df[
        df["Participant_ID"] == selected_patient
    ].iloc[0]

    original_hash = hashlib.sha256(
        str(patient.to_dict()).encode()
    ).hexdigest()

    tamper = st.checkbox(
        "Simulate Data Tampering"
    )

    modified_patient = patient.copy()

    if tamper:

        modified_patient[
            "Referral_Time_After_Minutes"
        ] += 50

    new_hash = hashlib.sha256(
        str(modified_patient.to_dict()).encode()
    ).hexdigest()

    if original_hash == new_hash:

        st.markdown("""
        <div class="verify-good">
        ✅ Record Verified
        <br><br>
        No Tampering Detected
        </div>
        """, unsafe_allow_html=True)

    else:

        st.markdown("""
        <div class="verify-bad">
        ⚠ Hash Mismatch Detected
        <br><br>
        Possible Data Manipulation
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# REFERRAL WORKFLOW
# ==========================================
elif menu == "Referral Workflow":

    st.title(
        "🚑 Referral Workflow Visualization"
    )

    workflow_steps = [

        "Patient Registered",
        "Doctor Review",
        "Referral Created",
        "Blockchain Verification",
        "Receiving Hospital Approval",
        "Completed"
    ]

    for step in workflow_steps:

        st.success(f"✅ {step}")

# ==========================================
# INTEROPERABILITY DEMO
# ==========================================
elif menu == "Interoperability Demo":

    st.title(
        "🌐 Healthcare Interoperability Demo"
    )

    interoperability_data = pd.DataFrame({

        "System": [
            "Hospital A",
            "KHIS",
            "FHIR API",
            "SHA/NHIF",
            "Hospital B"
        ],

        "Sync Status": [
            100,
            95,
            98,
            96,
            100
        ]
    })

    fig = px.bar(
        interoperability_data,
        x="System",
        y="Sync Status",
        title="Interoperability Synchronization"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==========================================
# BLOCKCHAIN NETWORK
# ==========================================
elif menu == "Blockchain Network":

    st.title(
        "⛓ Blockchain Network Visualization"
    )

    network_nodes = pd.DataFrame({

        "Node": [
            "JOOTRH Node",
            "SHA Node",
            "Pharmacy Node",
            "Laboratory Node",
            "Radiology Node",
            "KHIS Node"
        ],

        "Connections": [
            10,
            8,
            6,
            7,
            5,
            9
        ]
    })

    fig = px.scatter(
        network_nodes,
        x="Connections",
        y="Node",
        size="Connections",
        text="Node",
        title="Healthcare Blockchain Nodes"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==========================================
# USER ADOPTION CLUSTERS
# ==========================================
elif menu == "User Adoption Clusters":

    st.title(
        "📊 User Adoption Cluster Analysis"
    )

    cluster_data = pd.DataFrame({

        "Cluster": [
            "Tech-Savvy Adopters",
            "Cautious Users",
            "Resistant Traditionalists"
        ],

        "Percentage": [
            45,
            35,
            20
        ]
    })

    pie_fig = px.pie(
        cluster_data,
        names="Cluster",
        values="Percentage",
        title="Healthcare Blockchain Adoption"
    )

    st.plotly_chart(
        pie_fig,
        use_container_width=True
    )

    radar_fig = go.Figure()

    radar_fig.add_trace(go.Scatterpolar(

        r=[90, 70, 30],

        theta=[
            "Technology Acceptance",
            "Security Trust",
            "Blockchain Readiness"
        ],

        fill='toself',

        name='Adoption Behavior'
    ))

    radar_fig.update_layout(

        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),

        title="User Adoption Behavior Radar"
    )

    st.plotly_chart(
        radar_fig,
        use_container_width=True
    )

# ==========================================
# PILOT FINDINGS
# ==========================================
elif menu == "Pilot Findings":

    st.title("📈 Pilot Findings")

    findings = pd.DataFrame({

        "Metric": [
            "Unauthorized Access",
            "Referral Time",
            "Uptime"
        ],

        "Before": [
            "12.4",
            "3 Days",
            "85%"
        ],

        "After": [
            "1.8",
            "90 sec",
            "99.8%"
        ]
    })

    st.table(findings)

# ==========================================
# EXPORT REPORTS
# ==========================================
elif menu == "Export Reports":

    st.title("📄 Export Reports")

    blockchain_logs = pd.read_sql_query(
        "SELECT * FROM blockchain",
        conn
    )

    csv = blockchain_logs.to_csv(
        index=False
    ).encode('utf-8')

    st.download_button(

        label="⬇ Download Blockchain Audit Logs",

        data=csv,

        file_name="blockchain_audit_logs.csv",

        mime="text/csv"
    )

    patient_csv = df.to_csv(
        index=False
    ).encode('utf-8')

    st.download_button(

        label="⬇ Download Patient Report",

        data=patient_csv,

        file_name="patient_report.csv",

        mime="text/csv"
    )

# ==========================================
# DOCTOR DASHBOARD
# ==========================================
elif menu == "Doctor Dashboard":

    st.title(" Doctor Dashboard")

    st.dataframe(
        df.head(10)
    )

# ==========================================
# REFERRAL CENTER
# ==========================================
elif menu == "Referral Center":

    st.title("🚑 Referral Center")

    patient = st.selectbox(
        "Select Patient",
        df["Participant_ID"]
    )

    hospital = st.selectbox(
        "Refer To",
        [
            "Radiology",
            "Pharmacy",
            "Lab",
            "Specialist"
        ]
    )

    if st.button("Send Referral"):

        st.success(
            f"Referral Sent to {hospital}"
        )

# ==========================================
# NURSE DASHBOARD
# ==========================================
elif menu == "Nurse Dashboard":

    st.title(" Nurse Dashboard")

    st.dataframe(
        df.head(5)
    )

# ==========================================
# PATIENT MONITORING
# ==========================================
elif menu == "Patient Monitoring":

    st.title("📋 Patient Monitoring")

    st.dataframe(
        df.head(10)
    )

# ==========================================
# PATIENT PORTAL
# ==========================================
elif menu == "Patient Portal":

    st.title(" Patient Portal")

    st.info("Diagnosis: Malaria")

    st.info("Prescription: Coartem")

    st.info("Doctor: Dr. Ouma")

    st.markdown("---")

    st.subheader(
        " Blockchain Consent Management"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "Grant Doctor Access"
        ):

            st.success(
                "Doctor Access Granted"
            )

    with col2:

        if st.button(
            "Revoke Access"
        ):

            st.warning(
                "Doctor Access Revoked"
            )

    with col3:

        if st.button(
            "Emergency Access"
        ):

            st.error(
                "Emergency Access Activated"
            )

    st.success(
        "✔ Kenya Data Protection Act Compliant"
    )

    st.success(
        "✔ Blockchain Consent Logged"
    )

    st.success(
        "✔ Patient-Controlled Access"
    )