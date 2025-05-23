import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
from scipy.optimize import root_scalar

# --- Rasch Model Functions ---
@st.cache_data
def rasch_probability(theta, b):
    return 1 / (1 + np.exp(-(float(theta) - float(b))))

def infit_outfit(obs, exp):
    residuals = obs - exp
    weights = exp * (1 - exp)
    infit = np.sum(weights * residuals**2) / np.sum(weights)
    outfit = np.mean(residuals**2)
    return infit, outfit

@st.cache_data
def test_information(theta, difficulties):
    return sum([rasch_probability(theta, b) * (1 - rasch_probability(theta, b)) for b in difficulties])

def simulate_responses(theta, difficulties):
    return [np.random.binomial(1, rasch_probability(theta, b)) for b in difficulties]

def weighted_likelihood_estimation(responses, difficulties):
    def score_func(theta):
        p = np.array([rasch_probability(theta, b) for b in difficulties])
        return np.sum(responses - p)
    res = root_scalar(score_func, bracket=[-4, 4])
    return res.root if res.converged else np.nan

# --- Firestore Accessors ---
db = st.session_state.db

@st.cache_data
def get_student_data(sid):
    doc = db.collection("Student").document(sid).get()
    data = doc.to_dict() if doc.exists else {}
    return data.get("username", "Unknown"), float(data.get("Student_Ability", np.nan)), data.get("group", "Group1")

@st.cache_data
def get_question_data(qid):
    doc = db.collection("Questions").document("Math").collection("All").document(qid).get()
    data = doc.to_dict() if doc.exists else {}
    return data.get("answer"), float(data.get("Question_Deficulity", np.nan))


def get_taken_test_data(ref):
    doc = ref.get()
    return doc.to_dict() if doc.exists else {}

# --- Main Streamlit App ---
def main():
    st.title("Rasch Model Dashboard")

    with st.sidebar:
        field_id = st.text_input("Enter Field ID:", "L0AkesFie8dxqXEXfOAZ")
        search = st.button("Search")
        min_ability = st.slider("Min Ability Threshold", -4.0, 4.0, -4.0)

    if "search_done" not in st.session_state:
        st.session_state.search_done = False

    if search:
        st.session_state.search_done = True
        st.session_state.field_id = field_id
        st.session_state.min_ability = min_ability

    if not st.session_state.search_done:
        return

    doc = db.collection("Student_path_test_by_box").document(st.session_state.field_id).get()
    if not doc.exists:
        st.warning("Field ID not found.")
        return

    box_data = doc.to_dict().get("Box", {})
    usernames, student_ids, abilities, responses, groups = [], [], {}, {}, {}
    all_qids = set()

    for sid, refs in box_data.items():
        username, ability, group = get_student_data(sid)
        test = get_taken_test_data(refs[0])
        answers = test.get("answers", {})

        usernames.append(username)
        student_ids.append(sid)
        abilities[username] = ability
        responses[username] = answers
        groups[username] = group
        all_qids.update(answers.keys())

    qids = sorted(all_qids)
    question_data = {qid: get_question_data(qid) for qid in qids}
    difficulties = {qid: b for qid, (_, b) in question_data.items()}
    correct_answers = {qid: ans for qid, (ans, _) in question_data.items()}

    response_df = pd.DataFrame(index=usernames, columns=qids)
    for user in usernames:
        for qid in qids:
            ans = responses[user].get(qid)
            correct = correct_answers.get(qid)
            response_df.loc[user, qid] = int(ans == correct)

    expected = pd.DataFrame(index=usernames, columns=qids)
    for u in usernames:
        a = abilities.get(u)
        for qid in qids:
            b = difficulties.get(qid)
            expected.loc[u, qid] = rasch_probability(a, b) if not np.isnan(a) and not np.isnan(b) else np.nan

    observed = response_df.astype(float)

    # Summary Metrics
    st.subheader("Key Metrics")
    abil_values = [a for a in abilities.values() if not np.isnan(a)]
    p_var = np.var(abil_values)
    se_var = np.mean([1 / test_information(a, list(difficulties.values())) if test_information(a, list(difficulties.values())) > 0 else 0 for a in abil_values])
    reliability = p_var / (p_var + se_var) if p_var + se_var > 0 else np.nan

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Students", len(usernames))
    c2.metric("Items", len(qids))
    c3.metric("Avg Ability", f"{np.mean(abil_values):.2f}")
    c4.metric("Avg Difficulty", f"{np.mean(list(difficulties.values())):.2f}")
    c5.metric("Reliability", f"{reliability:.3f}")

    # Fit Stats
    item_fit, person_fit = {}, {}
    for qid in qids:
        obs, exp = observed[qid].dropna(), expected[qid].dropna()
        if len(obs) and len(exp):
            inf, outf = infit_outfit(obs, exp)
            item_fit[qid] = {"Infit": inf, "Outfit": outf}
    for u in usernames:
        obs, exp = observed.loc[u].dropna(), expected.loc[u].dropna()
        if len(obs) and len(exp):
            inf, outf = infit_outfit(obs, exp)
            person_fit[u] = {"Infit": inf, "Outfit": outf}

    st.subheader("Infit & Outfit Statistics")
    item_fit_df = pd.DataFrame(item_fit).T
    person_fit_df = pd.DataFrame(person_fit).T
    st.dataframe(item_fit_df)
    st.dataframe(person_fit_df)

    if "item_fit_csv" not in st.session_state:
        st.session_state.item_fit_csv = item_fit_df.to_csv().encode()
    if "person_fit_csv" not in st.session_state:
        st.session_state.person_fit_csv = person_fit_df.to_csv().encode()

    st.download_button("Download Item Fit CSV", data=st.session_state.item_fit_csv, file_name="item_fit.csv")
    st.download_button("Download Person Fit CSV", data=st.session_state.person_fit_csv, file_name="person_fit.csv")

    # Student Profile
    st.subheader("Student Profile")
    if "selected_student" not in st.session_state:
        st.session_state.selected_student = usernames[0] if usernames else None

    selected_student = st.selectbox("Select a student:", usernames, index=usernames.index(st.session_state.selected_student) if st.session_state.selected_student in usernames else 0, key="selected_student")
    
    if selected_student:
        st.write(f"**Ability:** {abilities[selected_student]}")
        st.write(f"**Group:** {groups[selected_student]}")
        st.dataframe(observed.loc[[selected_student]].T.rename(columns={selected_student: "Response"}))

    # Wright Map
    st.subheader("Wright Map")
    item_df = pd.DataFrame({"Type": "Item", "Logit": list(difficulties.values()), "Label": list(difficulties.keys())})
    person_df = pd.DataFrame({"Type": "Person", "Logit": list(abilities.values()), "Label": list(abilities.keys())})
    wright_df = pd.concat([item_df, person_df])

    w_chart = alt.Chart(wright_df).mark_circle(size=80).encode(
        y=alt.Y("Logit:Q", scale=alt.Scale(zero=False)),
        x=alt.X("Type:N", axis=alt.Axis(labelAngle=0)),
        tooltip=["Label", "Logit"]
    ).properties(height=500)

    st.altair_chart(w_chart, use_container_width=True)

    # --- Item Characteristic Curve (ICC) Visualization ---
    st.subheader("Item Characteristic Curve (ICC)")

    if qids:
        selected_qid = st.selectbox("Select an item to view ICC:", qids)

        # Prepare theta range
        theta_vals = np.linspace(-4, 4, 100)
        b = difficulties.get(selected_qid, np.nan)
        if not np.isnan(b):
            prob_vals = [rasch_probability(theta, b) for theta in theta_vals]

            fig, ax = plt.subplots()
            ax.plot(theta_vals, prob_vals, label='ICC Curve', color='blue')
            ax.set_xlabel("Ability (θ)")
            ax.set_ylabel("Probability of Correct Response")
            ax.set_title(f"Item Characteristic Curve for {selected_qid}")

            # Overlay observed student responses for that item
            ability_list = []
            response_list = []
            for user in usernames:
                a = abilities.get(user)
                r = observed.at[user, selected_qid] if selected_qid in observed.columns else np.nan
                if not np.isnan(a) and not np.isnan(r):
                    ability_list.append(a)
                    response_list.append(r)

            # Plot actual responses as scatter points: correct=1, incorrect=0
            ax.scatter(ability_list, response_list, color='red', alpha=0.6, label='Observed Responses')

            ax.legend()
            st.pyplot(fig)
        else:
            st.warning("Difficulty parameter for selected item not available.")
    else:
        st.info("No items available to display ICC.")

    # Response Heatmap
    st.subheader("Response Heatmap")
    filtered_students = [u for u in usernames if not np.isnan(abilities[u]) and abilities[u] >= st.session_state.min_ability]
    if filtered_students:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(observed.loc[filtered_students], cmap="RdYlGn", cbar=True, ax=ax)
        st.pyplot(fig)
    else:
        st.warning("No students above threshold")

if __name__ == "__main__":
    main()
