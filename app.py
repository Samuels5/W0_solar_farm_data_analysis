from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="practice for streamlit", page_icon="📊", layout="wide")

st.title("Practice for Streamlit")

st.write(" i did this with only python")

st.sidebar.header(" this is header")

uploaded = st.sidebar.file_uploader("upload a csv file", type=["csv"])

df = pd.read_csv(uploaded) if uploaded else pd.DataFrame()


st.dataframe(df.head(), use_container_width=True)

st.subheader('Shape')

st.write('Rows:', df.shape[0], 'Columns:', df.shape[1])

numeric_cols = df.select_dtypes(include='number').columns.tolist()
if len(numeric_cols) > 0:
    chosen = st.selectbox('Pick a numeric column', numeric_cols)
    # st.line_chart(df[chosen])
else:
    st.write("No numeric columns found in the uploaded file.")
st.warning('Please upload a CSV to start.')
