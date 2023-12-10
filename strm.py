import streamlit as st

st.title(":green[BMI calculator]")
st.subheader("Get your BMI... Are you healthy?")
weight = st.number_input("Enter your weight")
height = st.slider("Enter your height (in cm)", 50, 300)
st.text('Selected: {}'.format(height))
if st.button('Done'):
    bmi = weight/(height/100)**2
    st.text('BMI = {}'.format(round(bmi,2)))
    if bmi < 18.5:
        st.error("Underweight")
    elif 18.5 <= bmi <= 24.9:
        st.success("Normal")
    elif 25 <= bmi <= 29.9:
        st.warning("Overweight")
    else:
        st.error("Obesity")
