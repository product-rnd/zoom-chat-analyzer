import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import pyperclip
import re

class SessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def extract_participants_and_messages(lines):
    """
    Extracts participants and their messages from chat data.

    Args:
        lines (list): List of lines containing chat data.

    Returns:
        DataFrame: DataFrame containing participants and their messages.
    """
    chat_records = []
    for line in lines:
        parts = line.strip().decode('utf-8').split("\t")  # Decode bytes to string
        if len(parts) == 3:
            chat_records.append(parts)

    chat_data = pd.DataFrame(chat_records, columns=["Time", "Participant", "Message"])
    chat_data["Participant"] = chat_data["Participant"].str.replace(":", "")
    return chat_data

def extract_date_from_filename(filename):
    """
    Extracts the date from the file name after 'GMT'.

    Args:
        filename (str): The name of the file.

    Returns:
        str: The extracted date.
    """
    date_match = re.search(r"GMT(\d+)-", filename)
    if date_match:
        return date_match.group(1)
    else:
        return "Unknown Date"

def main():
    st.title("💭 Zoom Chat Analyzer")
    st.write("""
    📊 This app analyzes chat data and provides insights into the most active and silent participants.
    """)

    # Initialize session state
    state = SessionState(page="Summary", participant_data=None)

    # Page selection
    page = st.sidebar.radio("📍 Select Page", ["Summary", "Individual Analytics"], index=["Summary", "Individual Analytics"].index(state.page))

    if page == "Summary":
        state.page = "Summary"

        st.markdown("---")
        st.header("📃 Summary Page")

        # Course name and day input
        course_name = st.sidebar.text_input("👩🏻‍🏫 Course Name", "Batch - Course Name")
        day = st.sidebar.text_input("✨ Day", "Overall Day")

        # Upload files
        st.sidebar.header("🗃️ Upload Chat Files")
        st.sidebar.write("You can upload multiple files (e.g., Zoom Chat from Day 1 to Day 4)")
        uploaded_files = st.sidebar.file_uploader("Choose files", type=['txt'], accept_multiple_files=True)

        if uploaded_files:
            combined_data = pd.concat([extract_participants_and_messages(file.readlines()) for file in uploaded_files])

            # Extract participants and messages
            jumlah_pesan = combined_data.groupby("Participant").size().reset_index(name="Jumlah Pesan")

            # Most active participants plot
            st.subheader("Top 10 Most Active Participants")
            fig, ax = plt.subplots(figsize=(10, 6))
            orang_paling_aktif = jumlah_pesan.sort_values("Jumlah Pesan", ascending=False).head(10)
            orang_paling_aktif = orang_paling_aktif.sort_values("Jumlah Pesan", ascending=True).reset_index(drop=True)  # Reset index
            bars = ax.barh(orang_paling_aktif["Participant"], orang_paling_aktif["Jumlah Pesan"])
            ax.set_xlabel("Number of Messages")
            ax.set_ylabel("Participant")
            ax.set_title(f"Top 10 Most Active Participants - {course_name} {day}")
            for bar in bars:
                ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{bar.get_width():.0f}', 
                        va='center', ha='left', fontsize=10)
            st.pyplot(fig)

            # Print top 10 most active participants
            st.subheader("Top 10 Most Active Participants")
            st.write(orang_paling_aktif.sort_values("Jumlah Pesan", ascending=False)["Participant"].tolist())

            # Most silent participants plot
            st.subheader("Top 10 Most Silent Participants")
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            orang_paling_diam = jumlah_pesan.sort_values("Jumlah Pesan", ascending=True).head(10)
            orang_paling_diam = orang_paling_diam.sort_values("Jumlah Pesan", ascending=False).reset_index(drop=True)  # Reset index
            bars2 = ax2.barh(orang_paling_diam["Participant"], orang_paling_diam["Jumlah Pesan"], color='orange')
            ax2.set_xlabel("Number of Messages")
            ax2.set_ylabel("Participant")
            ax2.set_title(f"Top 10 Most Silent Participants - {course_name} {day}")
            for bar in bars2:
                ax2.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{bar.get_width():.0f}', 
                         va='center', ha='left', fontsize=10)
            st.pyplot(fig2)

            # Print top 10 most silent participants
            st.subheader("Top 10 Most Silent Participants")
            st.write(orang_paling_diam.sort_values("Jumlah Pesan", ascending=True)["Participant"].tolist())

            # Print DataFrames
            st.subheader("Chat Data Summary")
            st.write(combined_data)

            # Copy to clipboard button
            if st.button("Copy Data to Clipboard"):
                csv_data = combined_data.to_csv(index=False)
                st.write("Data copied to clipboard!")
                st.write(csv_data)
                df_bytes = io.BytesIO(csv_data.encode())
                st.download_button(
                    label="Download CSV",
                    data=df_bytes,
                    file_name="chat_data.csv",
                    mime="text/csv"
                )
    elif page == "Individual Analytics":
        state.page = "Individual Analytics"

        st.markdown("---")
        st.header("🫂Individual Analytics Page")
        # Upload files
        st.sidebar.header("🗃️ Upload Chat Files")
        st.sidebar.write("You can upload multiple files (e.g., Zoom Chat from Day 1 to Day 4)")
        uploaded_files = st.sidebar.file_uploader("Choose files", type=['txt'], accept_multiple_files=True)

        if uploaded_files:
            if state.participant_data is None:
                # Initialize an empty dictionary to store data for each participant
                participant_data = {}

                for file in uploaded_files:
                    # Use file name for meeting name
                    meeting_date = extract_date_from_filename(file.name)

                    # Extract chat data
                    chat_data = extract_participants_and_messages(file.readlines())

                    # Group participants by name and count messages
                    participant_summary = chat_data.groupby("Participant").size().reset_index(name="Message Count")

                    # Determine attendance and activity level for each participant
                    participant_summary["Attendance"] = "hadir"
                    participant_summary.loc[participant_summary["Message Count"] == 0, "Attendance"] = "tidak hadir"
                    participant_summary["Activity Level"] = "pasif"
                    participant_summary.loc[participant_summary["Message Count"] >= 9, "Activity Level"] = "aktif"
                    participant_summary.loc[(participant_summary["Message Count"] >= 3) & (participant_summary["Message Count"] < 9), "Activity Level"] = "kurang aktif"

                    # Combine attendance and activity level information
                    participant_summary["Summary"] = participant_summary["Attendance"] + ", " + participant_summary["Activity Level"]

                    # Add data for each participant to the dictionary
                    for _, row in participant_summary.iterrows():
                        participant_name = row["Participant"]
                        summary = f"{meeting_date}: {row['Summary']}"

                        if participant_name in participant_data:
                            participant_data[participant_name].append(summary)
                        else:
                            participant_data[participant_name] = [summary]

                state.participant_data = participant_data

            # Display participant data
            for participant, data in state.participant_data.items():
                st.subheader(participant)
                st.write("\n\n".join(data))

            # Copy data to clipboard button
            if st.button("Copy Summary to Clipboard"):
                formatted_summary = "\n\n".join(["{}:\n\n{}".format(participant, "\n\n".join(data)) for participant, data in participant_data.items()])
                pyperclip.copy(formatted_summary)
                # Inform user
                st.write("Data copied to clipboard!")

    # Footer
    st.markdown("""
    © 2024 [🏢 Algoritma](https://algorit.ma) | [💻 Github](https://github.com/product-rnd/zoom-chat-analyzer)
    """)

if __name__ == "__main__":
    main()
