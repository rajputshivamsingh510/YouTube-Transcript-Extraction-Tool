# YouTube Transcript Extraction Tool 📝

## 📌 Project Overview
This Python-based automation tool extracts transcripts from YouTube videos using Selenium WebDriver. It navigates through video pages, reveals the transcript panel (if available), scrapes each timestamped line, and exports the structured data into an Excel file.

This project is part of an internship submission to showcase web scraping, browser automation, and data processing skills.

---

## 🚀 Features
- Automated YouTube page interaction using Selenium
- Extracts full transcripts with timestamps
- Processes multiple video links from a Google Sheet (CSV format)
- Saves the output in a structured Excel file
- Handles dynamic and inconsistent page layouts gracefully

---

## 🔧 Technologies Used
- Python 3.x
- Selenium WebDriver
- pandas
- ChromeDriver

---

## 📂 Input
- A publicly accessible Google Sheet exported as CSV containing YouTube video links:
  ```
  https://docs.google.com/spreadsheets/d/.../export?format=csv
  ```

---

## 🔄 Workflow
1. Launch the Chrome browser with custom options to mimic real user behavior.
2. Load video URLs from a personal Google Sheet.
3. For each video:
   - Expand video description (if necessary)
   - Click "Show Transcript" button
   - Parse and extract timestamp-text pairs
4. Save results to `youtube_transcripts_output.xlsx`

---

## 🖼 Sample Output
```
0:00 - Transcriber: Joseph Geni Reviewer: Morton Bast...
0:12 - When I was 27 years old,...
0:13 - I left a very demanding job in management consulting...
```

---

## 📊 Output Format
Output is saved as an Excel file (`.xlsx`) with the following columns:
- `url`
- `timestamp`
- `text`

---

## ✅ Use Case
Ideal for:
- Content summarization
- Educational video indexing
- Podcast-to-text conversion
- Research automation

---

## 📃 License
This project is intended for academic and educational purposes only. Please respect YouTube's [Terms of Service](https://www.youtube.com/t/terms).

---

## 🙋 About Me
This project was created as part of my internship application. I am a Computer Science student passionate about automation, data engineering, and AI systems. Looking forward to applying my skills in impactful, real-world scenarios.
