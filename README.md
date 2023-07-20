# Business card Extraction using easyOCR and Streamlit
This Streamlit app will get business card image as input, process it and extract card data with easyOCR and the data can be stored in database. It allows us to view, update and delete the card details in Streamlit UI.
### Extracting card data with easyOCR and PIL
1. Upload an image in streamlit UI. streamlit fileuploader function is used here for the same<br/>
2. PIL Image can read the image and if image is not null, we are passing it to easyOCR engine to extract the data.<br/>
3. Extracted result data will further enumerated to get specific details like company,name,designation,phone,email,website and address.<br/>
4. Extracted data is stored in a pandas dataframe and shown in streamlit UI.
### Loading in MySQL
1. From dataframe, inserting the row along with image as encoded data into MySQL using mysql-connector-python library.
2. If there is a duplicate entry, card data will not get inserted in database
### View,Update and Delete Card
1. Card Details can be viewed, updated and deleted upon selecting the Card holder name in the selectbox.
2. Once done, it will show success message.

# Streamlit app: https://bizcardxtract-bdwgfyuk5b.streamlit.app/ 
