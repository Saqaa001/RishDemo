import streamlit as st
import pandas as pd 


# Assuming db is initialized elsewhere and available in session_state
db = st.session_state.db


def get_student_username(student_id):
    """Retrieve username from Student collection"""
    student_ref = db.collection("Student").document(student_id)
    doc = student_ref.get()
    return doc.to_dict().get("username", "Unknown") if doc.exists else "Unknown"


def get_student_taken_test(ref):

    taken_test = {}
    doc = ref.get()

    # Print the result
    if doc.exists:
        taken_test = doc.to_dict()

    else:
        print("Document not found.")

    return taken_test 


def get_question_body(question_id):
    question = {}
    question_ref = db.collection("Questions").document("Math").collection("All").document(question_id)
    question = question_ref.get().to_dict().get("answer")
    return question


def main():
    st.title("Field Viewer by ID")
    
    # Initialize session state
    if 'selected_box' not in st.session_state:
        st.session_state.selected_box = None
    if 'box_data' not in st.session_state:
        st.session_state.box_data = {}
    
    # Search section
    st.header("Search Field by ID")
    field_id = st.text_input("Enter Field ID:", "L0AkesFie8dxqXEXfOAZ")
    
    if st.button("Search"):
        st.divider()
        doc_ref = db.collection("Student_path_test_by_box").document(field_id)
        doc = doc_ref.get()
        
        if doc.exists:
            st.session_state.box_data = doc.to_dict().get("Box", {})
            if st.session_state.box_data and not st.session_state.selected_box:
                st.session_state.selected_box = next(iter(st.session_state.box_data.keys()))
    
            # Prepare to collect data
            usernames = []
            usernames_id = []
            true_false_lists = []
            all_question_keys = set()

            # First pass: collect usernames and all unique question keys
            for key, value in st.session_state.box_data.items():
                usernames_id.append(key)
                username = get_student_username(key)
                usernames.append(username)

                taken_test = get_student_taken_test(value[0])
                question_answer = taken_test.get("answers", {})

                all_question_keys.update(question_answer.keys())

            # Sort question keys to keep consistent QN order
            sorted_question_keys = sorted(all_question_keys)

            # Second pass: build true/false matrix
            for key in usernames_id:
                taken_test = get_student_taken_test(st.session_state.box_data[key][0])
                question_answer = taken_test.get("answers", {})
                true_false_list = []

                for qid in sorted_question_keys:
                    student_answer = question_answer.get(qid, None)
                    correct_answer = get_question_body(qid)
                    is_correct = "✅" if student_answer == correct_answer else "❌"
                    true_false_list.append(is_correct)

                true_false_lists.append(true_false_list)

            # Build DataFrame with usernames as columns, QNs as index
            df = pd.DataFrame(true_false_lists, index=usernames).T

            # Set dynamic QN based on question keys
            df.index = [f"Q{n+1}" for n in range(len(df))]
            df.index.name = "QN"

            # Add total stats rows: count number of "✅" and "❌" per student
            total_correct = (df == "✅").sum(axis=0)
            total_incorrect = (df == "❌").sum(axis=0)
            df.loc["Total Correct"] = total_correct
            df.loc["Total Incorrect"] = total_incorrect

            # Add column totals for questions: how many students got a question correct/incorrect
            total_question_correct = (df == "✅").sum(axis=1)
            total_question_incorrect = (df == "❌").sum(axis=1)
            df["Total Correct"] = total_question_correct
            df["Total Incorrect"] = total_question_incorrect

            # Display the DataFrame
            st.dataframe(df)

if __name__ == "__main__":
    main()


        







        
        # # Initial usernames
        # usernames = []
        # usernames_id = []

        # for key,value in st.session_state.box_data.items():
        #     usernames_id.append(key)
        #     username = get_student_username(key)
        #     usernames.append(username)
        #     taken_test = get_student_taken_test(value[0])
        #     question_answer = taken_test.get("answers")
        #     st.write(question_answer)

        # # Show current usernames
        # st.write(usernames)

        # # Update column names excluding "QN"
        # df.set_index("QN", inplace=True)

        # df.columns = usernames

        # # Display updated DataFrame
        # st.dataframe(df)


        # # Original DataFrame
        # df = pd.DataFrame(
        #     {
        #         "QN": [1, 2],
        #         "vali": ["A", "B" ],
        #         "sali": ["A", "B" ]
        #     }
        # )

        # # Prepare to collect data
        # usernames = []
        # usernames_id = []
        # answers_list = []
        # true_false_lists = []
        # # Loop through session state data
        # for key, value in st.session_state.box_data.items():
        #     usernames_id.append(key)
        #     username = get_student_username(key)
        #     usernames.append(username)

        #     taken_test = get_student_taken_test(value[0])
        #     question_answer = taken_test.get("answers", [])
        #     answers_list.append(question_answer)  # List of answers per user
        #     true_false_list = []
        #     for k,v in question_answer.items():
        #         # st.write(k,v)
        #         qbody = get_question_body(k)
        #         # st.write(qbody)
        #         true_false = 0
        #         if v == qbody:
        #             true_false = 1
                
        #         true_false_list.append(true_false)
        #     true_false_lists.append(true_false_list)
        # st.write(true_false_list)

        #     # st.write(f"{username}'s answers:", question_answer)

        # # Transpose the answers to have QNs as rows
        # df = pd.DataFrame(true_false_lists, index=usernames).T

        # # Set index to represent question numbers (e.g., QN 1, 2, 3...)
        # df.index = range(1, len(df) + 1)
        # df.index.name = "QN"

        # # Display
        # st.write("Usernames:", usernames)
        # st.dataframe(df)