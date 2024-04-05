# Zoom Chat Analyzer
📊 Chat Analyzer is a Streamlit-based web application that allows you to analyze chat data from text files. It provides insights into the most active and silent participants in the chat.

🎯 Algoritma (algorit.ma) purposes.

## Features

- 🔬 Analyze chat data from text files.
- 🔎 Identify the most active and silent participants.
- 📊 Visualize chat statistics with interactive plots.
- 📥 Copy chat data to clipboard or download as CSV.

## How to Use

1. **Upload Files:**
   - Click on the "Choose File" button to upload one or multiple chat files. Supported file format: .txt.

2. **Input Course Details:**
   - Enter the course name and day information in the sidebar.

3. **Analysis:**
   - After uploading the file(s) and providing course details, the app will analyze the chat data.
   - It will display two plots:
     - Top 10 Most Active Participants.
     - Top 10 Most Silent Participants.
   - Additionally, the app will print the top 10 most active and silent participant names.

4. **Data Summary:**
   - Below the plots, you can find a summary of the chat data.
   - It includes timestamps, participants, and messages.

5. **Copy or Download Data:**
   - You can copy the chat data to your clipboard or download it as a CSV file.

6. **Feedback:**
   - We welcome your feedback! Feel free to reach out with any questions or suggestions.

## Installation

To run this app locally, make sure you have Python installed. Then, follow these steps:

1. Clone this repository:
   ```
   git clone https://github.com/product-rnd/zoom-chat-analyzer.git
   ```

2. Navigate to the project directory:
   ```
   cd zoom-chat-analyzer
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

5. Access the app in your browser at `http://localhost:8501`.

## Example Chat Data

You can use the provided example chat data file (`GMT20240816.txt`) to test the application.
⚠️ Ensure that the file names follow the format "GMT+DATE.txt" where "DATE" represents the date in any specific format.

```
00:24:39    [Instructor] Alexander Graham Bell:   sore Bu
00:33:28    [TA] Marie Curie:    Iya sama sama Bu
01:25:50    [TA] Leonardo da Vinci:    Selamat datang di kelas EDA Day 4, Yoda Night Online. Berikut pranala kelas yang perlu dipersiapkan:...
01:37:36    [TA] Albert Einstein:  😀
01:37:52    J. Robert Oppenheimer Zoom (Laptop):   Reacted to "😀" with 🤣
01:46:25    Issac Newton:    household_new[(household_new['year'] == 2018)]
01:46:47    [TA] J. Robert Oppenheimer:  Reacted to "household_new[(household..." with 👏
01:48:34    B. J. Habibie:    karena data household_new yang originalnya akan keoverwrite
01:48:40    Issac Newton:    data awalnya berubah
02:00:25    J. Robert Oppenheimer Zoom (Laptop):   minimarket total sales nya sangat mendominasi dibandingkan format penjualan yg lain
02:02:05    Roberto Mario Uta:   Reacted to "kalau gak makan nasi..." with 😂
02:02:05    Arthur Scherbius:   Reacted to "kalau gak makan nasi..." with 🤣
```

## Credits

- Developed by RnD Product Team - Algoritma
- © 2024 Algoritma