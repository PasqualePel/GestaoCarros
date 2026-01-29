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
        pass
        
    return df

def pulisci_prenotazioni_scadute(sheet, df):
    """Cancella dal foglio le prenotazioni passate"""
    if df.empty:
        return df

    # Prendiamo l'ora attuale
    adesso = datetime.now()
    
    # Filtriamo: teniamo SOLO le prenotazioni che finiscono nel futuro
    # (Cioè dove la data di fine è maggiore di adesso)
    df_future = df[df['Fim'] > adesso]
    
    # Se abbiamo cancellato qualcosa (cioè se c'erano righe vecchie)
    if len(df_future) < len(df):
        # 1. Puliamo tutto il foglio
        sheet.clear()
        
        # 2. Rimettiamo le intestazioni
        header = ["Carro", "Missionario", "Inicio", "Fim"]
        sheet.append_row(header)
        
        # 3. Rimettiamo solo i dati futuri
        # Dobbiamo riconvertire le date in testo per scriverle su Google Sheets
        if not df_future.empty:
            # Creiamo una copia per non rovinare il dataframe originale
            df_to_write = df_future.copy()
            df_to_write['Inicio'] = df_to_write['Inicio'].dt.strftime("%Y-%m-%d %H:%M:%S")
            df_to_write['Fim'] = df_to_write['Fim'].dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Scriviamo tutte le righe in un colpo solo (più veloce)
            sheet.append_rows(df_to_write.values.tolist())
            
        return df_future # Ritorniamo il dataframe pulito
    
    return df # Se non c'era nulla da cancellare, ritorniamo quello originale

def salva_prenotazione(sheet, carro, missionario, inizio, fine):
    """Aggiunge una riga al foglio Google"""
    inizio_str = inizio.strftime("%Y-%m-%d %H:%M:%S")
    fine_str = fine.strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([carro, missionario, inizio_str, fine_str])

def controlla_conflitti(df, carro, inizio_nuovo, fine_nuovo):
    """Controlla sovrapposizioni"""
    if df.empty:
        return False, None
        
    prenotazioni_auto = df[df['Carro'] == carro]
    
    for index, row in prenotazioni_auto.iterrows():
        try:
            inicio_esistente = row['Inicio']
            fim_esistente = row['Fim']
            
            if inizio_nuovo < fim_esistente and fine_nuovo > inicio_esistente:
                return True, row['Missionario']
        except:
            continue
            
    return False, None

# --- INTERFACCIA UTENTE ---

st.title("🚗 Gestão de Carros da Comunidade")

# Tentativo di connessione e caricamento
try:
    sheet = get_google_sheet()
    df_grezzo = carica_dati(sheet)
    
    # PULIZIA AUTOMATICA: Rimuove le vecchie prenotazioni dal foglio
    df_prenotazioni = pulisci_prenotazioni_scadute(sheet, df_grezzo)
    
except Exception as e:
    st.error(f"Errore di connessione o pulizia dati: {e}")
    st.stop()

# --- FORM PRENOTAZIONE ---
with st.container():
    st.subheader("Nova Reserva")
    
    col1, col2 = st.columns(2)
    with col1:
        # Ora la lista inizia con un campo vuoto
        missionario = st.selectbox("Quem vai utilizar?", LISTA_MISSIONARIOS)
        carro = st.selectbox("Qual carro?", LISTA_CARROS)
    
    with col2:
        # Abbiamo aggiunto format="DD/MM/YYYY" per avere giorno/mese/anno
        d_inicio = st.date_input("Data de Início", datetime.today(), format="DD/MM/YYYY")
        t_inicio = st.time_input("Hora de Início", time(8, 0))
        d_fim = st.date_input("Data de Término", datetime.today(), format="DD/MM/YYYY")
        t_fim = st.time_input("Hora de Término", time(12, 0))

    dt_inicio = datetime.combine(d_inicio, t_inicio)
    dt_fim = datetime.combine(d_fim, t_fim)

    if st.button("Reservar Carro"):
        # CONTROLLO 1: Campi vuoti
        if missionario == "" or carro == "":
            st.error("⚠️ Erro: Por favor, selecione o nome do Missionário e o Carro.")
        # CONTROLLO 2: Date incoerenti
        elif dt_inicio >= dt_fim:
            st.error("⚠️ Erro: A data/hora de término deve ser posterior ao início.")
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
st.subheader("📅 Reservas Futuras")

if not df_prenotazioni.empty:
    df_visual = df_prenotazioni.sort_values(by="Inicio", ascending=True)
    try:
        # Formattazione colonna tabella
        df_visual['Inicio'] = df_visual['Inicio'].dt.strftime('%d/%m/%Y %H:%M')
        df_visual['Fim'] = df_visual['Fim'].dt.strftime('%d/%m/%Y %H:%M')
    except:
        pass
    st.dataframe(df_visual, use_container_width=True)
else:
    st.info("Nenhuma reserva futura encontrada.")
