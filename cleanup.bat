@echo off
REM Pastebin Cleanup Task
REM Run this script periodically to clean up old pastes (older than 5 days)

cd /d "c:\Users\ravibh\Desktop\pastebin"
python cleanup.py >> cleanup.log 2>&1

REM You can schedule this batch file to run daily using Windows Task Scheduler:
REM 1. Open Task Scheduler
REM 2. Create Basic Task
REM 3. Name: "Pastebin Cleanup"
REM 4. Trigger: Daily
REM 5. Action: Start a program - Browse to this .bat file
REM 6. Finish
