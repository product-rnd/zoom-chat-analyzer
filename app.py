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
    date_match = re.search(r"GMT(\d{8})", filename) 
    if date_match:
        return date_match.group(1)
    else:
        return "Unknown Date"
    
def process_uploaded_files(uploaded_files):
    # Initialize an empty list to store participant data
    participant_data = []
    meeting_dates = {}

    sorted_files = sorted(uploaded_files, key=lambda x: extract_date_from_filename(x.name))
    chats_data = []

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
        chats_data.append(chat_data)

        # Group participants by name and count messages
        message_count = chat_data.groupby("Participant").size().reset_index(name="Message Count")

        # Split messages into reactions and regular messages
        chat_data['Is Reaction'] = chat_data['Message'].str.startswith('Reacted')
        reaction_count = chat_data[chat_data['Is Reaction']].groupby('Participant').size().reset_index(name='Reaction Count')
        chat_count = chat_data[~chat_data['Is Reaction']].groupby('Participant').size().reset_index(name='Chat Count')

        # Merge reaction and chat counts
        participant_data_day = pd.merge(message_count, reaction_count, on='Participant', how='left').fillna(0)
        participant_data_day = pd.merge(participant_data_day, chat_count, on='Participant', how='left').fillna(0)
        
        participant_data_day['Reaction Count'] = participant_data_day['Reaction Count'].astype(int)
        participant_data_day['Chat Count'] = participant_data_day['Chat Count'].astype(int)

        # Determine attendance and activity level for each participant
        participant_data_day["Attendance"] = "1"
        participant_data_day.loc[participant_data_day["Message Count"] == 0, "Attendance"] = "0"
        participant_data_day["Activity Level"] = "pasif"
        
        # Add day information
        participant_data_day["Day"] = day
        
        # Append participant data to list
        participant_data.append(participant_data_day)

    return participant_data, chats_data, meeting_dates

def main():
    st.title("💭 Zoom Chat Analyzer - Algoritma")
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

        # Upload chat files
        st.sidebar.header("🗃️ Upload Chat Files")
        st.sidebar.write("You can upload multiple files (e.g., Zoom Chat from Day 1 to Day 4)")
        uploaded_files = st.sidebar.file_uploader("Choose files", type=['txt'], accept_multiple_files=True)
        st.sidebar.markdown("⚠️ Make sure your filename is the original name of the downloaded Zoom chat. **Do not rename it**. It must contain `GMTYYYYMMDD` at least.")

        if uploaded_files:
            # Concatenate participant data for all days
            participant_data_raw, chats_data, meeting_dates = process_uploaded_files(uploaded_files=uploaded_files)
            participant_data_df = pd.concat(participant_data_raw)
            participant_data_grouped = participant_data_df.groupby('Participant').agg({
                'Message Count': 'sum',
                'Reaction Count': 'sum',
                'Chat Count': 'sum',
                'Attendance': 'count'
            })

            # Most active participants plot
            st.subheader("Top 10 Most Active Participants")
            fig, ax = plt.subplots(figsize=(10, 6))
            most_active_participants = participant_data_grouped.sort_values("Message Count", ascending=False).head(10)
            most_active_participants = most_active_participants.sort_values("Message Count", ascending=True).reset_index() 
            bars = ax.barh(most_active_participants["Participant"], most_active_participants["Message Count"])
            ax.set_xlabel("Number of Messages")
            ax.set_ylabel("Participant")
            ax.set_title(f"Top 10 Most Active Participants - {course_name}")
            for bar in bars:
                ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{bar.get_width():.0f}', 
                        va='center', ha='left', fontsize=10)
            st.pyplot(fig)

            # Print top 10 most active participants
            st.write(", ".join(f'{participant}' for participant in most_active_participants.sort_values("Message Count", ascending=False)["Participant"].tolist()))

            # Most silent participants plot
            st.subheader("Top 10 Most Silent Participants")
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            most_silent_participants = participant_data_grouped.sort_values("Message Count", ascending=True).head(10)
            most_silent_participants = most_silent_participants.sort_values("Message Count", ascending=False).reset_index()
            bars2 = ax2.barh(most_silent_participants["Participant"], most_silent_participants["Message Count"], color='orange')
            ax2.set_xlabel("Number of Messages")
            ax2.set_ylabel("Participant")
            ax2.set_title(f"Top 10 Most Silent Participants - {course_name} {day}")
            for bar in bars2:
                ax2.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{bar.get_width():.0f}', 
                         va='center', ha='left', fontsize=10)
            st.pyplot(fig2)

            # Print top 10 most silent participants
            st.write(", ".join(f'{participant}' for participant in most_silent_participants.sort_values("Message Count", ascending=True)["Participant"].tolist()))

            st.subheader("Participant Activity Sorted by Number of Messages")
            sorted_participant_data = participant_data_grouped.sort_values("Message Count", ascending=False).reset_index()
            st.write(sorted_participant_data)

            st.markdown("---")
            
            chats_data = pd.concat(chats_data)
            # Print DataFrames
            st.subheader("Chat Data Summary")
            st.write(chats_data)

            # Download CSV button
            csv_data = chats_data.to_csv(index=False)
            df_bytes = io.BytesIO(csv_data.encode())
            st.download_button(
                label="Download Chat Summary CSV",
                data=df_bytes,
                file_name="chat_summary.csv",
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

        if uploaded_files:
            # Initialize an empty list to store participant data
            participant_data_raw, combine, meeting_dates = process_uploaded_files(uploaded_files=uploaded_files)

            # Concatenate participant data for all days
            participant_data_df = pd.concat(participant_data_raw)

            # Iterate over unique dates
            for key, value in meeting_dates.items():
                st.write(f"{key}: {value}")

            # Define mean_chat_count_day and mean_reaction_count_day for criteria
            mean_chat_count_day = int(participant_data_df["Chat Count"].mean())
            mean_reaction_count_day = int(participant_data_df["Reaction Count"].mean())

            # Convert meeting_dates to a list of dates in order
            dates = list(meeting_dates.keys())

            # Initialize participant attendance dictionary with all participants starting from Day 1
            participants = set(participant_data_df["Participant"])
            participant_attendance = {participant: ["❌"] * len(dates) for participant in participants}

            # Loop through each participant to determine attendance for each day
            for participant in participants:
                for date in dates:
                    if date in participant_data_df.loc[participant_data_df["Participant"] == participant, "Day"].values:
                        day_index = dates.index(date)
                        participant_attendance[participant][day_index] = "✅"

            # Update the participant list if a new participant appears in later dates
            for date in dates:
                new_participants = participant_data_df.loc[participant_data_df["Day"] == date, "Participant"].unique()
                for new_participant in new_participants:
                    if new_participant not in participant_attendance:
                        participant_attendance[new_participant] = ["❌"] * dates.index(date) + ["✅"] + ["❌"] * (len(meeting_dates) - meeting_dates.index(date) - 1)

            # Create participant notes based on message count, reaction count, and attendance criteria
            participant_notes = []
            for participant, participant_data in participant_data_df.groupby("Participant"):
                attendance_notes = []
                activity_notes = []

                for date, attendance in zip(dates, participant_attendance[participant]):
                    # Check attendance
                    attendance_notes.append(f"{date}: {attendance}")

                    # Check message count criteria
                    day_data = participant_data[participant_data["Day"] == date]
                    if not day_data.empty:
                        message_count = day_data["Message Count"].values[0]
                        reaction_count = day_data["Reaction Count"].values[0]

                        if message_count >= mean_chat_count_day:
                            activity_notes.append(f"{date}: sangat aktif chat ({message_count})")
                        elif 3 <= message_count < mean_chat_count_day:
                            activity_notes.append(f"{date}: kurang aktif chat ({message_count})")
                        else:
                            activity_notes.append(f"{date}: pasif ({message_count})")

                        # Check reaction count criteria
                        if reaction_count >= mean_reaction_count_day:
                            responsiveness = f"responsif konfirmasi, {reaction_count} kali react"
                        elif 1 <= reaction_count < mean_chat_count_day:
                            responsiveness = "kurang responsif"
                        else:
                            responsiveness = "tidak responsif"

                        activity_notes[-1] += f" & {responsiveness}"
                    else:
                        activity_notes.append(f"{date}: tidak hadir atau tidak chat/react sama sekali")

                    if date != dates[-1]:
                        activity_notes.append("\n-")

                # Combine attendance and activity notes
                attendance_notes_str = " | ".join(attendance_notes)
                activity_notes_str = " ".join(activity_notes)

                # Overall notes for the participant
                overall_notes = f"Kehadiran\n{attendance_notes_str}\n\nNotes: \n- {activity_notes_str}"

                participant_notes.append({
                    "Name": participant,
                    "Notes": overall_notes
                })

            # Create DataFrame for participant notes
            participant_notes_df = pd.DataFrame(participant_notes)

            # Display participant notes in a table format
            st.subheader("Participant Notes")
            st.write(participant_notes_df)

            # Download CSV button
            csv_data = participant_notes_df.to_csv(index=False)
            df_bytes = io.BytesIO(csv_data.encode())
            st.download_button(
                label="Download Summary CSV",
                data=df_bytes,
                file_name="participant_notes.csv",
                mime="text/csv"
            )

            # Display participant notes in a table format
            st.subheader("Detail Rules Each Day")
            st.write("Students are considered active/responsive only if their chat_count is more than the mean message count in each meeting, and their reaction_count is more than the mean reaction count as well.")
            st.markdown("- Mean Message Count: " + str(mean_chat_count_day))
            st.markdown("- Mean Reaction Count: " + str(mean_reaction_count_day))

    # Footer
    st.markdown("""
    © 2024 [🏢 Algoritma](https://algorit.ma) | [💻 Github](https://github.com/product-rnd/zoom-chat-analyzer)
    """)

if __name__ == "__main__":
    main()
