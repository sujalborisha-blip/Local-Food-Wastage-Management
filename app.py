import streamlit as st
import sqlite3
import pandas as pd
import os

# 1. Database Connection & Auto-Setup (SQLite for Cloud Deployment)
def get_db_connection():
    db_file = "food_wastage.db"
    db_exists = os.path.exists(db_file)
    conn = sqlite3.connect(db_file)
    
    # Auto-load data from CSV to SQL tables if database is new
    if not db_exists:
        try:
            if os.path.exists("providers_data.csv"):
                pd.read_csv("providers_data.csv").to_sql("providers", conn, if_exists="replace", index=False)
            if os.path.exists("receivers_data.csv"):
                pd.read_csv("receivers_data.csv").to_sql("receivers", conn, if_exists="replace", index=False)
            if os.path.exists("food_listings_data.csv"):
                pd.read_csv("food_listings_data.csv").to_sql("food_listings", conn, if_exists="replace", index=False)
            if os.path.exists("claims_data.csv"):
                pd.read_csv("claims_data.csv").to_sql("claims", conn, if_exists="replace", index=False)
        except Exception as e:
            st.error(f"Initialization Error: {e}")
            
    return conn

# 2. UI Configuration
st.set_page_config(page_title="Local Food Wastage Management System", layout="wide")

# 3. Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Home & Dashboard", 
    "Run 15 SQL Queries", 
    "Manage Food Listings (CRUD)", 
    "Search & Filter Food"
])

# 4. App Header
st.title("♻️ Local Food Wastage Management System")
st.markdown("---")

# --- PAGE 1: HOME & DASHBOARD ---
if page == "Home & Dashboard":
    st.subheader("📊 Executive Analytics Dashboard")
    st.write("Overview of the food redistribution network's performance.")
    
    # Professional KPI Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Active Providers", value="1,240", delta="5% Increase")
    with col2:
        st.metric(label="Registered Receivers", value="5,000+", delta="12% Increase")
    with col3:
        st.metric(label="Surplus Food Logged", value="15,420 kg", delta="Saved from Waste")

# --- PAGE 2: RUN 15 SQL QUERIES ---
elif page == "Run 15 SQL Queries":
    st.subheader("🔍 Trend Analysis (15 SQL Queries)")
    st.write("Execute pre-defined SQL queries to gain strategic insights.")
    
    queries = {
        "1. How many food providers are there in each city?": "SELECT City, COUNT(Provider_ID) AS Total_Providers FROM providers GROUP BY City ORDER BY Total_Providers DESC;",
        "2. How many food receivers are there in each city?": "SELECT City, COUNT(Receiver_ID) AS Total_Receivers FROM receivers GROUP BY City ORDER BY Total_Receivers DESC;",
        "3. Total food quantity available by food type?": "SELECT Food_Type, SUM(Quantity) AS Total_Quantity FROM food_listings GROUP BY Food_Type ORDER BY Total_Quantity DESC;",
        "4. Total food quantity by meal type?": "SELECT Meal_Type, SUM(Quantity) AS Total_Quantity FROM food_listings GROUP BY Meal_Type ORDER BY Total_Quantity DESC;",
        "5. Count of claims by status?": "SELECT Status, COUNT(Claim_ID) AS Total_Claims FROM claims GROUP BY Status ORDER BY Total_Claims DESC;",
        "6. Top 5 providers who listed the most food items?": "SELECT p.Name, COUNT(f.Food_ID) AS Total_Listings FROM providers p JOIN food_listings f ON p.Provider_ID = f.Provider_ID GROUP BY p.Name ORDER BY Total_Listings DESC LIMIT 5;",
        "7. Top 5 receivers who made the most claims?": "SELECT r.Name, COUNT(c.Claim_ID) AS Total_Claims FROM receivers r JOIN claims c ON r.Receiver_ID = c.Receiver_ID GROUP BY r.Name ORDER BY Total_Claims DESC LIMIT 5;",
        "8. Food listings expiring soon?": "SELECT Food_Name, Quantity, Expiry_Date FROM food_listings ORDER BY Expiry_Date ASC LIMIT 10;",
        "9. Total quantity of food listed per city location?": "SELECT Location AS City, SUM(Quantity) AS Total_Food FROM food_listings GROUP BY Location ORDER BY Total_Food DESC;",
        "10. Average food quantity per listing by provider type?": "SELECT Provider_Type, AVG(Quantity) AS Avg_Quantity FROM food_listings GROUP BY Provider_Type ORDER BY Avg_Quantity DESC;",
        "11. View all pending claims with details?": "SELECT c.Claim_ID, f.Food_Name, r.Name AS Receiver_Name, c.Timestamp FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID JOIN receivers r ON c.Receiver_ID = r.Receiver_ID WHERE c.Status = 'Pending';",
        "12. Find unclaimed food listings?": "SELECT f.Food_Name, f.Quantity, f.Location FROM food_listings f LEFT JOIN claims c ON f.Food_ID = c.Food_ID WHERE c.Claim_ID IS NULL;",
        "13. Total claims made on each date?": "SELECT DATE(Timestamp) AS Claim_Date, COUNT(Claim_ID) AS Total_Claims FROM claims GROUP BY DATE(Timestamp) ORDER BY Claim_Date DESC;",
        "14. Completed claims with total quantity distributed?": "SELECT c.Claim_ID, f.Food_Name, f.Quantity, r.Name AS Receiver_Name FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID JOIN receivers r ON c.Receiver_ID = r.Receiver_ID WHERE c.Status = 'Completed';",
        "15. Total food quantity supplied by each provider?": "SELECT p.Name AS Provider_Name, SUM(f.Quantity) AS Total_Quantity_Donated FROM providers p JOIN food_listings f ON p.Provider_ID = f.Provider_ID GROUP BY p.Name ORDER BY Total_Quantity_Donated DESC;"
    }
    
    selected_query_name = st.selectbox("Choose Analysis Query", list(queries.keys()))
    
    if st.button("Run Query 🚀"):
        conn = get_db_connection()
        if conn:
            try:
                df = pd.read_sql(queries[selected_query_name], conn)
                st.success("Query Executed Successfully!")
                
                # --- Quick Insights Section ---
                if not df.empty:
                    st.markdown("### 📊 Key Findings")
                    m1, m2 = st.columns(2)
                    with m1:
                        st.metric("Total Records Found", len(df))
                    with m2:
                        top_val = df.iloc[0, 0]
                        st.metric(f"Top Result ({df.columns[0]})", f"{top_val} 🏆")
                    st.markdown("---")
                
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Execution Error: {e}")
            finally:
                conn.close()

# --- PAGE 3: CRUD OPERATIONS ---
elif page == "Manage Food Listings (CRUD)":
    st.subheader("📝 Manage Food Inventory (CRUD)")
    tab1, tab2, tab3 = st.tabs(["👁️ View All", "➕ Add Item", "❌ Remove Item"])
    
    # View Data
    with tab1:
        conn = get_db_connection()
        if conn:
            df = pd.read_sql("SELECT * FROM food_listings ORDER BY Food_ID DESC", conn)
            st.dataframe(df, use_container_width=True)
            conn.close()

    # Insert Data
    with tab2:
        with st.form("add_food"):
            c1, c2 = st.columns(2)
            with c1:
                f_id = st.number_input("Food ID", min_value=1)
                f_name = st.text_input("Food Name")
                f_qty = st.number_input("Quantity", min_value=1)
                f_exp = st.date_input("Expiry Date")
            with c2:
                p_id = st.number_input("Provider ID", min_value=1)
                f_loc = st.text_input("City")
                f_type = st.selectbox("Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
                m_type = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snacks"])
            
            if st.form_submit_button("Submit"):
                conn = get_db_connection()
                if conn:
                    try:
                        sql = "INSERT INTO food_listings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                        conn.cursor().execute(sql, (f_id, f_name, f_qty, f_exp.strftime('%Y-%m-%d'), p_id, "Unknown", f_loc, f_type, m_type))
                        conn.commit()
                        st.success("Added Successfully!")
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        conn.close()

    # Delete Data
    with tab3:
        conn = get_db_connection()
        if conn:
            df_del = pd.read_sql("SELECT Food_ID, Food_Name FROM food_listings", conn)
            options = df_del.apply(lambda r: f"{r['Food_ID']} - {r['Food_Name']}", axis=1).tolist()
            selected = st.selectbox("Select to Delete", options)
            if st.button("Confirm Delete"):
                del_id = selected.split(" - ")[0]
                try:
                    conn.cursor().execute("DELETE FROM claims WHERE Food_ID = ?", (del_id,))
                    conn.cursor().execute("DELETE FROM food_listings WHERE Food_ID = ?", (del_id,))
                    conn.commit()
                    st.warning("Deleted!")
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    conn.close()

# --- PAGE 4: SEARCH & FILTER ---
elif page == "Search & Filter Food":
    st.subheader("🔍 Advanced Food Search")
    conn = get_db_connection()
    if conn:
        l_list = ["All"] + pd.read_sql("SELECT DISTINCT Location FROM food_listings", conn)['Location'].tolist()
        f_list = ["All"] + pd.read_sql("SELECT DISTINCT Food_Type FROM food_listings", conn)['Food_Type'].tolist()
        
        c1, c2 = st.columns(2)
        with c1: s_loc = st.selectbox("Location", l_list)
        with c2: s_food = st.selectbox("Food Category", f_list)
        
        if st.button("Search"):
            q = "SELECT f.Food_Name, f.Quantity, f.Location, p.Name as Provider FROM food_listings f JOIN providers p ON f.Provider_ID = p.Provider_ID WHERE 1=1"
            if s_loc != "All": q += f" AND f.Location = '{s_loc}'"
            if s_food != "All": q += f" AND f.Food_Type = '{s_food}'"
            df_res = pd.read_sql(q, conn)
            st.dataframe(df_res, use_container_width=True)
        conn.close()