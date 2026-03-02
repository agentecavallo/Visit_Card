import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import urllib.parse

# 1. Configurazione API Gemini (legge la chiave in modo sicuro da Streamlit Cloud)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def analizza_biglietto(immagine):
    """Invia l'immagine a Gemini chiedendo ESATTAMENTE i 6 campi richiesti."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Estrai i dati da questo biglietto da visita e restituisci SOLO un JSON valido con queste chiavi. Non aggiungere markdown o altro testo:
    {
        "nome": "Solo il nome",
        "cognome": "Solo il cognome",
        "azienda": "Nome dell'azienda",
        "cellulare": "Numero di cellulare",
        "telefono_ufficio": "Numero di telefono fisso/ufficio",
        "email": "Indirizzo email"
    }
    Se un dato non è presente, lascia la stringa vuota "".
    """
    
    response = model.generate_content([prompt, immagine])
    testo_risposta = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(testo_risposta)

def genera_vcard(nome, cognome, azienda, cellulare, tel_ufficio, email):
    """Genera la vCard. Su Android, separare Nome e Cognome aiuta l'ordinamento in rubrica."""
    vcard = f"""BEGIN:VCARD
VERSION:3.0
N:{cognome};{nome};;;
FN:{nome} {cognome}
ORG:{azienda}
TEL;TYPE=CELL:{cellulare}
TEL;TYPE=WORK,VOICE:{tel_ufficio}
EMAIL;TYPE=WORK:{email}
END:VCARD"""
    return vcard

# --- INTERFACCIA OTTIMIZZATA PER MOBILE ---

st.set_page_config(page_title="Scanner Contatti", page_icon="📱", layout="centered")

st.title("📱 Aggiungi Contatto")

# Acquisizione Immagine
foto_scattata = st.camera_input("Scatta foto al biglietto")
file_caricato = st.file_uploader("O carica dalla galleria", type=["jpg", "png"])

immagine_da_analizzare = foto_scattata or file_caricato

if immagine_da_analizzare:
    img = Image.open(immagine_da_analizzare)
    
    if st.button("✨ ESTRAI DATI", type="primary", use_container_width=True):
        with st.spinner("Analisi in corso..."):
            try:
                dati = analizza_biglietto(img)
                st.session_state['dati_android'] = dati
                st.success("Dati estratti!")
            except Exception as e:
                st.error(f"Errore di lettura. Riprova. Dettagli: {e}")

# Visualizzazione e Modifica Dati
if 'dati_android' in st.session_state:
    d = st.session_state['dati_android']
    
    nome = st.text_input("Nome", value=d.get("nome", ""))
    cognome = st.text_input("Cognome", value=d.get("cognome", ""))
    azienda = st.text_input("Azienda", value=d.get("azienda", ""))
    cellulare = st.text_input("Cellulare", value=d.get("cellulare", ""))
    tel_ufficio = st.text_input("Telefono Ufficio", value=d.get("telefono_ufficio", ""))
    email = st.text_input("Email", value=d.get("email", ""))

    st.divider()
    
    # --- AZIONE 1: RUBRICA ---
    vcard_str = genera_vcard(nome, cognome, azienda, cellulare, tel_ufficio, email)
    nome_file = f"{nome}_{cognome}.vcf".replace(" ", "")
    
    st.download_button(
        label="💾 SALVA IN RUBRICA",
        data=vcard_str,
        file_name=nome_file,
        mime="text/vcard",
        use_container_width=True
    )

    st.divider()

    # --- AZIONE 2: EMAIL RAPIDA ---
    destinatario = st.text_input("Invia copia a:", placeholder="indirizzo@email.it")
    
    oggetto_email = f"Contatto: {nome} {cognome} - {azienda}"
    # Stile email asciutto e diretto
    corpo_email = f"Nuovo contatto:\n\nNome: {nome} {cognome}\nAzienda: {azienda}\nCellulare: {cellulare}\nUfficio: {tel_ufficio}\nEmail: {email}"
    
    oggetto_url = urllib.parse.quote(oggetto_email)
    corpo_url = urllib.parse.quote(corpo_email)
    link_mailto = f"mailto:{destinatario}?subject={oggetto_url}&body={corpo_url}"
    
    st.markdown(
        f'''
        <a href="{link_mailto}" target="_blank" style="text-decoration: none;">
            <div style="width: 100%; text-align: center; padding: 12px; background-color: #31333F; color: white; border-radius: 8px; font-weight: bold;">
                ✉️ INVIA PER EMAIL
            </div>
        </a>
        ''',
        unsafe_allow_html=True
    )
