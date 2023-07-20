import easyocr as ocr
import streamlit as st
from PIL import Image
import pandas as pd
import numpy as np
import base64
import re
import mysql.connector
from mysql.connector.errors import Error

mydb = mysql.connector.connect(**st.secrets["mysql"])
cursor = mydb.cursor()

@st.cache_data
def load_model(): 
    reader = ocr.Reader(['en'])
    return reader

def convertToBinaryData(image):
    # Convert digital data to binary data
    image_data = image.read()
    encoded_image = base64.b64encode(image_data).decode() # Convert to base64 encoded string
    return encoded_image

def get_data_from_result_text(result_text):
    phone = []
    company = []
    for string in enumerate(result_text):
        flag = 0
        #extracting name from result_text
        if string[1] == result_text[0] and not re.search(r"[0-9]",string[1]): 
            name = string[1]
            flag = 1
        #extracting designation from result_text
        elif string[1] == result_text[1] and not re.search(r"[0-9]",string[1]):
            design = string[1]
            flag = 1
        #extracting phone number from result_text
        elif re.search(r'(?:ph|phone|phno)?\s*(?:[+-]?\d\s*[\(\)]*){7,}', string[1]) and len(re.findall(r'\d', string[1])) > 7: 
            phone.append(string[1])
            flag = 1
        #extracting email id from result_text
        elif re.search(r"@",string[1].lower()): 
            email = string[1].lower()
            flag = 1
        #extracting website from result_text
        elif re.search(r"(www|.*com$)",string[1].lower()) and not re.search(r"@",string[1].lower()): 
            website = string[1].lower()
            flag = 1
        #extracting area from result_text
        elif re.search(r"[0-9] [a-zA-Z]+",string[1]): 
            area = string[1].split(",")[0]
            flag = 1
        #extracting city from result_text
        if re.search(r".+St , ([a-zA-Z]+).+",string[1]):
            city = string[1].split(",")[1]
            flag = 1
        elif re.search(r".+St,, ([a-zA-Z]+).+",string[1]):
            city = (string[1].split(",,")[1]).split(",")[0]
            flag = 1
        elif re.search(r"[a-zA-Z]+,", string[1]):
            city = string[1].rstrip(",")
            flag = 1
        #extracting state from result_text
        if re.search(r".+St , ([a-zA-Z]+).+, ([a-zA-Z]+)",string[1]):
            state = string[1].split(",")[2]
            flag = 1
        if re.search(r".+St,, ([a-zA-Z]+).+",string[1]):
            state = (string[1].split(",,")[1]).split(",")[1]
            flag = 1
        elif re.search(r"([a-zA-Z]+) \d{6}",string[1]):
            state = string[1].split(" ")[0]
            flag = 1
        #extracting pincode from result_text
        if re.search(r"([a-zA-Z]+) \d{6}",string[1]):
            pincode = string[1].split(" ")[1]
            flag = 1
        elif re.search(r"\d{6}",string[1]):
            pincode = string[1]
            flag = 1
        if flag == 0 and re.search(r"([a-zA-Z]+)([a-zA-Z]+)",string[1]):
            if len(company) <= 1:
                company.append(string[1])                       

    if len(phone) > 1:
        phone = ",".join(phone)
        phone = phone.strip("[]")
    else:
        phone = str(*phone)
    if len(company) > 1:
        company = " ".join(company)
        company = company.strip('[]')
    else:
        company = str(company)
        company = company.strip('[]')  

    data = [company,name,design,phone,email,website,area,city,state,pincode]

    return data

def get_dataframe(data,img):
    #creating dataframe to show extracted data in tabular format and store in mysql
    df = pd.DataFrame([data], columns = ["company","name","designation","phone","email","website","area","city","state","pincode"])
    img_df = pd.DataFrame([img], columns = ['image'])
    df = pd.concat([df,img_df], axis = 1) 

    return df

def load_into_mysql(df1):
    # Connect to MySQL
    cols = ",".join([str(i) for i in df1.columns.tolist()])
    try:
        for i,row in df1.iterrows():
            sql = "INSERT INTO bizcardx (" +cols + ") VALUES (" + "%s,"*(len(row)-1) + "%s)"
            cursor.execute(sql, tuple(row))

            # the connection is not autocommitted by default, so we must commit to save our changes
            mydb.commit()
        st.success("Business card Data loaded in Database")
    except mysql.connector.Error:
        st.error("Error occurred while inserting data")

st.set_page_config(layout="wide", page_title="Business card Extraction")
st.markdown(f""" <style>.stApp {{
                    background: url("https://images.pexels.com/photos/3255761/pexels-photo-3255761.jpeg");
                    background-size: cover}}
                    </style>""",unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: blue;'>Extracting Business Card Data with OCR</h1>", unsafe_allow_html=True)
tab1,tab2 = st.tabs(["Extract card and Load into MySQL","Update & Delete card details"])
with tab1:
    col1,col2 = st.columns(2)
    with col1:
        image = st.file_uploader("Choose a file:", type = ['jpg','jpeg','png'])
        
    
    if image is not None:
        with st.spinner("In progress..."):
            input_image = Image.open(image)
            #extracting image using easyocr using function load_model()
            reader = load_model()
            result = reader.readtext(np.array(input_image))
            result_text = []
            for text in result:
                result_text.append(text[1])
            
            #calling function to fetch data and store in dataframe
            data = get_data_from_result_text(result_text)
            #calling function to convert image into binary data
            img = convertToBinaryData(image)
            #calling function to get dataframe
            df = get_dataframe(data,img)
            st.dataframe(df)
    
        clicked1 = st.button("**Load into Database**")
        if clicked1:
            with st.spinner("Connecting MySQL..."):
                #calling function to insert data into database
                load_into_mysql(df)
with tab2:
    col1,col2 = st.columns(2)
    with col1:
        sql = "SELECT name from bizcardx"
        cursor.execute(sql)
        result = cursor.fetchall()
        result = [', '.join(map(str, x)) for x in result]
        name1 = st.selectbox("Select cardholder name to update or delete the data", result)
        if name1:
            option = st.selectbox("Choose an option..",('Select something','View Card','Update Card','Delete Card'))
        else:
            st.write("No data available in database")
    with col2:
        if option == 'Update Card':
            sql = "SELECT company,name,designation,phone,email,website,area,city,state,pincode FROM bizcardx WHERE name = '"+name1+"'"
            cursor.execute(sql)
            result = cursor.fetchone()
            # displaying all the informations
            company2 = st.text_input("Company_Name", result[0])
            name2 = st.text_input("Card_Holder_Name", result[1])
            designation2 = st.text_input("Designation", result[2])
            phone2 = st.text_input("Mobile_Number", result[3])
            email2 = st.text_input("Email", result[4])
            website2 = st.text_input("Website", result[5])
            area2 = st.text_input("Area", result[6])
            city2 = st.text_input("City", result[7])
            state2 = st.text_input("State", result[8])
            pincode2 = st.text_input("Pin_Code", result[9])
            if st.button("Proceed..!"):
                sql = "UPDATE bizcardx SET company='"+company2+"',name='"+name2+"',designation='"+designation2+"',phone='"+phone2+"',email='"+email2+"',area='"+area2+"',city='"+city2+"',state='"+state2+"',pincode="+pincode2+" WHERE name = '"+name1+"'"
                cursor.execute(sql)
                mydb.commit()
                st.success("Updated Successfully..!!!")
        if option == 'Delete Card':
            if st.button("Proceed..!"):
                try:
                    sql = "DELETE from bizcardx WHERE name = '"+name1+"'"
                    cursor.execute(sql)
                    mydb.commit()
                    st.success("Card details deleted from database")            
                except mysql.connector.Error:
                    st.error("An Error Occurred")
        if option == 'View Card':
            sql = "SELECT * from bizcardx WHERE name = '"+name1+"'"
            cursor.execute(sql)
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(result, columns=column_names)
            st.dataframe(df,use_container_width=True)
