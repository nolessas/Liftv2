import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json


def init_firebase():
    if not firebase_admin._apps:
        firebase_secret_dict = st.secrets["Fire_base"]
        # Convert the secrets object to a regular Python dictionary
        firebase_secret_dict = dict(firebase_secret_dict)
        # Create a copy of the secret dictionary
        modified_secret_dict = firebase_secret_dict.copy()
        # Replace escape characters in the private key
        modified_secret_dict['private_key'] = modified_secret_dict['private_key'].replace('\\n', '\n')
        cred = credentials.Certificate(modified_secret_dict)
        firebase_admin.initialize_app(cred)



# Function to get the current weights for a user
def get_current_weights(user_id):
    db = firestore.client()
    user_ref = db.collection(user_id)  # Access the collection corresponding to the user
    workouts_by_day = {"Day1": {}, "Day2": {}}

    try:
        docs = user_ref.stream()
        for doc in docs:
            doc_id = doc.id
            doc_data = doc.to_dict()
            if doc_id in ["1.Squat", "2.Benchpress", "3.Deadlift"]:
                workouts_by_day["Day1"][doc_id] = doc_data
            elif doc_id in ["4.Cardio", "5.OHP", "6.Chinups"]:
                workouts_by_day["Day2"][doc_id] = doc_data
    except Exception as e:
        st.error(f"An error occurred: {e}")

    return workouts_by_day

def update_exercise_weight(user_id, exercise_name, detail_name, current_weight, success):
    db = firestore.client()
    user_ref = db.collection(user_id).document(exercise_name)
    
    weight_increment = 2.5 if success else -2.5
    new_weight = current_weight + weight_increment  # Default increment behavior

    if 'Chinups' in exercise_name:
        # For Chinups, do not enforce a minimum weight of 0 to allow negative weights
        pass
    elif 'Cardio' in exercise_name:
        # For Cardio, increment or decrement by 1
        new_weight = current_weight + (1 if success else -1)
    else:
        # For other exercises, ensure the weight does not go below zero
        new_weight = max(0, new_weight)
    
    # Update the nested field within the document
    user_ref.update({detail_name: new_weight})

    
    # Update the nested field within the document
    user_ref.update({detail_name: new_weight})

def display_and_update_weights(user_id):
    # Custom CSS to make the columns fit-content
    st.markdown("""
                <style>
                    div[data-testid="column"] {
                        display: flex;
                        flex-direction: row;
                        gap: 0.75rem;
                    }
                    div[data-testid="column"] > div {
                        flex: 1;
                    }
                    .stButton > button {
                        width: 100%;
                        padding: 0.25rem 0.75rem;
                    }
                </style>
                """, unsafe_allow_html=True)

    # Fetch the categorized workouts
    workouts_by_day = get_current_weights(user_id)

    # Check if workouts exist
    if workouts_by_day:
        # Loop through each day and its exercises
        for day, exercises in workouts_by_day.items():
            st.header(day)  # Display the day as a header
            for exercise_name, details in exercises.items():
                if isinstance(details, dict):
                    detail_name, weight = next(iter(details.items()))
                    unit = "min" if "Cardio" in exercise_name else "kg"

                    # Use custom column widths for display and buttons
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.text(f"{exercise_name} {detail_name}: {weight}{unit}")
                    with col2:
                        if st.button("✅", key=f"success_{exercise_name}"):
                            update_exercise_weight(user_id, exercise_name, detail_name, weight, success=True)
                            st.experimental_rerun()
                    with col3:
                        if st.button("❌", key=f"fail_{exercise_name}"):
                            update_exercise_weight(user_id, exercise_name, detail_name, weight, success=False)
                            st.experimental_rerun()
                else:
                    st.error(f"Unexpected data format for {exercise_name} in user {user_id}'s document.")
    else:
        st.error("No exercises found for this user.")




def main():
    st.image("dale4.png", use_column_width=True)
    st.title('')
    init_firebase()  # Initialize Firebase Admin SDK
    selected_user = st.radio("", ["Egis", "Karolis", "Kipras"], horizontal=True)
    display_and_update_weights(selected_user)


if __name__ == "__main__":
    main()
