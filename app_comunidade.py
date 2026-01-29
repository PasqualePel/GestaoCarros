import streamlit as st
import pandas as pd
from datetime import datetime, time
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Gestão de Carros", layout="centered")

# --- COSTANTI ---
LISTA_CARROS = [
    "Rav 4", "Nissan Novo", "Nissan Velho", "Carrinha", "Nissan Vermelho"
]

LISTA_MISSIONARIOS = [
    "Pe. Roberto", "Pe. Marcio", "Pe. Stefano", "Pe. Antonio", 
    "Pe. Pasquale", "Pe. Massimo", "Dicson", "Carmen", 
    "Annamaria", "Felicia", "Diana", "Concy", "Marilda"
]

# --- CONNESSIONE A GOOGLE SHEETS ---
def get_google_sheet():
    """Si collega a Google Sheets usando il segreto salvato su Streamlit"""
    # Definiamo i permessi necessari
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Leggiamo la chiave JSON dai segreti di Streamlit
    json_creds = json.loads(st.secrets["gcp_json"])
    
    # Creiamo le credenziali
    creds = Credentials.from_service_account_info(json_creds, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Apriamo il foglio (assicurati che il nome sia ESATTO)
    sheet = client.open("Prenotazioni_Auto").sheet1
    return sheet

# --- FUNZIONI DI GESTIONE DATI ---

def carica_dati(sheet):
    """Scarica i dati dal foglio Google e li trasforma in tabella Pandas"""
    dati = sheet.get_all_records()
    
    if not dati:
        # Se il foglio è vuoto, ritorna dataframe vuoto
        return pd.DataFrame(columns=["Carro", "Missionario", "Inicio", "Fim"])
        
    df = pd.DataFrame(dati)
    
    # Convertiamo le stringhe in date vere per i calcoli
    # Gestiamo eventuali errori di formato se qualcuno tocca il foglio a mano
    try:
        df['Inicio'] = pd.to_datetime(df['Inicio'])
        df['Fim'] = pd.to_datetime(df['Fim'])
    except Exception as e:
        st.error(f"Errore nella lettura delle date dal foglio: {e}")
        
    return df

def salva_prenotazione(sheet, carro, missionario, inizio, fine):
    """Aggiunge una riga al foglio Google"""
    # Convertiamo le date in testo (stringa) per Google Sheets
    inizio_str = inizio.strftime("%Y-%m-%d %H:%M:%S")
    fine_str = fine.strftime("%Y-%m-%d %H:%M:%S")
    
    # Aggiungiamo la riga
    sheet.append_row([carro, missionario, inizio_str, fine_str])

def controlla_conflitti(df, carro, inizio_nuovo, fine_nuovo):
    """Controlla se l'auto è già occupata"""
    if df.empty:
        return False, None
        
    prenotazioni_auto = df[df['Carro'] == carro]
    
    for index, row in prenotazioni_auto.iterrows():
        inicio_esistente = row['Inicio']
        fim_esistente = row['Fim']
        
        # Logica sovrapposizione
        if inizio_nuovo < fim_esistente and fine_nuovo > inicio_esistente:
            return True, row['Missionario']
            
    return False, None

# --- INTERFACCIA UTENTE ---

st.title("🚗 Gestão de Carros da Comunidade")

# Tentativo di connessione
try:
    sheet = get_google_sheet()
    df_prenotazioni = carica_dati(sheet)
    connessione_ok = True
except Exception as e:
    st.error(f"Errore di connessione a Google Sheets: {e}")
    st.stop() # Ferma l'app se non si collega

# --- FORM PRENOTAZIONE ---
with st.container():
    st.subheader("Nova Reserva")
    
    col1, col2 = st.columns(2)
    with col1:
        missionario = st.selectbox("Quem vai utilizar?", LISTA_MISSIONARIOS)
        carro = st.selectbox("Qual carro?", LISTA_CARROS)
    
    with col2:
        d_inicio = st.date_input("Data de Início", datetime.today())
        t_inicio = st.time_input("Hora de Início", time(8, 0))
        d_fim = st.date_input("Data de Término", datetime.today())
        t_fim = st.time_input("Hora de Término", time(12, 0))

    dt_inicio = datetime.combine(d_inicio, t_inicio)
    dt_fim = datetime.combine(d_fim, t_fim)

    if st.button("Reservar Carro"):
        if dt_inicio >= dt_fim:
            st.error("Erro: A data/hora de término deve ser posterior ao início.")
        else:
            conflitto, nome_occupante = controlla_conflitti(df_prenotazioni, carro, dt_inicio, dt_fim)
            
            if conflitto:
                st.error(f"⚠️ O carro {carro} já está reservado por: {nome_occupante}!")
            else:
                with st.spinner('Salvando no Google Sheets...'):
                    salva_prenotazione(sheet, carro, missionario, dt_inicio, dt_fim)
                    st.success(f"Sucesso! {carro} reservado para {missionario}.")
                    st.balloons()
                    import time as t
                    t.sleep(2)
                    st.rerun()

# --- TABELLA ---
st.divider()
st.subheader("📅 Reservas Atuais (Google Sheets)")

if not df_prenotazioni.empty:
    df_visual = df_prenotazioni.sort_values(by="Inicio", ascending=False)
    # Formattazione per la visualizzazione
    df_visual['Inicio'] = df_visual['Inicio'].dt.strftime('%d/%m/%Y %H:%M')
    df_visual['Fim'] = df_visual['Fim'].dt.strftime('%d/%m/%Y %H:%M')
    st.dataframe(df_visual, use_container_width=True)
else:
    st.info("Nenhuma reserva encontrada.")


