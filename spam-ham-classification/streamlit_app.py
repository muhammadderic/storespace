import streamlit as st
import joblib

# load model
# This job need to be improved again
model = joblib.load('spam_text_clf_model.joblib')

st.title('Stay ahead of spammers')
st.subheader('Classify messages as spam or legitimate instantly!')

message = st.text_input('Enter a message')

submit = st.button('Predict')


if submit:
    prediction = model.predict([message])
    
    if prediction[0] == 'spam':
        st.warning('This message is spam')
        st.snow()
    else:
        st.success('This message is Legit (HAM)')
        st.balloons()

