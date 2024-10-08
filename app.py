import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import datetime

from preprocessing import SessionState, process_uploaded_files, get_students_spreadsheet, process_attendance_files, process_chat_notes, process_attendance_notes


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

        # Upload files
        st.sidebar.header("🗃️ Upload Chat Files")
        uploaded_files = st.sidebar.file_uploader("Download meeting chat files here: [Zoom Recording](https://zoom.us/recording)", type=['txt'], accept_multiple_files=True)

        # Upload Attendance
        st.sidebar.header("💻 Upload Attendance (🆕)")

        end_time = datetime.datetime.today()
        start_time = end_time - datetime.timedelta(days=5)

        attendance_files = st.sidebar.file_uploader(f"Download attendance files here: [Zoom Attendance Report](https://zoom.us/account/my/report?from={start_time.strftime('%m/%d/%Y')}&to={end_time.strftime('%m/%d/%Y')}#/)", type=['csv'], accept_multiple_files=True)

        st.sidebar.markdown("""
                            📝**Note**: 

                            - You can upload multiple files (e.g., Zoom Chat from Day 1 to Day 4)
                            - Make sure your Zoom chat filenames is the original name from the downloaded recording. **Do not rename it**. It must contain `GMTYYYYMMDD` at least.
                            - Even though attendance filenames is the same for each day, you don't have to rename it 
                            """)

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
            ax.set_title(f"Top 10 Most Active Participants")
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
            ax2.set_title(f"Top 10 Most Silent Participants")
            for bar in bars2:
                ax2.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{bar.get_width():.0f}', 
                         va='center', ha='left', fontsize=10)
            st.pyplot(fig2)

            # Print top 10 most silent participants
            st.write(", ".join(f'{participant}' for participant in most_silent_participants.sort_values("Message Count", ascending=True)["Participant"].tolist()))

            st.subheader("Participant Activity Sorted by Number of Messages")
            sorted_participant_data = participant_data_grouped.sort_values("Message Count", ascending=False).reset_index()
            st.dataframe(sorted_participant_data, use_container_width = True)

            st.markdown("---")
            
            chats_data = pd.concat(chats_data)
            # Print DataFrames
            st.subheader("Chat Data Summary")
            st.dataframe(chats_data, use_container_width = True)

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
        st.header("👨‍🎓 Individual Analytics Page")
        # Upload files
        st.sidebar.header("🗃️ Upload Chat Files")
        uploaded_files = st.sidebar.file_uploader("Download meeting chat files here: [Zoom Recording](https://zoom.us/recording)", type=['txt'], accept_multiple_files=True)

        # Upload Attendance
        st.sidebar.header("💻 Upload Attendance (🆕)")

        end_time = datetime.datetime.today()
        start_time = end_time - datetime.timedelta(days=5)

        attendance_files = st.sidebar.file_uploader(f"Download attendance files here: [Zoom Attendance Report](https://zoom.us/account/my/report?from={start_time.strftime('%m/%d/%Y')}&to={end_time.strftime('%m/%d/%Y')}#/)", type=['csv'], accept_multiple_files=True)

        st.sidebar.markdown("""
                            📝**Note**: 

                            - You can upload multiple files (e.g., Zoom Chat from Day 1 to Day 4)
                            - Make sure your Zoom chat filenames is the original name from the downloaded recording. **Do not rename it**. It must contain `GMTYYYYMMDD` at least.
                            - Even though attendance filenames is the same for each day, you don't have to rename it 
                            """)
        
        if uploaded_files and attendance_files:
            
            # Initialize an empty list to store participant data
            participant_data_raw, combine, meeting_dates = process_uploaded_files(uploaded_files=uploaded_files)
            
            # Get student's name from Schedule Workshop
            sheet_name = st.text_input("Input Students Sheet Name in [Schedule Workshop](https://docs.google.com/spreadsheets/d/1APwoLJ4lGGNnYhOfQ9AVF14f-aSmNDmAeA0PtMYwMIc)", value=f"Zeus Student")
            student_data = get_students_spreadsheet(sheet_name)

            # Create Chat notes based on Zoom recording 
            participant_notes_df, mean_chat_count_day, mean_reaction_count_day = process_chat_notes(participant_data_raw, meeting_dates)

            # Preprocess attendance files
            attendance = process_attendance_files(attendance_files)

            # Create Attendance note based on Zoom attendance report 
            participant_df = process_attendance_notes(attendance, student_data, participant_notes_df)

            # Display participant notes in a table format
            st.subheader("Participant Notes")
            st.dataframe(participant_df, use_container_width = True)

            # Iterate over unique dates
            st.write("📝 Note:")
            for key, value in meeting_dates.items():
                st.write(f"&nbsp;&nbsp;&nbsp;&nbsp; - {key}: {value}")

            # Display participant notes in a table format
            st.subheader("Detail Rules Each Day")
            st.write("Students are considered active/responsive only if their chat_count is more than the mean message count in each meeting, and their reaction_count is more than the mean reaction count as well.")
            st.markdown("- Mean Message Count: " + str(mean_chat_count_day))
            st.markdown("- Mean Reaction Count: " + str(mean_reaction_count_day))

        elif uploaded_files:
            # Initialize an empty list to store participant data
            participant_data_raw, combine, meeting_dates = process_uploaded_files(uploaded_files=uploaded_files)
            
            # Get student's name from Schedule Workshop
            sheet_name = st.text_input("Input Students Sheet Name in [Schedule Workshop](https://docs.google.com/spreadsheets/d/1APwoLJ4lGGNnYhOfQ9AVF14f-aSmNDmAeA0PtMYwMIc)", value=f"Zeus Student")
            student_data = get_students_spreadsheet(sheet_name)

            # Create Chat notes based on Zoom recording 
            participant_notes_df, mean_chat_count_day, mean_reaction_count_day = process_chat_notes(participant_data_raw, meeting_dates)

            # Display participant notes in a table format
            st.subheader("Participant Notes")
            st.dataframe(participant_notes_df, use_container_width = True)

            # Iterate over unique dates
            for key, value in meeting_dates.items():
                st.write(f"{key}: {value}")

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
