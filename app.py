cat << 'EOF' > app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------
DB_FILE = "servitrack.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            contact_number TEXT,
            brand TEXT,
            model TEXT,
            imei_sn TEXT,
            passcode TEXT,
            services TEXT,
            issue_desc TEXT,
            condition TEXT,
            estimated_cost REAL,
            status TEXT,
            tech_notes TEXT,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            category TEXT,
            quantity INTEGER,
            cost_price REAL,
            selling_price REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# PAGE CONFIG & CUSTOM STYLING (DARK CARD THEME)
# ---------------------------------------------------------
st.set_page_config(page_title="ServiTrack Workspace", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #0e1117;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1e2640 0%, #0f172a 100%);
        padding: 24px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 25px;
    }
    .main-header h1 {
        color: #f8fafc;
        font-weight: 700;
        margin: 0;
        font-size: 28px;
    }
    .main-header p {
        color: #94a3b8;
        margin: 5px 0 0 0;
        font-size: 14px;
    }

    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 18px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: 700;
    }

    /* Form and Box Containers */
    .css-1r6594q, .stForm {
        background-color: #1e293b;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }

    /* Buttons */
    .stButton>button, .stFormSubmitButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 24px;
        transition: all 0.2s ease;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }

    /* Section Headers */
    .section-title {
        color: #f1f5f9;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 15px;
        border-bottom: 2px solid #334155;
        padding-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# TOP BANNER
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>⚡ ServiTrack Pro</h1>
    <p>Mobile Hardware Diagnostics, Repair Tracking & Parts Management</p>
</div>
""", unsafe_allow_html=True)

# Top Bar Horizontal Navigation
tab_dash, tab_intake, tab_status, tab_parts = st.tabs([
    "📊 Overview", 
    "➕ New Repair Intake", 
    "🔍 Active Jobs & Updates", 
    "📦 Stock & Parts"
])

# ---------------------------------------------------------
# TAB 1: OVERVIEW
# ---------------------------------------------------------
with tab_dash:
    conn = sqlite3.connect(DB_FILE)
    df_tickets = pd.read_sql_query("SELECT * FROM tickets", conn)
    conn.close()

    total_jobs = len(df_tickets)
    in_progress = len(df_tickets[df_tickets['status'] == 'In Progress']) if not df_tickets.empty else 0
    ready_pickup = len(df_tickets[df_tickets['status'] == 'Ready for Pickup']) if not df_tickets.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Jobs Received", total_jobs)
    col2.metric("Bench Work (In Progress)", in_progress)
    col3.metric("Ready for Pickup", ready_pickup)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Live Work Orders</div>", unsafe_allow_html=True)
    
    if not df_tickets.empty:
        st.dataframe(
            df_tickets[['ticket_id', 'customer_name', 'brand', 'model', 'status', 'created_at']]
            .sort_values(by='ticket_id', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No work orders registered yet.")

# ---------------------------------------------------------
# TAB 2: INTAKE FORM
# ---------------------------------------------------------
with tab_intake:
    st.markdown("<div class='section-title'>Register Device for Repair</div>", unsafe_allow_html=True)
    
    with st.form("new_repair_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("##### 👤 Customer Info")
            customer_name = st.text_input("Customer Name *")
            contact_number = st.text_input("Contact Number *")
            
            st.markdown("##### 📱 Device Specifications")
            brand = st.selectbox("Brand", ["Apple", "Samsung", "Xiaomi", "Tecno / Infinix", "OPPO / Vivo", "Google Pixel", "Other"])
            model = st.text_input("Model (e.g., iPhone 12 Pro, Redmi Note 11) *")
            imei_sn = st.text_input("IMEI / Serial Number")
            passcode = st.text_input("PIN / Pattern Code")

        with c2:
            st.markdown("##### 🛠️ Service Specs & Faults")
            services = st.multiselect("Selected Services", [
                "Screen Replacement", "Battery Replacement", "Charging Port Repair",
                "Water Damage Diagnostics", "Software Flashing / Unlocking",
                "Board Repair / Soldering", "Speaker / Mic Replacement"
            ])
            issue_desc = st.text_area("Fault Symptoms / Notes")
            condition = st.text_input("Physical Condition (Scratches, frame dents, missing parts)")
            estimated_cost = st.number_input("Estimated Total ($)", min_value=0.0, step=5.0)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Submit Work Order"):
            if not customer_name or not model:
                st.error("Please enter both the Customer Name and Device Model.")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                service_str = ", ".join(services) if services else "General Assessment"
                
                c.execute('''
                    INSERT INTO tickets (customer_name, contact_number, brand, model, imei_sn, passcode, services, issue_desc, condition, estimated_cost, status, tech_notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (customer_name, contact_number, brand, model, imei_sn, passcode, service_str, issue_desc, condition, estimated_cost, "Received", "", created_at))
                
                ticket_id = c.lastrowid
                conn.commit()
                conn.close()
                st.success(f"Job Order #{ticket_id} logged for {customer_name} ({brand} {model})!")

# ---------------------------------------------------------
# TAB 3: STATUS UPDATES
# ---------------------------------------------------------
with tab_status:
    st.markdown("<div class='section-title'>Work Order Management</div>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_FILE)
    df_tickets = pd.read_sql_query("SELECT * FROM tickets", conn)
    conn.close()

    if not df_tickets.empty:
        ticket_options = [f"#{row['ticket_id']} - {row['customer_name']} | {row['brand']} {row['model']}" for _, row in df_tickets.iterrows()]
        selected_option = st.selectbox("Select Active Ticket", ticket_options)
        
        selected_id = int(selected_option.split("#")[1].split(" ")[0])
        ticket = df_tickets[df_tickets['ticket_id'] == selected_id].iloc[0]

        st.markdown("<br>", unsafe_allow_html=True)
        col_info, col_action = st.columns([1, 1])
        
        with col_info:
            st.markdown(f"""
            **Ticket ID:** #{ticket['ticket_id']}  
            **Customer:** {ticket['customer_name']} ({ticket['contact_number']})  
            **Device:** {ticket['brand']} {ticket['model']}  
            **IMEI/SN:** `{ticket['imei_sn'] if ticket['imei_sn'] else 'N/A'}`  
            **Passcode:** `{ticket['passcode'] if ticket['passcode'] else 'N/A'}`  
            **Services Needed:** {ticket['services']}  
            **Reported Fault:** {ticket['issue_desc']}
            """)

        with col_action:
            statuses = ["Received", "Pending Diagnostics", "Awaiting Parts", "In Progress", "Ready for Pickup", "Completed", "Cancelled"]
            current_index = statuses.index(ticket['status']) if ticket['status'] in statuses else 0
            
            new_status = st.selectbox("Update Status", statuses, index=current_index)
            tech_notes = st.text_area("Technician Work Log", value=ticket['tech_notes'])
            
            if st.button("Update Work Order"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("UPDATE tickets SET status=?, tech_notes=? WHERE ticket_id=?", (new_status, tech_notes, selected_id))
                conn.commit()
                conn.close()
                st.success(f"Ticket #{selected_id} updated to {new_status}!")
                st.rerun()
    else:
        st.info("No work orders to manage.")

# ---------------------------------------------------------
# TAB 4: PARTS INVENTORY
# ---------------------------------------------------------
with tab_parts:
    st.markdown("<div class='section-title'>Spare Parts Stock</div>", unsafe_allow_html=True)
    
    subtab1, subtab2 = st.tabs(["Inventory List", "Add Stock Item"])
    conn = sqlite3.connect(DB_FILE)
    
    with subtab1:
        df_inv = pd.read_sql_query("SELECT * FROM inventory", conn)
        if not df_inv.empty:
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
        else:
            st.info("Inventory empty.")
            
    with subtab2:
        with st.form("add_part_form", clear_on_submit=True):
            item_name = st.text_input("Part Name (e.g., iPhone 11 Display Original)")
            category = st.selectbox("Category", ["Screens", "Batteries", "Flex Cables", "Cameras", "ICs / Microcomponents", "Tools"])
            quantity = st.number_input("Quantity", min_value=1, step=1)
            cost_price = st.number_input("Cost Price ($)", min_value=0.0, step=1.0)
            selling_price = st.number_input("Retail Price ($)", min_value=0.0, step=1.0)
            
            if st.form_submit_button("Save to Inventory"):
                c = conn.cursor()
                c.execute("INSERT INTO inventory (item_name, category, quantity, cost_price, selling_price) VALUES (?, ?, ?, ?, ?)",
                          (item_name, category, quantity, cost_price, selling_price))
                conn.commit()
                st.success(f"Added {quantity}x {item_name}!")
                st.rerun()
                
    conn.close()
EOF
