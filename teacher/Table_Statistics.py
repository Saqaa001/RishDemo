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
        doc_ref = db.collection("Student_path_test_by_box").document(field_id)
        doc = doc_ref.get()
        
        if doc.exists:
            st.session_state.box_data = doc.to_dict().get("Box", {})
            if st.session_state.box_data and not st.session_state.selected_box:
                st.session_state.selected_box = next(iter(st.session_state.box_data.keys()))
    
    
    
    




        
        
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
                is_correct = 1 if student_answer == correct_answer else 0
                true_false_list.append(is_correct)

            true_false_lists.append(true_false_list)

        # Build DataFrame with usernames as columns, QNs as index
        df = pd.DataFrame(true_false_lists, index=usernames).T

        # Set dynamic QN based on question keys
        df.index = [f"Q{n+1}" for n in range(len(df))]
        df.index.name = "QN"

        # Display
        st.write("Usernames:", usernames)
        st.dataframe(df)


        if 0:
            st.subheader(f"Documents in Box: {get_student_username(st.session_state.selected_box)}")
            doc_refs = st.session_state.box_data[st.session_state.selected_box]
            
            if isinstance(doc_refs, list):
                # st.write(f"**Total documents:** {len(doc_refs)}")
                for i, doc_ref in enumerate(doc_refs, 1):
                    taken_test = get_student_taken_test(doc_ref)
                    st.write(doc_ref)
                    answers = taken_test.get("answers")
                    # st.write(f"{i}. {doc_ref}")
                    # st.write(answers)
                    for qid,answer  in answers.items():

                        # st.write(qid,answer)
                        question_body = get_question_body(qid)
                        # st.write(qid,answer)
            else:
                st.write("doc_refs")









    # Display results if data exists
    if 0:
        st.write(f"### Viewing Field: {field_id}")
        st.write("---")
        
        # Create two columns
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.session_state.selected_box:
                st.subheader(f"Documents in Box: {get_student_username(st.session_state.selected_box)}")
                doc_refs = st.session_state.box_data[st.session_state.selected_box]
                
                if isinstance(doc_refs, list):
                    st.write(f"**Total documents:** {len(doc_refs)}")
                    for i, doc_ref in enumerate(doc_refs, 1):
                        taken_test = get_student_taken_test(doc_ref)
                        answers = taken_test.get("answers")
                        st.write(f"{i}. {doc_ref}")
                        st.write(answers)
                        for qid,answer  in answers.items():

                            st.write(qid,answer)
                            question_body = get_question_body(qid)
                            st.write(qid,answer)
                else:
                    st.write("doc_refs")
        
        with col2:
            st.subheader("Available Boxes")
            st.write(f"**Total boxes:** {len(st.session_state.box_data)}")
            
            if st.session_state.selected_box:
                doc_refs = st.session_state.box_data[st.session_state.selected_box]
                count = len(doc_refs) if isinstance(doc_refs, list) else 1
                st.write(f"**Current box documents:** {count}")
            
            st.write("### Select Box:")
            for box_id in st.session_state.box_data:
                username = get_student_username(box_id)
                if st.button(username, key=f"btn_{box_id}"):
                    st.session_state.selected_box = box_id
                    st.rerun()

if __name__ == "__main__":
    main()



