import pandas as pd
from datetime import datetime
import re
import streamlit as st

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

class SessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

@st.cache_data
def get_students_spreadsheet(sheet_name):
    SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly', # View your Google Classroom classes.
              'https://www.googleapis.com/auth/classroom.rosters', # Manage your Google Classroom class rosters.
              'https://www.googleapis.com/auth/classroom.profile.emails', # View the email addresses of people in your classes.
              'https://www.googleapis.com/auth/classroom.topics', #See, create, and edit topics in Google Classroom.
              'https://www.googleapis.com/auth/classroom.coursework.students', # Manage coursework and grades for students
              'https://www.googleapis.com/auth/classroom.courseworkmaterials', # See, edit, and create classwork materials in Google Classroom.
              'https://www.googleapis.com/auth/spreadsheets'] # See all your Google Sheets spreadsheets.

    creds = Credentials.from_authorized_user_info({"token": st.secrets['token'], 
                                                   "refresh_token": st.secrets['refresh_token'], 
                                                   "token_uri": "https://oauth2.googleapis.com/token", 
                                                   "client_id": st.secrets['client_id'], 
                                                   "client_secret": st.secrets['client_secret'], 
                                                   "scopes": ["https://www.googleapis.com/auth/classroom.courses.readonly", "https://www.googleapis.com/auth/classroom.rosters", "https://www.googleapis.com/auth/classroom.profile.emails", "https://www.googleapis.com/auth/classroom.topics", "https://www.googleapis.com/auth/classroom.coursework.students", "https://www.googleapis.com/auth/classroom.courseworkmaterials", "https://www.googleapis.com/auth/spreadsheets"], 
                                                   "expiry": "2024-02-05T10:21:31.547832Z"}, SCOPES)
    
    SHEET_ID = "1APwoLJ4lGGNnYhOfQ9AVF14f-aSmNDmAeA0PtMYwMIc" # Schedule Workshop
    SHEET_RANGE = f"{sheet_name}!A:L"

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets().values().batchGet(spreadsheetId=SHEET_ID,
                                                     ranges=SHEET_RANGE).execute()
    values = sheet.get('valueRanges', [])

    active = pd.DataFrame(values[0].get('values'))
    active = active.dropna(how="all").rename(columns=active.iloc[0]).drop(index=0)
    
    return active

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

@st.cache_data    
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


def name_check(real_name, zoom_names):
    '''
    Returns Zoom name from a student's real name or Missing if the real name isn't found
    '''
    intersect = {}
    for zoom_name in zoom_names:
        zoom_name = re.sub('[^\w]', ' ', zoom_name)
        real_set = set(real_name.lower().split())
        zoom_set = set(zoom_name.lower().split())

        if len(real_set.intersection(zoom_set)) > 0:
            intersect[zoom_name] = len(real_set.intersection(zoom_set))
        
    if intersect != {}:
        return max(intersect, key=intersect.get)
    else:
        return 'Missing'
    

def process_attendance_files(attendance_files):

    attendance_list = []
    for attendance_file in attendance_files:
        attendance_list.append(pd.read_csv(attendance_file))

    attendance = pd.concat(attendance_list)
    
    attendance['Join time'] = pd.to_datetime(attendance['Join time'], format='%m/%d/%Y %I:%M:%S %p')
    attendance['Leave time'] = pd.to_datetime(attendance['Leave time'], format='%m/%d/%Y %I:%M:%S %p')
    attendance = attendance.sort_values(by='Join time', ascending=True)
    attendance_agg = attendance.groupby([attendance['Join time'].dt.day_name(), 'Name (original name)'], sort=False).agg({
        'Email':'first',
        'Join time':'first',
        'Leave time':'last',
        'Duration (minutes)':'sum'
    })

    return attendance_agg


def process_chat_notes(participant_data_raw, meeting_dates):
    # Concatenate participant data for all days
    participant_data_df = pd.concat(participant_data_raw)

    # Define mean_chat_count_day and mean_reaction_count_day for criteria
    mean_chat_count_day = int(participant_data_df["Chat Count"].mean())
    mean_reaction_count_day = int(participant_data_df["Reaction Count"].mean())

    # Convert meeting_dates to a list of dates in order
    dates = list(meeting_dates.keys())

    # Create participant notes based on message count, reaction count, and attendance criteria
    participant_notes = []
    for participant, participant_data in participant_data_df.groupby("Participant"):
        activity_notes = []

        for date in dates:

            # Check message count criteria
            day_data = participant_data[participant_data["Day"] == date]
            if not day_data.empty:
                message_count = day_data["Message Count"].values[0]
                reaction_count = day_data["Reaction Count"].values[0]

                if message_count >= mean_chat_count_day:
                    activity_notes.append(f"{date}: Sangat aktif chat ({message_count})")
                elif 1 <= message_count < mean_chat_count_day:
                    activity_notes.append(f"{date}: Kurang aktif chat ({message_count})")
                else:
                    activity_notes.append(f"{date}: Pasif ({message_count})")

                # Check reaction count criteria
                if reaction_count >= mean_reaction_count_day:
                    responsiveness = f"aktif memberikan reaction ({reaction_count})"
                elif 1 <= reaction_count < mean_chat_count_day:
                    responsiveness = f"kurang aktif memberikan reaction ({reaction_count})"
                else:
                    responsiveness = "tidak memberikan reaction"

                activity_notes[-1] += f", {responsiveness}"
            else:
                activity_notes.append(f"{date}: Tidak chat/memberikan reaction sama sekali")

            if date != dates[-1]:
                activity_notes.append("\n-")

        # Combine attendance and activity notes
        activity_notes_str = " ".join(activity_notes)

        # Overall notes for the participant
        overall_notes = f"Notes: \n- {activity_notes_str}"

        participant_notes.append({
            "Name": participant,
            "Notes": overall_notes
        })

    participant_notes_df = pd.DataFrame(participant_notes)

    return participant_notes_df, mean_chat_count_day, mean_reaction_count_day

def process_attendance_notes(attendance, student_data, participant_notes_df):
    participant_list = []

    for nama_student in student_data['Name']:
        kehadiran_text = []
        chat_text = []

        for i, day in enumerate(attendance.index.get_level_values(0).unique()):
            participant_day = attendance.loc[day]
            if name_check(nama_student, participant_day.index) != 'Missing':
                kehadiran_text.append(f"Day {i+1}: ✅")

            else:
                kehadiran_text.append(f"Day {i+1}: ❌")

        overall_kehadiran = " | ".join(kehadiran_text)


        if name_check(nama_student, participant_notes_df['Name']) in participant_notes_df['Name'].tolist():
            overall_chat = participant_notes_df.loc[participant_notes_df['Name'] == name_check(nama_student, participant_notes_df['Name']), 'Notes'].values[0]
        elif ("✅" in overall_kehadiran) and ("❌" not in overall_kehadiran):
            overall_chat = "Notes: Selalu hadir namun tidak pernah mengirimkan chat/memberikan reaction (pasif)"
        elif ("✅" in overall_kehadiran) and ("❌" in overall_kehadiran):
            overall_chat = f"Notes: Hadir {overall_kehadiran.count('✅')} hari namun tidak pernah mengirimkan chat/memberikan reaction (pasif)" 
        else:
            overall_chat = "Notes: Tidak hadir sama sekali"

        participant_list.append({
            'Name':nama_student,
            'Notes':f"Kehadiran:\n{overall_kehadiran}\n\n{overall_chat}"
        })

    participant_df = pd.DataFrame(participant_list)

    return participant_df