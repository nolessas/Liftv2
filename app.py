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
    workouts = {}
    
    # Attempt to fetch all documents within the user's collection
    try:
        docs = user_ref.stream()
        for doc in docs:
            doc_id = doc.id
            doc_data = doc.to_dict()
            workouts[doc_id] = doc_data
            print(f"Found workout {doc_id} for user {user_id}: {doc_data}")  # Debug print
    except Exception as e:
        print(f"An error occurred: {e}")

    if workouts:
        print(f"Collected workout data for user {user_id}: {workouts}")  # Debug print
        return workouts
    else:
        print(f"No workouts found for user_id: {user_id}")  # Debug print
        return None

def update_exercise_weight(user_id, exercise_name, detail_name, current_weight, success):
    db = firestore.client()
    user_ref = db.collection(user_id).document(exercise_name)
    
    weight_increment = 2.5 if success else -2.5
    if 'Chinups' in exercise_name:
        new_weight = max(0, current_weight + weight_increment)
    elif 'Cardio' in exercise_name:
        new_weight = current_weight + (1 if success else -1)
    else:
        new_weight = current_weight + weight_increment
    
    # Update the nested field within the document
    user_ref.update({detail_name: new_weight})

import streamlit as st

def display_and_update_weights(user_id):
    st.write(f"Profile: {user_id}")
    exercises = get_current_weights(user_id)
    selected_exercises = {}  # Keep track of selected exercises

    if exercises:
        for exercise_name, details in exercises.items():
            if isinstance(details, dict):
                detail_name, weight = next(iter(details.items()))
                col1, col2, col3, col4 = st.columns([5, 1, 1, 1])  # Add an extra column for selection
                with col1:
                    unit = "min" if "Cardio" in exercise_name else "kg"
                    st.write(f"{exercise_name} {detail_name}: {weight}{unit}")
                with col4:  # Use the extra column for checkboxes
                    # Let users select exercises
                    selected = st.checkbox("", key=f"select_{user_id}_{exercise_name}")
                    selected_exercises[exercise_name] = selected

                with col2:
                    if st.button("✅", key=f"{user_id}_{exercise_name}_success"):
                        update_exercise_weight(user_id, exercise_name, detail_name, weight, True)
                        st.experimental_rerun()
                with col3:
                    if st.button("❌", key=f"{user_id}_{exercise_name}_fail"):
                        update_exercise_weight(user_id, exercise_name, detail_name, weight, False)
                        st.experimental_rerun()
            else:
                st.error(f"Unexpected data format for {exercise_name} in user {user_id}'s document.")

        # At the bottom, add Success and Failure buttons for selected exercises
        if st.button("Success for Selected"):
            for exercise_name, selected in selected_exercises.items():
                if selected:
                    # Update each selected exercise as success
                    update_exercise_weight(user_id, exercise_name, detail_name, weight, True)
            st.experimental_rerun()

        if st.button("Failure for Selected"):
            for exercise_name, selected in selected_exercises.items():
                if selected:
                    # Update each selected exercise as failure
                    update_exercise_weight(user_id, exercise_name, detail_name, weight, False)
            st.experimental_rerun()
    else:
        st.error("No exercises found for this user.")


def main():
    st.title('Workout Progress Tracker')
    init_firebase()  # Initialize Firebase Admin SDK
    selected_user = st.radio("Select user:", ["Egis", "Karolis", "Kipras"])
    display_and_update_weights(selected_user)

if __name__ == "__main__":
    main()
