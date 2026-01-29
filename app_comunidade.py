import streamlit as st
import pandas as pd
from datetime import datetime, time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Gestão de Carros", layout="centered")

# --- DATI (LISTE) ---
LISTA_CARROS = [
    "Rav 4",
    "Nissan Novo",
    "Nissan Velho",
    "Carrinha",
    "Nissan Vermelho"
]

LISTA_MISSIONARIOS = [
    "Pe. Roberto", "Pe. Marcio", "Pe. Stefano", "Pe. Antonio", 
    "Pe. Pasquale", "Pe. Massimo", "Dicson", "Carmen", 
    "Annamaria", "Felicia", "Diana", "Concy", "Marilda"
]

FILE_DATI = "prenotazioni.csv"

# --- FUNZIONI DI SUPPORTO ---

def carica_dati():
    """Carica le prenotazioni dal file CSV se esiste, altrimenti crea un DataFrame vuoto."""
    try:
        df = pd.read_csv(FILE_DATI)
        # Convertiamo le colonne di testo in veri oggetti data/ora
        df['Inicio'] = pd.to_datetime(df['Inicio'])
        df['Fim'] = pd.to_datetime(df['Fim'])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Carro", "Missionario", "Inicio", "Fim"])

def salva_dati(df):
    """Salva il DataFrame nel file CSV."""
    df.to_csv(FILE_DATI, index=False)

def controlla_conflitti(df, carro, inizio_nuovo, fine_nuovo):
    """
    Controlla se l'auto è già occupata in quel lasso di tempo.
    Ritorna True se c'è un conflitto, False se è libera.
    """
    # Filtriamo solo le prenotazioni di QUELLA auto
    prenotazioni_auto = df[df['Carro'] == carro]
    
    for index, row in prenotazioni_auto.iterrows():
        inicio_esistente = row['Inicio']
        fim_esistente = row['Fim']
        
        # Logica di sovrapposizione:
        # (Nuovo Inizio < Fine Esistente) E (Nuovo Fine > Inizio Esistente)
        if inizio_nuovo < fim_esistente and fine_nuovo > inicio_esistente:
            return True, row['Missionario'] # Ritorna chi ha prenotato
            
    return False, None

# --- INTERFACCIA UTENTE (PORTOGHESE) ---

st.title("🚗 Gestão de Carros da Comunidade")
st.write("Bem-vindo. Utilize este sistema para reservar um carro.")

# Carichiamo i dati esistenti
df_prenotazioni = carica_dati()

# --- SEZIONE PRENOTAZIONE (SIDEBAR O SOPRA) ---
with st.container():
    st.subheader("Nova Reserva")
    
    col1, col2 = st.columns(2)
    with col1:
        missionario = st.selectbox("Quem vai utilizar?", LISTA_MISSIONARIOS)
        carro = st.selectbox("Qual carro?", LISTA_CARROS)
    
    with col2:
        # Data e Ora Inizio
        d_inicio = st.date_input("Data de Início", datetime.today())
        t_inicio = st.time_input("Hora de Início", time(8, 0)) # Default 08:00
        
        # Data e Ora Fine
        d_fim = st.date_input("Data de Término", datetime.today())
        t_fim = st.time_input("Hora de Término", time(12, 0)) # Default 12:00

    # Combiniamo data e ora in un unico oggetto per il controllo
    dt_inicio = datetime.combine(d_inicio, t_inicio)
    dt_fim = datetime.combine(d_fim, t_fim)

    if st.button("Reservar Carro"):
        # 1. Validazione base
        if dt_inicio >= dt_fim:
            st.error("Erro: A data/hora de término deve ser posterior ao início.")
        else:
            # 2. Controllo Conflitti
            conflitto, nome_occupante = controlla_conflitti(df_prenotazioni, carro, dt_inicio, dt_fim)
            
            if conflitto:
                st.error(f"⚠️ O carro {carro} já está reservado nesse horário por: {nome_occupante}!")
            else:
                # 3. Salvataggio
                nuova_riga = {
                    "Carro": carro,
                    "Missionario": missionario,
                    "Inicio": dt_inicio,
                    "Fim": dt_fim
                }
                # Aggiungiamo la nuova riga usando concat (metodo moderno di pandas)
                df_prenotazioni = pd.concat([df_prenotazioni, pd.DataFrame([nuova_riga])], ignore_index=True)
                salva_dati(df_prenotazioni)
                st.success(f"Sucesso! {carro} reservado para {missionario}.")
                st.rerun() # Ricarica la pagina per mostrare la nuova lista

# --- VISUALIZZAZIONE LISTA PRENOTAZIONI ---
st.divider()
st.subheader("📅 Reservas Atuais")

if not df_prenotazioni.empty:
    # Ordiniamo per data di inizio
    df_visual = df_prenotazioni.sort_values(by="Inicio", ascending=False)
    
    # Formattiamo le date per renderle più leggibili in tabella
    df_visual['Inicio'] = df_visual['Inicio'].dt.strftime('%d/%m/%Y %H:%M')
    df_visual['Fim'] = df_visual['Fim'].dt.strftime('%d/%m/%Y %H:%M')
    
    st.dataframe(df_visual, use_container_width=True)
else:
    st.info("Nenhuma reserva encontrada.")