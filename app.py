import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

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

def main():
    st.title("💭 Zoom Chat Analyzer")
    st.write("""
    📊 This app analyzes chat data and provides insights into the most active and silent participants.
    """)

    # Upload files
    st.sidebar.header("🗃️ Upload Chat Files")
    st.sidebar.write("You can upload multiple files (e.g., Zoom Chat from Day 1 to Day 4)")
    uploaded_files = st.sidebar.file_uploader("Choose files", type=['txt'], accept_multiple_files=True)

    # Course name and day input
    course_name = st.sidebar.text_input("👩🏻‍🏫 Course Name", "EDA")
    day = st.sidebar.text_input("✨ Day", "Day 4")

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
    # Footer
    st.markdown("""
    © 2024 Algoritma | [Github](https://github.com/finesaaa)
    """)

if __name__ == "__main__":
    main()