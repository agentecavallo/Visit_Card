import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import urllib.parse
import os

# Configurazione API Gemini (legge la chiave in modo sicuro da Streamlit Cloud)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def analizza_biglietto(immagine):
    """Invia l'immagine a Gemini chiedendo i 7 campi richiesti (incluso indirizzo)."""
    # Modello aggiornato per risolvere l'errore 404 e per una migliore analisi visiva
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = """
    Estrai i dati da questo biglietto da visita e restituisci SOLO un JSON valido con queste chiavi. Non aggiungere markdown o altro testo:
    {
        "nome": "Solo il nome",
        "cognome": "Solo il cognome",
        "azienda": "Nome dell'azienda",
        "cellulare": "Numero di cellulare",
        "telefono_ufficio": "Numero di telefono fisso/ufficio",
        "email": "Indirizzo email",
        "indirizzo": "Indirizzo completo (via, numero civico, CAP, città, provincia)"
    }
    Se un dato non è presente, lascia la stringa vuota "".
    """
    
    response = model.generate_content([prompt, immagine])
    testo_risposta = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(testo_risposta)

def genera_vcard(nome, cognome, azienda, cellulare, tel_ufficio, email, indirizzo):
    """Genera la vCard. Su Android, separare Nome e Cognome aiuta l'ordinamento in rubrica.
    Il campo ADR;TYPE=WORK è quello letto da Maps su Android per l'indirizzo."""
    vcard = f"""BEGIN:VCARD
VERSION:3.0
N:{cognome};{nome};;;
FN:{nome} {cognome}
ORG:{azienda}
TITLE:
TEL;TYPE=CELL:{cellulare}
TEL;TYPE=WORK,VOICE:{tel_ufficio}
EMAIL;TYPE=WORK:{email}
ADR;TYPE=WORK:;;{indirizzo};;;;
END:VCARD"""
    return vcard

# --- INTERFACCIA OTTIMIZZATA PER MOBILE ---

# Impostiamo il layout per adattarsi bene agli schermi stretti
st.set_page_config(page_title="Scanner Contatti", page_icon="📱", layout="centered")

st.title("📱 Aggiungi Contatto")

# --- FIRMA 'MICHELONE.JPG' DOPO IL TITOLO ---
# Raddoppiamo l'altezza a 120px e usiamo il filtro LANCZOS per non sgranare
target_height = 120
image_path = "michelone.jpg"

if os.path.exists(image_path):
    try:
        signature_img = Image.open(image_path)
        w, h = signature_img.size
        # Calcoliamo la nuova larghezza proporzionale
        target_width = int((target_height / h) * w)
        
        # Ridimensioniamo con filtro LANCZOS (altissima qualità)
        # Resampling.LANCZOS richiede Pillow >= 9.1.0; per versioni vecchie usare Image.ANTIALIAS
        resized_signature = signature_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Visualizziamo l'immagine nitida senza adattarla alla larghezza del contenitore
        st.image(resized_signature, use_container_width=False)
    except Exception as e:
        st.caption(f"(Firma michelone.jpg non caricabile: {e})")
else:
    # Mostriamo un avviso se l'immagine manca nel repository GitHub
    st.caption("(⚠️ Firma michelone.jpg mancante nel repository GitHub)")

st.divider()

st.write("Fai tap per caricare la foto o scattarne una nuova.")

# Acquisizione Immagine - Solo uploader (apre la fotocamera o la galleria nativa su Android)
file_caricato = st.file_uploader("Scegli immagine", type=["jpg", "png", "jpeg"])

if file_caricato:
    img = Image.open(file_caricato)
    
    if st.button("✨ ESTRAI DATI", type="primary", use_container_width=True):
        with st.spinner("Analisi in corso..."):
            try:
                # Chiamata a Gemini per l'estrazione dati
                dati = analizza_biglietto(img)
                st.session_state['dati_android'] = dati
                st.success("Dati estratti con successo!")
            except Exception as e:
                st.error(f"Errore di lettura. Riprova. Dettagli: {e}")

# Visualizzazione e Modifica Dati
if 'dati_android' in st.session_state:
    d = st.session_state['dati_android']
    
    st.markdown("### Controlla i dati")
    
    # Campi di input uno sotto l'altro per facilitare l'uso su mobile
    nome = st.text_input("Nome", value=d.get("nome", ""))
    cognome = st.text_input("Cognome", value=d.get("cognome", ""))
    azienda = st.text_input("Azienda", value=d.get("azienda", ""))
    indirizzo = st.text_input("Indirizzo", value=d.get("indirizzo", ""))
    cellulare = st.text_input("Cellulare", value=d.get("cellulare", ""))
    tel_ufficio = st.text_input("Telefono Ufficio", value=d.get("telefono_ufficio", ""))
    email = st.text_input("Email", value=d.get("email", ""))

    st.divider()
    
    # --- AZIONE 1: RUBRICA (vCard) ---
    vcard_str = genera_vcard(nome, cognome, azienda, cellulare, tel_ufficio, email, indirizzo)
    # Rimuoviamo gli spazi dal nome del file
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
    # Formattazione email asciutta e diretta
    corpo_email = f"Nuovo contatto:\n\nNome: {nome} {cognome}\nAzienda: {azienda}\nIndirizzo: {indirizzo}\nCellulare: {cellulare}\nUfficio: {tel_ufficio}\nEmail: {email}"
    
    oggetto_url = urllib.parse.quote(oggetto_email)
    corpo_url = urllib.parse.quote(corpo_email)
    # Creiamo il link mailto per aprire il client di posta predefinito
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
