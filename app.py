cat << 'EOF' > app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------
DB_FILE = "servitrack.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Users & Roles Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            full_name TEXT
        )
    ''')
    
    # Repair Work Orders Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            contact_number TEXT,
            email TEXT,
            brand TEXT,
            model TEXT,
            imei_sn TEXT,
            passcode TEXT,
            services TEXT,
            issue_desc TEXT,
            pre_checklist TEXT,
            condition TEXT,
            estimated_cost REAL,
            deposit_paid REAL,
            status TEXT,
            assigned_tech TEXT,
            tech_notes TEXT,
            created_at TEXT
        )
    ''')
    
    # Inventory & Parts Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            category TEXT,
            sku TEXT,
            quantity INTEGER,
            cost_price REAL,
            selling_price REAL
        )
    ''')
    
    # Sales Transactions Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            customer_name TEXT,
            total_amount REAL,
            payment_method TEXT,
            cashier TEXT,
            sale_date TEXT
        )
    ''')
    
    # Insert Default Users if table is empty
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        default_users = [
            ("admin", "admin123", "Admin", "System Administrator"),
            ("tech", "tech123", "Technician", "Lead Hardware Tech"),
            ("desk", "desk123", "Receptionist", "Front Desk Representative")
        ]
        c.executemany("INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)", default_users)

    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# PAGE CONFIGURATION & CUSTOM STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="GlobalRepair POS & ERP", page_icon="📱", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Container */
    .app-header {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 20px 28px;
        border-radius: 12px;
        border: 1px solid #374151;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .app-header h2 {
        color: #f9fafb;
        margin: 0;
        font-weight: 700;
        font-size: 26px;
    }
    .app-header p {
        color: #9ca3af;
        margin: 4px 0 0 0;
        font-size: 13px;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #1f2937;
        border: 1px solid #374151;
        padding: 16px;
        border-radius: 10px;
    }
    div[data-testid="stMetric"] label {
        color: #9ca3af !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
    }

    /* Custom Buttons */
    .stButton>button, .stFormSubmitButton>button {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        padding: 8px 18px;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover {
        background: #1d4ed8;
    }

    /* POS Receipt Box */
    .receipt-box {
        background-color: #ffffff;
        color: #000000;
        padding: 20px;
        font-family: 'Courier New', Courier, monospace;
        border-radius: 6px;
        border: 1px solid #cccccc;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# AUTHENTICATION & SESSION MANAGEMENT
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "full_name" not in st.session_state:
    st.session_state["full_name"] = ""

def login_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, full_name FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

if not st.session_state["authenticated"]:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background-color:#1f2937; padding:25px; border-radius:12px; border:1px solid #374151; text-align:center;">
            <h1 style="color:#f9fafb; margin-bottom:5px;">📱 GlobalRepair POS</h1>
            <p style="color:#9ca3af;">Enterprise Mobile Repair Management System</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.subheader("🔑 User Login")
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In")
            
            if submit:
                user_match = login_user(user_input, pass_input)
                if user_match:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_input
                    st.session_state["role"] = user_match[0]
                    st.session_state["full_name"] = user_match[1]
                    st.success("Authenticated!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")
                    
        st.markdown("""
        <div style="background-color:#111827; padding:12px; border-radius:8px; border:1px dashed #374151; font-size:12px; color:#9ca3af; margin-top:10px;">
            <b>Default Test Credentials:</b><br>
            • Admin: <code>admin</code> / <code>admin123</code><br>
            • Technician: <code>tech</code> / <code>tech123</code><br>
            • Front Desk: <code>desk</code> / <code>desk123</code>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------
# NAVIGATION & HEADER BAR
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(f"👤 **{st.session_state['full_name']}**")
    st.markdown(f"🏷️ Role: `{st.session_state['role']}`")
    if st.button("🚪 Sign Out"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.session_state["role"] = ""
        st.session_state["full_name"] = ""
        st.rerun()
    st.markdown("---")

st.markdown(f"""
<div class="app-header">
    <div>
        <h2>📱 GlobalRepair POS & Service ERP</h2>
        <p>Standard Device Intake • Bench Workflow • Parts Inventory • POS Checkout</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Define Tabs based on User Role permissions
nav_tabs = ["📊 Dashboard", "📝 New Service Intake", "🔧 Repair Bench & Workflow", "🛒 POS Cashier Checkout", "📦 Parts Inventory"]
if st.session_state["role"] == "Admin":
    nav_tabs.append("👥 User Management")

selected_tab = st.tabs(nav_tabs)

# ---------------------------------------------------------
# TAB 1: DASHBOARD OVERVIEW
# ---------------------------------------------------------
with selected_tab[0]:
    conn = sqlite3.connect(DB_FILE)
    df_tickets = pd.read_sql_query("SELECT * FROM tickets", conn)
    df_sales = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()

    total_tickets = len(df_tickets)
    in_repair = len(df_tickets[df_tickets['status'].isin(['Under Diagnostics', 'In Repair'])]) if not df_tickets.empty else 0
    ready_pickup = len(df_tickets[df_tickets['status'] == 'Ready for Pickup']) if not df_tickets.empty else 0
    total_revenue = df_sales['total_amount'].sum() if not df_sales.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tickets Logged", total_tickets)
    c2.metric("Active Bench Work", in_repair)
    c3.metric("Ready for Pickup", ready_pickup)
    c4.metric("Total Revenue ($)", f"${total_revenue:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Active Work Orders")
    if not df_tickets.empty:
        st.dataframe(
            df_tickets[['ticket_id', 'customer_name', 'brand', 'model', 'status', 'assigned_tech', 'estimated_cost', 'created_at']]
            .sort_values(by='ticket_id', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No work orders registered.")

# ---------------------------------------------------------
# TAB 2: NEW SERVICE INTAKE
# ---------------------------------------------------------
with selected_tab[1]:
    st.subheader("📝 Customer & Device Intake Form")
    
    with st.form("intake_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 👤 Customer Profile")
            c_name = st.text_input("Customer Full Name *")
            c_phone = st.text_input("Contact Phone Number *")
            c_email = st.text_input("Email Address")

            st.markdown("##### 📱 Hardware Details")
            brand = st.selectbox("Brand", ["Apple iPhone", "Samsung", "Xiaomi / Redmi", "Tecno / Infinix", "OPPO / Vivo", "Google Pixel", "Motorola", "Other"])
            model = st.text_input("Device Model (e.g., iPhone 13 Pro, Galaxy S22) *")
            imei = st.text_input("IMEI / Serial Number")
            passcode = st.text_input("Screen Lock PIN / Pattern Code")

        with col2:
            st.markdown("##### 🛠️ Diagnostics & Services Required")
            services = st.multiselect("Standard Services", [
                "Screen Replacement", "Battery Replacement", "Charging Port Repair",
                "Water Damage Diagnostics", "Software Flashing / FRP Removal",
                "Logic Board Soldering / Micro-repair", "Camera Module Repair", "Back Glass Replacement"
            ])
            issue = st.text_area("Customer Stated Issue / Symptoms")
            
            st.markdown("##### 🔍 Pre-Repair Diagnostic Checklist")
            chk_power = st.checkbox("Device Powers On", value=True)
            chk_display = st.checkbox("Touch Screen Functional", value=True)
            chk_cameras = st.checkbox("Front/Rear Cameras Working", value=True)
            chk_wifi = st.checkbox("Wi-Fi & Cellular Signal OK", value=True)
            chk_biometrics = st.checkbox("FaceID / TouchID Operational", value=True)
            
            st.markdown("##### 💰 Commercial Estimates")
            est_cost = st.number_input("Estimated Total Price ($)", min_value=0.0, step=5.0)
            dep_paid = st.number_input("Advance Deposit Paid ($)", min_value=0.0, step=5.0)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Register & Print Intake Ticket"):
            if not c_name or not model or not c_phone:
                st.error("Missing mandatory fields: Customer Name, Phone Number, and Device Model.")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                service_str = ", ".join(services) if services else "General Assessment"
                
                checklist_summary = f"Power:{chk_power} | Touch:{chk_display} | Cam:{chk_cameras} | Net:{chk_wifi} | Bio:{chk_biometrics}"
                
                c.execute('''
                    INSERT INTO tickets (customer_name, contact_number, email, brand, model, imei_sn, passcode, services, issue_desc, pre_checklist, condition, estimated_cost, deposit_paid, status, assigned_tech, tech_notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (c_name, c_phone, c_email, brand, model, imei, passcode, service_str, issue, checklist_summary, "Received at desk", est_cost, dep_paid, "Intake Registered", "Unassigned", "", created_at))
                
                ticket_id = c.lastrowid
                conn.commit()
                conn.close()
                st.success(f"Work Order #{ticket_id} created for {c_name} ({brand} {model})!")

# ---------------------------------------------------------
# TAB 3: BENCH WORKFLOW & DIAGNOSTICS
# ---------------------------------------------------------
with selected_tab[2]:
    st.subheader("🔧 Technician Bench & Workflow Management")
    
    conn = sqlite3.connect(DB_FILE)
    df_tickets = pd.read_sql_query("SELECT * FROM tickets", conn)
    df_users = pd.read_sql_query("SELECT full_name FROM users WHERE role IN ('Admin', 'Technician')", conn)
    conn.close()

    if not df_tickets.empty:
        ticket_opts = [f"Ticket #{row['ticket_id']} - {row['customer_name']} | {row['brand']} {row['model']} [{row['status']}]" for _, row in df_tickets.iterrows()]
        selected_ticket_str = st.selectbox("Select Active Repair Ticket", ticket_opts)
        
        selected_id = int(selected_ticket_str.split("#")[1].split(" ")[0])
        ticket = df_tickets[df_tickets['ticket_id'] == selected_id].iloc[0]

        st.markdown("---")
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.markdown("#### 📄 Device Specs & Intake State")
            st.write(f"**Customer:** {ticket['customer_name']} ({ticket['contact_number']})")
            st.write(f"**Hardware:** {ticket['brand']} {ticket['model']}")
            st.write(f"**IMEI / SN:** `{ticket['imei_sn'] if ticket['imei_sn'] else 'N/A'}`")
            st.write(f"**Unlock Passcode:** `{ticket['passcode'] if ticket['passcode'] else 'N/A'}`")
            st.write(f"**Requested Services:** {ticket['services']}")
            st.write(f"**Fault Description:** {ticket['issue_desc']}")
            st.write(f"**Pre-Intake Checks:** {ticket['pre_checklist']}")
            st.write(f"**Financial Status:** Est: ${ticket['estimated_cost']:.2f} \vert{} Deposit:${ticket['deposit_paid']:.2f}")

        with col_right:
            st.markdown("#### 🛠️ Tech Actions & Updates")
            
            statuses = [
                "Intake Registered", "Under Diagnostics", "Awaiting Parts", 
                "In Repair", "Quality Control Passed", "Ready for Pickup", 
                "Collected & Closed", "Cancelled"
            ]
            current_idx = statuses.index(ticket['status']) if ticket['status'] in statuses else 0
            
            new_status = st.selectbox("Update Repair Status", statuses, index=current_idx)
            
            tech_list = df_users['full_name'].tolist() if not df_users.empty else ["Lead Tech"]
            assigned_tech = st.selectbox("Assign Lead Technician", tech_list, index=0)
            
            tech_notes = st.text_area("Technician Diagnostic & Repair Notes", value=ticket['tech_notes'])
            
            if st.button("Save Ticket Updates"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("UPDATE tickets SET status=?, assigned_tech=?, tech_notes=? WHERE ticket_id=?", (new_status, assigned_tech, tech_notes, selected_id))
                conn.commit()
                conn.close()
                st.success(f"Ticket #{selected_id} status updated to '{new_status}'!")
                st.rerun()
    else:
        st.info("No active tickets found.")

# ---------------------------------------------------------
# TAB 4: POINT OF SALE (POS) CASHIER CHECKOUT
# ---------------------------------------------------------
with selected_tab[3]:
    st.subheader("🛒 POS Cashier Checkout & Billing")
    
    conn = sqlite3.connect(DB_FILE)
    df_tickets = pd.read_sql_query("SELECT * FROM tickets WHERE status != 'Collected & Closed'", conn)
    df_parts = pd.read_sql_query("SELECT * FROM inventory WHERE quantity > 0", conn)
    conn.close()

    col_pos1, col_pos2 = st.columns([1.2, 1])

    with col_pos1:
        st.markdown("##### 1. Select Ticket or Sale Items")
        checkout_type = st.radio("Transaction Type", ["Repair Ticket Payment", "Direct Parts / Retail Sale"], horizontal=True)

        total_due = 0.0
        customer_ref = "Walk-in Customer"
        ticket_ref_id = None

        if checkout_type == "Repair Ticket Payment":
            if not df_tickets.empty:
                t_opts = [f"#{row['ticket_id']} - {row['customer_name']} ({row['brand']} {row['model']}) - Due: ${row['estimated_cost'] - row['deposit_paid']:.2f}" for _, row in df_tickets.iterrows()]
                sel_t = st.selectbox("Select Repair Ticket to Checkout", t_opts)
                
                t_id = int(sel_t.split("#")[1].split(" ")[0])
                t_row = df_tickets[df_tickets['ticket_id'] == t_id].iloc[0]
                
                ticket_ref_id = t_id
                customer_ref = t_row['customer_name']
                balance_due = t_row['estimated_cost'] - t_row['deposit_paid']
                
                st.info(f"Total Estimate: ${t_row['estimated_cost']:.2f} \vert{} Deposit Paid:${t_row['deposit_paid']:.2f}")
                total_due = st.number_input("Final Amount to Charge ($)", min_value=0.0, value=float(balance_due))
            else:
                st.warning("No pending repair tickets available for checkout.")
        else:
            customer_ref = st.text_input("Customer Name", value="Walk-in Customer")
            if not df_parts.empty:
                part_opts = [f"{row['item_name']} - ${row['selling_price']:.2f} (Stock: {row['quantity']})" for _, row in df_parts.iterrows()]
                sel_p = st.selectbox("Select Item / Accessory", part_opts)
                p_qty = st.number_input("Quantity", min_value=1, value=1)
                
                p_idx = part_opts.index(sel_p)
                p_row = df_parts.iloc[p_idx]
                total_due = p_row['selling_price'] * p_qty
            else:
                st.warning("No parts or accessories in stock.")

    with col_pos2:
        st.markdown("##### 2. Payment & Receipt")
        payment_method = st.selectbox("Payment Method", ["Cash", "Credit Card", "Mobile Money / Transfer", "Split Payment"])
        
        if st.button("Complete Transaction & Print Receipt"):
            if total_due >= 0:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                c.execute("INSERT INTO sales (ticket_id, customer_name, total_amount, payment_method, cashier, sale_date) VALUES (?, ?, ?, ?, ?, ?)",
                          (ticket_ref_id, customer_ref, total_due, payment_method, st.session_state['full_name'], now_str))
                
                if ticket_ref_id:
                    c.execute("UPDATE tickets SET status='Collected & Closed' WHERE ticket_id=?", (ticket_ref_id,))
                
                conn.commit()
                conn.close()
                
                st.success("Transaction completed successfully!")
                
                st.markdown(f"""
                <div class="receipt-box">
                    <h3 style="text-align:center; margin:0;">GLOBAL REPAIR SERVICES</h3>
                    <p style="text-align:center; margin:2px;">Official Sales Receipt</p>
                    <hr>
                    <p><b>Date:</b> {now_str}<br>
                    <b>Cashier:</b> {st.session_state['full_name']}<br>
                    <b>Customer:</b> {customer_ref}</p>
                    <hr>
                    <p><b>Total Paid:</b> ${total_due:,.2f}<br>
                    <b>Payment Method:</b> {payment_method}</p>
                    <hr>
                    <p style="text-align:center;">Thank you for your business!<br>30 Days Warranty on Repairs</p>
                </div>
                """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 5: PARTS & COMPONENT INVENTORY
# ---------------------------------------------------------
with selected_tab[4]:
    st.subheader("📦 Spare Parts & Components Inventory")
    
    sub1, sub2 = st.tabs(["Stock Catalog", "Add New Stock Item"])
    conn = sqlite3.connect(DB_FILE)
    
    with sub1:
        df_inv = pd.read_sql_query("SELECT * FROM inventory", conn)
        if not df_inv.empty:
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
        else:
            st.info("Inventory catalog is currently empty.")
            
    with sub2:
        with st.form("add_stock_form", clear_on_submit=True):
            i_name = st.text_input("Part Name (e.g., iPhone 12 OLED Display Assembly)")
            i_cat = st.selectbox("Category", ["Displays & Touch", "Batteries", "Charging Ports", "Cameras", "Logic Board ICs", "Accessories / Retail"])
            i_sku = st.text_input("SKU / Barcode Number")
            i_qty = st.number_input("Quantity Received", min_value=1, value=1)
            i_cost = st.number_input("Unit Wholesale Cost ($)", min_value=0.0, step=1.0)
            i_sell = st.number_input("Retail / Selling Price ($)", min_value=0.0, step=1.0)
            
            if st.form_submit_button("Add Item to Stock"):
                c = conn.cursor()
                c.execute("INSERT INTO inventory (item_name, category, sku, quantity, cost_price, selling_price) VALUES (?, ?, ?, ?, ?, ?)",
                          (i_name, i_cat, i_sku, i_qty, i_cost, i_sell))
                conn.commit()
                st.success(f"Added {i_qty}x {i_name} to inventory!")
                st.rerun()
    conn.close()

# ---------------------------------------------------------
# TAB 6: ADMIN USER MANAGEMENT (ADMIN ONLY)
# ---------------------------------------------------------
if st.session_state["role"] == "Admin":
    with selected_tab[5]:
        st.subheader("👥 System User Accounts & Roles")
        
        conn = sqlite3.connect(DB_FILE)
        df_u = pd.read_sql_query("SELECT user_id, username, role, full_name FROM users", conn)
        st.dataframe(df_u, use_container_width=True, hide_index=True)
        
        with st.form("add_user_form", clear_on_submit=True):
            st.markdown("##### Create New User Account")
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            new_name = st.text_input("Full Employee Name")
            new_role = st.selectbox("System Role", ["Admin", "Technician", "Receptionist"])
            
            if st.form_submit_button("Create System User"):
                if new_user and new_pass:
                    try:
                        c = conn.cursor()
                        c.execute("INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                                  (new_user, new_pass, new_role, new_name))
                        conn.commit()
                        st.success(f"User account '{new_user}' created!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username already exists!")
                else:
                    st.error("Please fill in both Username and Password.")
        conn.close()
EOF
