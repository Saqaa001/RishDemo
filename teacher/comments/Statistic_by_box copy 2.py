import streamlit as st
import pandas as pd

# Access Firestore from session_state
db = st.session_state.db


def get_student_username(student_id):
    doc = db.collection("Student").document(student_id).get()
    return doc.to_dict().get("username", "Unknown") if doc.exists else "Unknown"


def get_student_taken_test(ref):
    doc = ref.get()
    return doc.to_dict() if doc.exists else {}


def get_question_body(question_id):
    doc = db.collection("Questions").document("Math").collection("All").document(question_id).get()
    return doc.to_dict() if doc.exists else {}


def main():
    st.title("Field Viewer by ID")

    st.session_state.setdefault('selected_box', None)
    st.session_state.setdefault('box_data', {})

    st.header("Search Field by ID")
    field_id = st.text_input("Enter Field ID:", "L0AkesFie8dxqXEXfOAZ")

    if st.button("Search"):
        doc = db.collection("Student_path_test_by_box").document(field_id).get()
        if doc.exists:
            st.session_state.box_data = doc.to_dict().get("Box", {})
            if st.session_state.box_data and not st.session_state.selected_box:
                st.session_state.selected_box = next(iter(st.session_state.box_data.keys()))
        else:
            st.warning("Field ID not found.")

    if st.session_state.box_data:
        st.markdown(f"### Viewing Field: `{field_id}`")
        st.divider()

        col1, col2 = st.columns([3, 1])

        with col1:
            selected_box = st.session_state.selected_box
            if selected_box:
                username = get_student_username(selected_box)
                st.subheader(f"Documents in Box: {username}")

                doc_refs = st.session_state.box_data[selected_box]
                total_questions = 0
                total_correct = 0
                total_incorrect = 0
                results_data = []

                show_correct = st.checkbox("✅ Show correct answers", value=True)
                show_incorrect = st.checkbox("❌ Show incorrect answers", value=True)

                if isinstance(doc_refs, list):
                    st.write(f"**Total documents:** {len(doc_refs)}")

                    for i, doc_ref in enumerate(doc_refs, 1):
                        taken_test = get_student_taken_test(doc_ref)
                        answers = taken_test.get("answers", {})

                        for qid, answer in answers.items():
                            question_body = get_question_body(qid)
                            correct_answer = question_body.get("answer") if question_body else None
                            is_correct = answer == correct_answer

                            total_questions += 1
                            if is_correct:
                                total_correct += 1
                            else:
                                total_incorrect += 1

                            results_data.append({
                                "Question ID": qid,
                                "Answer Given": answer,
                                "Correct Answer": correct_answer,
                                "Is Correct": is_correct,
                            })

                            # Filtering logic
                            if (is_correct and show_correct) or (not is_correct and show_incorrect):
                                st.markdown(f"**Q{i}.{qid}**: Answer: `{answer}`")
                                if question_body:
                                    st.write("Question:", question_body.get("question", "No question text."))
                                if is_correct:
                                    st.success("✅ Correct")
                                else:
                                    st.error(f"❌ Incorrect (Expected: `{correct_answer}`)")

                    # Statistics
                    st.write("---")
                    st.subheader("📊 Answer Statistics")
                    st.write(f"- **Total Questions:** {total_questions}")
                    st.write(f"- ✅ **Correct Answers:** {total_correct}")
                    st.write(f"- ❌ **Incorrect Answers:** {total_incorrect}")
                    if total_questions > 0:
                        accuracy = (total_correct / total_questions) * 100
                        st.write(f"- 🎯 **Accuracy:** {accuracy:.2f}%")
                        st.progress(total_correct / total_questions)

                        # CSV download
                        df = pd.DataFrame(results_data)
                        csv = df.to_csv(index=False).encode()
                        st.download_button("📥 Download Results as CSV", csv, "results.csv", "text/csv")
                else:
                    st.warning("⚠️ Unexpected data format for documents in box.")

        with col2:
            st.subheader("Available Boxes")
            st.write(f"**Total boxes:** {len(st.session_state.box_data)}")

            if selected_box:
                count = len(st.session_state.box_data[selected_box]) if isinstance(
                    st.session_state.box_data[selected_box], list) else 1
                st.write(f"**Current box documents:** {count}")

            st.markdown("### Select Box:")
            for box_id in st.session_state.box_data:
                username = get_student_username(box_id)
                if st.button(username, key=f"btn_{box_id}"):
                    st.session_state.selected_box = box_id
                    st.rerun()


if __name__ == "__main__":
    main()
