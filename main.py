import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from st_aggrid import AgGrid, GridOptionsBuilder
import logging

# log queries
logging.basicConfig(level=logging.INFO, filename='migration.log', filemode='w')

# SQL queries on a DataFrame using SQLAlchemy
def run_query(query, df):
    engine = create_engine('sqlite://', echo=False)
    df.to_sql('data', con=engine, index=False, if_exists='replace')
    result = pd.read_sql_query(text(query), con=engine)
    return result

# Cache the data
@st.cache_data
def load_csv_data(file):
    return pd.read_csv(file)

@st.cache_data
def load_excel_data(file, sheet_name):
    return pd.read_excel(file, sheet_name=sheet_name)

def main():
    st.set_page_config(page_title="Data Dashboard", layout="wide", initial_sidebar_state="expanded")
    st.title("Data Processing Dashboard")
    
    st.markdown("### 1. Upload your Data File")
    uploaded_file = st.file_uploader("Upload your CSV or Excel data", type=["csv", "xlsx", "xls"])

    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1]
        
        if file_type == 'csv':
            df = load_csv_data(uploaded_file)
        elif file_type in ['xlsx', 'xls']:
            sheets = pd.ExcelFile(uploaded_file).sheet_names
            selected_sheet = st.selectbox("Select a sheet", sheets, index=0)
            df = load_excel_data(uploaded_file, selected_sheet)

        # Data preprocessing
        with st.expander("Data Preprocessing Options"):
            if st.checkbox("Handle missing data"):
                option = st.selectbox("Choose a method", ("Drop rows with missing values", "Fill missing values"))
                if option == "Drop rows with missing values":
                    df = df.dropna()
                elif option == "Fill missing values":
                    fill_value = st.text_input("Enter fill value:")
                    df = df.fillna(fill_value)
                st.write("Updated Data Preview:")
                st.write(df.head())

        # Data Table
        st.markdown("### 2. Data Overview")
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True)
        gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        gridOptions = gb.build()
        grid_response = AgGrid(df, gridOptions=gridOptions, update_mode='MODEL_CHANGED', theme='streamlit')
        selected_rows = grid_response['selected_rows']

        st.write("Selected Rows")
        st.write(pd.DataFrame(selected_rows))

        # SQL query input
        st.markdown("### 3. SQL Query Execution")
        query = st.text_area("Enter your SQL query here")

        if st.button("Run Query", help="Click to execute the SQL query"):
            try:
                with st.spinner('Running query...'):
                    result = run_query(query, df)
                st.success("Query executed successfully!")
                st.write(result)
            except Exception as e:
                st.error(f"Query failed: {e}")
                logging.error(f"Query failed: {query}. Error: {e}")

        # Export
        st.markdown("### 4. Export Data")
        if st.button("Export Data"):
            export_format = st.selectbox("Select export format", ["CSV", "Excel"])
            if export_format == "CSV":
                df.to_csv("exported_data.csv", index=False)
                st.success("Data exported as CSV successfully.")
            elif export_format == "Excel":
                df.to_excel("exported_data.xlsx", index=False)
                st.success("Data exported as Excel successfully.")

if __name__ == "__main__":
    main()
