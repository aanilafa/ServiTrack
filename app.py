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
    # Create tickets table
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
    # Create inventory table
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
# STREAMLIT CONFIG & UI
# ---------------------------------------------------------
st.set_page_config(page_title="ServiTrack - Mobile Repair", page_icon="📱", layout="wide")

st.title("📱 ServiTrack - Repair & Service Management")

menu = st.sidebar.selectbox("Navigation", ["Dashboard", "New Repair Intake", "Job Status & Updates", "Inventory"])

# ---------------------------------------------------------
# MODULE 1: DASHBOARD
# ---------------------------------------------------------
if menu == "Dashboard":
    st.subheader("📊 Repair Shop Overview")
    
    conn = sqlite3.connect(DB_FILE)
    df_tickets = pd.read_sql_query("SELECT * FROM tickets", conn)
    conn.close()

    total_jobs = len(df_tickets)
    in_progress = len(df_tickets[df_tickets['status'] == 'In Progress']) if not df_tickets.empty else 0
    ready_pickup = len(df_tickets[df_tickets['status'] == 'Ready for Pickup']) if not df_tickets.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Jobs Logged", total_jobs)
    col2.metric("In Progress", in_progress)
    col3.metric("Ready for Pickup", ready_pickup)

    st.markdown("---")
    st.subheader("Recent Work Orders")
    if not df_tickets.empty:
        st.dataframe(df_tickets[['ticket_id', 'customer_name', 'brand', 'model', 'status', 'created_at']].sort_values(by='ticket_id', ascending=False), use_container_width=True)
    else:
        st.info("No repair tickets recorded yet. Go to 'New Repair Intake' to log your first job!")

# ---------------------------------------------------------
# MODULE 2: NEW REPAIR INTAKE
# ---------------------------------------------------------
elif menu == "New Repair Intake":
    st.subheader("📝 Log New Phone Repair")
    
    with st.form("intake_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Customer & Device")
            customer_name = st.text_input("Customer Name *")
            contact_number = st.text_input("Phone Number *")
            brand = st.selectbox("Brand", ["Apple", "Samsung", "Xiaomi", "Tecno / Infinix", "OPPO / Vivo", "Google Pixel", "Other"])
            model = st.text_input("Model (e.g., iPhone 11, Galaxy A53) *")
            imei_sn = st.text_input("IMEI / Serial Number")
            passcode = st.text_input("PIN / Pattern Passcode (for testing)")

        with col2:
            st.markdown("### Job & Cost Details")
            services = st.multiselect("Services Required", ["Screen Replacement", "Battery Replacement", "Charging Port Repair", "Water Damage Diagnostics", "Software Flashing / Unlocking", "Motherboard Soldering", "Speaker / Mic Repair"])
            issue_desc = st.text_area("Fault Symptoms / Customer Description")
            condition = st.text_input("Physical Condition (e.g., cracked back, scratched frame)")
            estimated_cost = st.number_input("Estimated Price ($)", min_value=0.0, step=5.0)

        submitted = st.form_submit_button("📩 Save Repair Ticket")
        
        if submitted:
            if not customer_name or not model:
                st.error("Please fill in the required fields: Customer Name and Model.")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                service_str = ", ".join(services) if services else "General Diagnostic"
                
                c.execute('''
                    INSERT INTO tickets (customer_name, contact_number, brand, model, imei_sn, passcode, services, issue_desc, condition, estimated_cost, status, tech_notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (customer_name, contact_number, brand, model, imei_sn, passcode, service_str, issue_desc, condition, estimated_cost, "Received", "", created_at))
                
                ticket_id = c.lastrowid
                conn.commit()
                conn.close()
                st.success(f"✅ Ticket #{ticket_id} created successfully for {customer_name} ({brand} {model})!")

# ---------------------------------------------------------
# MODULE 3: JOB STATUS & UPDATES
# ---------------------------------------------------------
elif menu == "Job Status & Updates":
    st.subheader("🔍 Search & Update Repair Orders")
    
    conn = sqlite3.connect(DB_FILE)
    df_tickets = pd.read_sql_query("SELECT * FROM tickets", conn)
    conn.close()

    if not df_tickets.empty:
        ticket_list = [f"Ticket #{row['ticket_id']} - {row['customer_name']} ({row['brand']} {row['model']})" for _, row in df_tickets.iterrows()]
        selected_ticket_str = st.selectbox("Select Ticket to View/Edit", ticket_list)
        
        selected_id = int(selected_ticket_str.split("#")[1].split(" ")[0])
        ticket_data = df_tickets[df_tickets['ticket_id'] == selected_id].iloc[0]

        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Customer:** {ticket_data['customer_name']} ({ticket_data['contact_number']})")
            st.write(f"**Device:** {ticket_data['brand']} {ticket_data['model']}")
            st.write(f"**IMEI/SN:** {ticket_data['imei_sn']}")
            st.write(f"**Passcode:** {ticket_data['passcode']}")
            st.write(f"**Services:** {ticket_data['services']}")
            st.write(f"**Symptoms:** {ticket_data['issue_desc']}")

        with col2:
            new_status = st.selectbox("Update Status", ["Received", "Pending Diagnostics", "Awaiting Parts", "In Progress", "Ready for Pickup", "Completed", "Cancelled"], index=["Received", "Pending Diagnostics", "Awaiting Parts", "In Progress", "Ready for Pickup", "Completed", "Cancelled"].index(ticket_data['status']))
            tech_notes = st.text_area("Technician Work Notes", value=ticket_data['tech_notes'])
            
            if st.button("Save Ticket Updates"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("UPDATE tickets SET status=?, tech_notes=? WHERE ticket_id=?", (new_status, tech_notes, selected_id))
                conn.commit()
                conn.close()
                st.success(f"Status for Ticket #{selected_id} updated to '{new_status}'!")
                st.rerun()
    else:
        st.info("No tickets available to update.")

# ---------------------------------------------------------
# MODULE 4: INVENTORY
# ---------------------------------------------------------
elif menu == "Inventory":
    st.subheader("📦 Spare Parts & Components Inventory")
    
    tab1, tab2 = st.tabs(["View Stock", "Add New Part"])
    
    conn = sqlite3.connect(DB_FILE)
    
    with tab1:
        df_inv = pd.read_sql_query("SELECT * FROM inventory", conn)
        if not df_inv.empty:
            st.dataframe(df_inv, use_container_width=True)
        else:
            st.info("No inventory items found.")
            
    with tab2:
        with st.form("add_inv_form", clear_on_submit=True):
            item_name = st.text_input("Item Name (e.g., iPhone 11 LCD Assembly)")
            category = st.selectbox("Category", ["Screens", "Batteries", "Charging Flex", "Camera Modules", "Tools / Consumables", "IC Chips / Components"])
            quantity = st.number_input("Stock Quantity", min_value=1, step=1)
            cost_price = st.number_input("Cost Price ($)", min_value=0.0, step=1.0)
            selling_price = st.number_input("Selling Price ($)", min_value=0.0, step=1.0)
            
            if st.form_submit_button("Add Part to Stock"):
                c = conn.cursor()
                c.execute("INSERT INTO inventory (item_name, category, quantity, cost_price, selling_price) VALUES (?, ?, ?, ?, ?)",
                          (item_name, category, quantity, cost_price, selling_price))
                conn.commit()
                st.success(f"Added {quantity}x {item_name} to inventory!")
                st.rerun()
                
    conn.close()
EOF
