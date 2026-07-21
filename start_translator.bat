@echo off
call venv\Scripts\activate
python run_client.py --model small --lang ja --enable_translation --target_language en
pause