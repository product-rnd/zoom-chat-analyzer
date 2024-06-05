import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import pyperclip
from datetime import datetime
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
    st.title("💭 Zoom Chat Analyzer - Algoritma Product")
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

            # Split messages into reactions and regular messages
            combined_data['Is Reaction'] = combined_data['Message'].str.startswith('Reacted')
            reaction_count = combined_data[combined_data['Is Reaction']].groupby('Participant').size().reset_index(name='Reaction Count')
            chat_count = combined_data[~combined_data['Is Reaction']].groupby('Participant').size().reset_index(name='Chat Count')

            # Merge reaction and chat counts
            participant_data = pd.merge(jumlah_pesan, reaction_count, on='Participant', how='left').fillna(0)
            participant_data = pd.merge(participant_data, chat_count, on='Participant', how='left').fillna(0)
            participant_data['Reaction Count'] = participant_data['Reaction Count'].astype(int)
            participant_data['Chat Count'] = participant_data['Chat Count'].astype(int)

            st.subheader("Participant Activity Sorted by Number of Messages")
            sorted_participant_data = participant_data.sort_values("Jumlah Pesan", ascending=False).reset_index(drop=True)
            st.write(sorted_participant_data)

            # Most active participants plot
            st.subheader("Top 10 Most Active Participants")
            fig, ax = plt.subplots(figsize=(10, 6))
            orang_paling_aktif = participant_data.sort_values("Jumlah Pesan", ascending=False).head(10)
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
            orang_paling_diam = participant_data.sort_values("Jumlah Pesan", ascending=True).head(10)
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

            # Download CSV button
            csv_data = combined_data.to_csv(index=False)
            df_bytes = io.BytesIO(csv_data.encode())
            st.download_button(
                label="Download Summary CSV",
                data=df_bytes,
                file_name="participant_notes.csv",
                mime="text/csv"
            )

    elif page == "Individual Analytics":
        state.page = "Individual Analytics"

        st.markdown("---")
        st.header("🫂 Individual Analytics Page")
        # Upload files
        st.sidebar.header("🗃️ Upload Chat Files")
        st.sidebar.write("You can upload multiple files (e.g., Zoom Chat from Day 1 to Day 4)")
        uploaded_files = st.sidebar.file_uploader("Choose files", type=['txt'], accept_multiple_files=True)
        meeting_dates = {}

        if uploaded_files:
            if state.participant_data is None:
                # Initialize an empty list to store participant data
                participant_data = []

                sorted_files = sorted(uploaded_files, key=lambda x: extract_date_from_filename(x.name))
            
                for file_index, file in enumerate(sorted_files, start=1):
                    # Use file name for meeting name
                    meeting_date = extract_date_from_filename(file.name)
                    # Convert the meeting date string to a datetime object
                    meeting_date = datetime.strptime(meeting_date, "%Y%m%d")
                    # Format the meeting date as desired
                    formatted_date = meeting_date.strftime("%A, %d %B %Y")
                    meeting_dates[f"Day {file_index}"] = formatted_date

                    day = f"Day {file_index}"

                    # Extract chat data
                    chat_data = extract_participants_and_messages(file.readlines())

                    # Group participants by name and count messages
                    jumlah_pesan = chat_data.groupby("Participant").size().reset_index(name="Message Count")

                    # Split messages into reactions and regular messages
                    chat_data['Is Reaction'] = chat_data['Message'].str.startswith('Reacted')
                    reaction_count = chat_data[chat_data['Is Reaction']].groupby('Participant').size().reset_index(name='Reaction Count')
                    chat_count = chat_data[~chat_data['Is Reaction']].groupby('Participant').size().reset_index(name='Chat Count')

                    # Merge reaction and chat counts
                    participant_data_day = pd.merge(jumlah_pesan, reaction_count, on='Participant', how='left').fillna(0)
                    participant_data_day = pd.merge(participant_data_day, chat_count, on='Participant', how='left').fillna(0)
                    
                    participant_data_day['Reaction Count'] = participant_data_day['Reaction Count'].astype(int)
                    participant_data_day['Chat Count'] = participant_data_day['Chat Count'].astype(int)

                    mean_reaction_count = participant_data_day["Reaction Count"].mean()
                    mean_message_count = participant_data_day["Chat Count"].mean()

                    # Determine attendance and activity level for each participant
                    participant_data_day["Attendance"] = "1"
                    participant_data_day.loc[participant_data_day["Message Count"] == 0, "Attendance"] = "0"
                    participant_data_day["Activity Level"] = "pasif"
                    
                    participant_data_day.loc[participant_data_day["Message Count"] >= mean_message_count, "Activity Level"] = "sangat aktif"
                    participant_data_day.loc[(participant_data_day["Message Count"] >= 3) & (participant_data_day["Message Count"] < mean_message_count), "Activity Level"] = "kurang aktif"

                    # Add day information
                    participant_data_day["Day"] = day

                    # Append participant data to the list
                    participant_data.append(participant_data_day)

            # Concatenate participant data for all days
            participant_data_combined = pd.concat(participant_data)

            # Iterate over unique dates
            for key, value in meeting_dates.items():
                st.write(f"{key}: {value}")

             # Get the unique participants
            participants = participant_data_combined["Participant"].unique()

            # Create a dictionary to store participant attendance
            participant_attendance = {participant: [] for participant in participants}

            # Loop through each participant to determine attendance for each day
            for participant in participants:
                for day in range(1, len(uploaded_files) + 1):
                    day_str = f"Day {day}"
                    if day_str in participant_data_combined.loc[participant_data_combined["Participant"] == participant, "Day"].values:
                        participant_attendance[participant].append("✅")
                    else:
                        participant_attendance[participant].append("❌")

            # Create participant notes based on message count, reaction count, and attendance criteria
            notes = []
            for participant, participant_data in participant_data_combined.groupby("Participant"):
                attendance_notes = []
                activity_notes = []

                for index, (day, attendance) in enumerate(zip(participant_data["Day"], participant_attendance[participant])):
                    # Check attendance
                    attendance_notes.append(f"{day}: {attendance}")

                    # Check message count criteria
                    if attendance == "✅":
                        if participant_data["Message Count"].iloc[index] >= mean_message_count:
                            activity_notes.append(f"{day}: cukup aktif ({participant_data['Message Count'].iloc[index]})")
                        elif 3 <= participant_data["Message Count"].iloc[index] < mean_message_count:
                            activity_notes.append(f"{day}: kurang aktif ({participant_data['Message Count'].iloc[index]})")
                        else:
                            activity_notes.append(f"{day}: pasif ({participant_data['Message Count'].iloc[index]})")
                    else:
                        activity_notes.append(f"{day}: tidak hadir")

                    # Check reaction count criteria
                    if participant_data["Reaction Count"].iloc[index] >= mean_reaction_count:
                        responsiveness = "tidak responsif"
                    else:
                        responsiveness = "responsif, selalu react jika konfirmasi"

                    # Determine overall activity level
                    if attendance == "✅":
                        activity_notes[-1] += f" & {responsiveness}"
                    else:
                        activity_notes[-1] += " & tidak responsif"

                    if (index != len(participant_data["Day"]) - 1):
                        activity_notes.append("\n-")

                # Combine attendance and activity notes
                attendance_notes_str = " | ".join(attendance_notes)
                activity_notes_str = " ".join(activity_notes)

                # Overall notes for the participant
                overall_notes = f"Kehadiran\n{attendance_notes_str}\n\nNotes Overall: \n- {activity_notes_str}"

                notes.append({
                    "Name": participant,
                    "Notes": overall_notes
                })

            # Create DataFrame for participant notes
            notes_df = pd.DataFrame(notes)

            # Display participant notes in a table format
            st.subheader("Participant Notes")
            st.write(notes_df)

            # Download CSV button
            csv_data = notes_df.to_csv(index=False)
            df_bytes = io.BytesIO(csv_data.encode())
            st.download_button(
                label="Download Summary CSV",
                data=df_bytes,
                file_name="participant_notes.csv",
                mime="text/csv"
            )


    # Footer
    st.markdown("""
    © 2024 [🏢 Algoritma](https://algorit.ma) | [💻 Github](https://github.com/product-rnd/zoom-chat-analyzer)
    """)

if __name__ == "__main__":
    main()
