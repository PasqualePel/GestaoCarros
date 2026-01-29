import streamlit as st
import pandas as pd
from datetime import datetime, time
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Gestão de Carros", layout="centered")

# --- COSTANTI ---
# Aggiungiamo una stringa vuota all'inizio per lasciare il campo bianco
LISTA_CARROS = [
    "", "Rav 4", "Nissan Novo", "Nissan Velho", "Carrinha", "Nissan Vermelho"
]

# Ho aggiunto "Gisele" in fondo alla lista
LISTA_MISSIONARIOS = [
    "", "Pe. Roberto", "Pe. Marcio", "Pe. Stefano", "Pe. Antonio", 
    "Pe. Pasquale", "Pe. Massimo", "Dicson", "Carmen", 
    "Annamaria", "Felicia", "Diana", "Concy", "Marilda", "Gisele"
]

# --- CONNESSIONE A GOOGLE SHEETS ---
def get_google_sheet():
    """Si collega a Google Sheets usando il segreto salvato su Streamlit"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    json_creds = json.loads(st.secrets["gcp_json"])
    creds = Credentials.from_service_account_info(json_creds, scopes=scopes)
    client = gspread.authorize(creds)
    
    # ID del tuo foglio
    sheet_id = "1ZzFjPgqy4aMCS7lUK3AHAx7HMdPaH8jRnZDGgi8e7BU"
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet

# --- FUNZIONI DI GESTIONE DATI ---

def carica_dati(sheet):
    """Scarica i dati e gestisce le date"""
    dati = sheet.get_all_records()
    
    if not dati:
        return pd.DataFrame(columns=["Carro", "Missionario", "Inicio", "Fim"])
        
    df = pd.DataFrame(dati)
    
    # Convertiamo le colonne in formato data
    try:
        df['Inicio'] = pd.to_datetime(df['Inicio'])
        df['Fim'] = pd.to_datetime(df['Fim'])
    except Exception:
