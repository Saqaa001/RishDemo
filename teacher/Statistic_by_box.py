import streamlit as st
import pandas as pd
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Access Firestore client from session_state
db = st.session_state.db


@st.cache_data(show_spinner=False)
def get_student_username(student_id: str) -> str:
    doc = db.collection("Student").document(student_id).get()
    return doc.to_dict().get("username", "Unknown") if doc.exists else "Unknown"


@st.cache_data(show_spinner=False)
def get_student_taken_test(doc_path: str) -> dict:
    doc = db.document(doc_path).get()
    return doc.to_dict() if doc.exists else {}


@st.cache_data(show_spinner=False)
def get_question_body(question_id: str) -> dict:
    doc = db.collection("Questions").document("Math").collection("All").document(question_id).get()
    return doc.to_dict() if doc.exists else {}


def main():
    st.title("Field Viewer by ID")

    if 'box_data' not in st.session_state:
        st.session_state.box_data = {}
    if 'selected_box' not in st.session_state:
        st.session_state.selected_box = None

    st.header("Search Field by ID")
    field_id = st.text_input("Enter Field ID:", value="L0AkesFie8dxqXEXfOAZ")

    if st.button("Search"):
        doc = db.collection("Student_path_test_by_box").document(field_id).get()
        if doc.exists:
            st.session_state.box_data = doc.to_dict().get("Box", {})
            if st.session_state.box_data:
                st.session_state.selected_box = next(iter(st.session_state.box_data.keys()))
            else:
                st.warning("No boxes found in this field.")
                st.session_state.selected_box = None
        else:
            st.warning("Field ID not found.")
            st.session_state.box_data = {}
            st.session_state.selected_box = None

    if st.session_state.box_data:
      
        st.divider()

        col1, col2 = st.columns([3, 1])

        with col1:
            selected_box = st.session_state.selected_box
            if selected_box:
                username = get_student_username(selected_box)
                st.subheader(f"{username}")

                doc_refs = st.session_state.box_data.get(selected_box, [])
                if not isinstance(doc_refs, list):
                    st.warning("⚠️ Unexpected data format for documents in box.")
                    return

                total_questions = total_correct = total_incorrect = 0
                results_data = []

                # For new analytics
                question_stats = defaultdict(lambda: {"correct": 0, "total": 0, "answers": defaultdict(int), "attempted_by": set()})
                doc_summary = []  # Per-document summary: doc_id, total_qs, correct_qs, accuracy
                student_scores = defaultdict(lambda: {"tests_taken": 0, "total_correct": 0, "total_questions": 0})

                
                show_correct = st.checkbox("✅ Show correct answers", value=True)
                show_incorrect = st.checkbox("❌ Show incorrect answers", value=True)

                st.divider()

                # st.write(f"**Total documents:** {len(doc_refs)}")

                for i, doc_ref in enumerate(doc_refs, start=1):
                    taken_test = get_student_taken_test(doc_ref.path)
                    answers = taken_test.get("answers", {})
                    # Optionally, get timestamp if available:
                    timestamp = taken_test.get("timestamp")  # Placeholder for time-based trends

                    correct_in_doc = 0
                    total_in_doc = len(answers)

                    # Use document path as unique identifier
                    doc_id = doc_ref.path if hasattr(doc_ref, "path") else str(doc_ref)

                    for qid, answer in answers.items():
                        question_body = get_question_body(qid)
                        correct_answer = question_body.get("answer")
                        if correct_answer == "W":
                            correct_answer_value = "W"
                        else:
                            correct_answer_value = question_body.get(correct_answer)
                        is_correct = (answer == correct_answer)

                        total_questions += 1
                        if is_correct:
                            total_correct += 1
                            correct_in_doc += 1
                        else:
                            total_incorrect += 1

                        results_data.append({
                            "Document": doc_id,
                            "Question ID": qid,
                            "Answer Given": answer,
                            "Correct Answer": correct_answer,
                            "Is Correct": is_correct,
                            "correct_answer_value":correct_answer_value
                        })

                        # Update per-question stats
                        qstat = question_stats[qid]
                        qstat["total"] += 1
                        if is_correct:
                            qstat["correct"] += 1
                        qstat["answers"][answer] += 1
                        qstat["attempted_by"].add(doc_id)

                        # Update per-student summary assuming selected_box == student_id
                        student_scores[selected_box]["tests_taken"] += 1
                        student_scores[selected_box]["total_correct"] += int(is_correct)
                        student_scores[selected_box]["total_questions"] += 1

                        if (is_correct and show_correct) or (not is_correct and show_incorrect):
                            st.markdown(f"**Q{i}. {qid}**")
                            if question_body:
                                st.write("Question:", question_body.get("question", "No question text."))
                            if is_correct:
                                st.success(f"✅ {answer}. {correct_answer_value}")
                            else:
                                st.error(f"❌ {answer}. {correct_answer_value }")

                    # Append per-document summary
                    accuracy = (correct_in_doc / total_in_doc) * 100 if total_in_doc > 0 else 0
                    doc_summary.append({"Document": doc_id, "Total Questions": total_in_doc, "Correct Answers": correct_in_doc, "Accuracy": accuracy})

                # Basic summary stats
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

                # === Detailed Analytics ===
                st.write("---")
                st.subheader("🔍 Detailed Analytics")

                # 1. Per-Question Performance
                st.markdown("**1. Per-Question Performance**")
                pq_data = []
                for qid, stats in question_stats.items():
                    accuracy = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
                    pq_data.append({"Question ID": qid,
                                    "Attempts": stats["total"],
                                    "Correct %": accuracy,
                                    "Completion Rate": len(stats["attempted_by"])})
                pq_df = pd.DataFrame(pq_data).sort_values(by="Correct %", ascending=False)
                st.dataframe(pq_df)

                # Highlight hardest questions (lowest accuracy)
                hardest = pq_df.nsmallest(3, "Correct %")
                st.markdown("**Hardest Questions (Lowest Accuracy):**")
                for _, row in hardest.iterrows():
                    st.write(f"- {row['Question ID']} — {row['Correct %']:.2f}% correct")

                # 2. Per-Document / Test Summary
                st.markdown("**2. Per-Document / Test Summary**")
                doc_df = pd.DataFrame(doc_summary)
                # Map document IDs to username + short doc id
                username = get_student_username(selected_box)
                doc_df["Student Username"] = username
                doc_df_display = doc_df.copy()
                doc_df_display["Document"] = doc_df["Student Username"] + " (" + doc_df["Document"].apply(lambda x: x.split('/')[-1]) + ")"

                st.dataframe(doc_df_display)

                # Bar chart of accuracy per test document with username+doc label
                st.bar_chart(doc_df_display.set_index("Document")["Accuracy"])

                # 3. Time-Based Trends (if timestamp available)
                st.markdown("**3. Time-Based Trends**")
                timestamps = []
                accuracies = []
                for doc_ref in doc_refs:
                    taken_test = get_student_taken_test(doc_ref.path)
                    answers = taken_test.get("answers", {})
                    ts = taken_test.get("timestamp")
                    if not ts:
                        continue
                    correct_count = 0
                    total_count = len(answers)
                    for qid, answer in answers.items():
                        correct_answer = get_question_body(qid).get("answer")
                        if answer == correct_answer:
                            correct_count += 1
                    if total_count > 0:
                        timestamps.append(ts)
                        accuracies.append(correct_count / total_count * 100)
                if timestamps and accuracies:
                    time_df = pd.DataFrame({"Timestamp": pd.to_datetime(timestamps), "Accuracy": accuracies})
                    time_df = time_df.sort_values("Timestamp")
                    st.line_chart(time_df.set_index("Timestamp")["Accuracy"])
                else:
                    st.write("No timestamp data available for time-based trends.")

                # 4. Answer Distribution (per question)
                st.markdown("**4. Answer Distribution (per question)**")
                for qid, stats in question_stats.items():
                    st.write(f"Question ID: {qid}")
                    answers = stats["answers"]
                    if answers:
                        ans_df = pd.DataFrame(list(answers.items()), columns=["Answer", "Count"]).sort_values(by="Count", ascending=False)
                        st.bar_chart(ans_df.set_index("Answer")["Count"])
                    else:
                        st.write("No answers recorded.")

                # 5. Student-Level Summary (for selected box/student)
                st.markdown("**5. Student-Level Summary**")
                for student_id, summary in student_scores.items():
                    tests_taken = summary["tests_taken"]
                    total_correct = summary["total_correct"]
                    total_qs = summary["total_questions"]
                    avg_accuracy = (total_correct / total_qs) * 100 if total_qs > 0 else 0
                    st.write(f"- Student: {get_student_username(student_id)}")
                    st.write(f"  - Tests Taken: {tests_taken}")
                    st.write(f"  - Total Questions Answered: {total_qs}")
                    st.write(f"  - Average Accuracy: {avg_accuracy:.2f}%")

                # 6. Accuracy Heatmap (Questions vs Documents)
                st.markdown("**6. Accuracy Heatmap**")
                # Create matrix: rows=questions, cols=documents, values=1 if correct else 0
                question_list = list(question_stats.keys())
                document_list = []
                for doc_ref in doc_refs:
                    doc_name = doc_ref.path.split('/')[-1] if hasattr(doc_ref, "path") else str(doc_ref)
                    username = get_student_username(selected_box)
                    document_list.append(f"{username} ({doc_name})")

                heatmap_data = pd.DataFrame(0, index=question_list, columns=document_list)
                for entry in results_data:
                    qid = entry["Question ID"]
                    doc_id = entry["Document"]
                    doc_short = doc_id.split('/')[-1] if '/' in doc_id else doc_id
                    col_label = f"{get_student_username(selected_box)} ({doc_short})"
                    heatmap_data.at[qid, col_label] = int(entry["Is Correct"])

                fig, ax = plt.subplots(figsize=(10, max(4, len(question_list)*0.3)))
                sns.heatmap(heatmap_data, cmap="YlGnBu", cbar_kws={"label": "Correctness"})
                ax.set_xlabel("Documents")
                ax.set_ylabel("Questions")
                st.pyplot(fig)

                # 7. Statistical Metrics
                st.markdown("**7. Statistical Metrics**")
                accuracies = [d["Accuracy"] for d in doc_summary if d["Accuracy"] is not None]
                if accuracies:
                    mean_acc = np.mean(accuracies)
                    std_acc = np.std(accuracies)
                    var_acc = np.var(accuracies)
                    st.write(f"- Mean Accuracy: {mean_acc:.2f}%")
                    st.write(f"- Standard Deviation: {std_acc:.2f}")
                    st.write(f"- Variance: {var_acc:.2f}")
                else:
                    st.write("No accuracy data to calculate statistics.")

                # 8. Question Completion Rate
                st.markdown("**8. Question Completion Rate**")
                total_docs = len(doc_refs)
                completion_data = []
                for qid, stats in question_stats.items():
                    completion_rate = (len(stats["attempted_by"]) / total_docs) * 100 if total_docs > 0 else 0
                    completion_data.append({"Question ID": qid, "Completion Rate (%)": completion_rate})
                completion_df = pd.DataFrame(completion_data).sort_values(by="Completion Rate (%)", ascending=False)
                st.dataframe(completion_df)

        with col2:
            
           

            st.markdown("##### Students: " + str(len(st.session_state.box_data)))
            for box_id in st.session_state.box_data.keys():
                username = get_student_username(box_id)
                if st.button(username, key=f"btn_{box_id}"):
                    st.session_state.selected_box = box_id
                    st.rerun()

if __name__ == "__main__":
    main()
