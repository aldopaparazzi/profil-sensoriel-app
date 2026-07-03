@echo off
echo 📊 Lancement du tableau de bord Profil Sensoriel...
py.exe -3.12 -m venv .venv
.venv\Scripts\activate
# pip install -r requirements.txt
pause
streamlit run app/dashboard.py --server.port 8501
pause