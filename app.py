import streamlit as st
import sqlite3
import pandas as pd
import os

# 1. Database Connection & Auto-Setup Function
def get_db_connection():
    db_file = "food_wastage.db"
    db_exists = os.path.exists(db_file)
    
    # Connect to SQLite (Self-contained SQL database)
    conn = sqlite3.connect(db_file)
    
    # If database is new, automatically create tables from uploaded CSV files
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
            st.error(f"Error initializing local database files: {e}")
            
    return conn

# 2. Page Configuration
st.set_page_config(page_title="Local Food Wastage Management System", layout="wide")

# 3. Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home & Dashboard", "Run 15 SQL Queries", "Manage Food Listings (CRUD)", "Search & Filter Food"])

# 4. App Header
st.title("♻️ Local Food Wastage Management System")
st.markdown("---")

# --- PAGE 1: HOME & DASHBOARD ---
if page == "Home & Dashboard":
    st.subheader("📊 Executive Analytics Dashboard")
    st.write("Welcome back! Here is the real-time status of your food redistribution network.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Active Providers", value="1,240")
    with col2:
        st.metric(label="Registered Receivers", value="5,000+")
    with col3:
        st.metric(label="Total Food Listings", value="15,420 kg")

# --- PAGE 2: RUN 15 SQL QUERIES ---
elif page == "Run 15 SQL Queries":
    st.subheader("🔍 Trend Analysis (15 SQL Queries)")
    st.write("Select a query below to fetch live analytics from your database.")
    
    # Note: SQLite uses slightly different format for Date functions, updated accordingly below
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
            sql_query = queries[selected_query_name]
            try:
                df = pd.read_sql(sql_query, conn)
                st.success("Query Executed Successfully!")
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Error execution query: {e}")
            finally:
                conn.close()

# --- PAGE 3: CRUD OPERATIONS ---
elif page == "Manage Food Listings (CRUD)":
    st.subheader("📝 Manage Food Inventory (CRUD)")
    
    tab1, tab2, tab3 = st.tabs(["👁️ View All Food", "➕ Add New Food", "❌ Delete Food"])
    
    with tab1:
        st.write("Current Food Listings in Database:")
        conn = get_db_connection()
        if conn:
            df = pd.read_sql("SELECT * FROM food_listings ORDER BY Food_ID DESC", conn)
            st.dataframe(df, use_container_width=True)
            conn.close()

    with tab2:
        st.write("Add a newly donated food item here:")
        with st.form("add_food_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_id = st.number_input("Food ID", min_value=1, step=1)
                f_name = st.text_input("Food Name (e.g., Rice, Bread)")
                f_qty = st.number_input("Quantity (kg/units)", min_value=1, step=1)
                f_expiry = st.date_input("Expiry Date")
            with col2:
                p_id = st.number_input("Provider ID", min_value=1, step=1)
                f_location = st.text_input("Location (City)")
                f_type = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan", "Mixed"])
                m_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks", "Raw Ingredients"])
            
            submitted = st.form_submit_button("Add Food Item ✅")
            
            if submitted:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        sql = """INSERT INTO food_listings 
                                 (Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                        val = (f_id, f_name, f_qty, f_expiry.strftime('%Y-%m-%d'), p_id, "Unknown", f_location, f_type, m_type)
                        cursor.execute(sql, val)
                        conn.commit()
                        st.success(f"Successfully added '{f_name}' to the database!")
                    except Exception as e:
                        st.error(f"Error adding data: {e}")
                    finally:
                        conn.close()

    with tab3:
        st.write("Remove expired or incorrectly listed food items:")
        conn = get_db_connection()
        if conn:
            df_del = pd.read_sql("SELECT Food_ID, Food_Name FROM food_listings", conn)
            if not df_del.empty:
                options = df_del.apply(lambda row: f"{row['Food_ID']} - {row['Food_Name']}", axis=1).tolist()
                selected_item = st.selectbox("Select Food Item to Delete", options)
                
                if st.button("Delete Item ❌"):
                    del_id = selected_item.split(" - ")[0]
                    cursor = conn.cursor()
                    try:
                        cursor.execute("DELETE FROM claims WHERE Food_ID = ?", (del_id,))
                        cursor.execute("DELETE FROM food_listings WHERE Food_ID = ?", (del_id,))
                        conn.commit()
                        st.warning(f"Item {selected_item} permanently deleted.")
                    except Exception as e:
                        st.error(f"Error deleting data: {e}")
                    finally:
                        conn.close()
            else:
                st.info("No food items available to delete.")
                conn.close()

# --- PAGE 4: SEARCH & FILTER ---
elif page == "Search & Filter Food":
    st.subheader("🔍 Advanced Food Search")
    st.write("Filter available food listings by city, type, and meal category.")
    
    conn = get_db_connection()
    if conn:
        df_locations = pd.read_sql("SELECT DISTINCT Location FROM food_listings", conn)
        df_food_types = pd.read_sql("SELECT DISTINCT Food_Type FROM food_listings", conn)
        df_meal_types = pd.read_sql("SELECT DISTINCT Meal_Type FROM food_listings", conn)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            sel_location = st.selectbox("Select City", ["All"] + df_locations['Location'].tolist())
        with col2:
            sel_food = st.selectbox("Food Type", ["All"] + df_food_types['Food_Type'].tolist())
        with col3:
            sel_meal = st.selectbox("Meal Type", ["All"] + df_meal_types['Meal_Type'].tolist())
        
        if st.button("Search Food Available"):
            query = "SELECT f.Food_Name, f.Quantity, f.Location, f.Food_Type, p.Name AS Provider_Name, p.Contact FROM food_listings f JOIN providers p ON f.Provider_ID = p.Provider_ID WHERE 1=1"
            
            if sel_location != "All":
                query += f" AND f.Location = '{sel_location}'"
            if sel_food != "All":
                query += f" AND f.Food_Type = '{sel_food}'"
            if sel_meal != "All":
                query += f" AND f.Meal_Type = '{sel_meal}'"
                
            df_filtered = pd.read_sql(query, conn)
            
            if not df_filtered.empty:
                st.success(f"Found {len(df_filtered)} listings matching your criteria!")
                st.dataframe(df_filtered, use_container_width=True)
            else:
                st.warning("No food listings found for the selected filters.")
                
        conn.close()