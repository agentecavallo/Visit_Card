import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import urllib.parse
import os # Importiamo os per verificare se il file immagine esiste

# Configurazione API Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def analizza_biglietto(immagine):
    """Invia l'immagine a Gemini chiedendo i 7 campi richiesti (incluso indirizzo)."""
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
    """Genera la vCard. Il campo ADR;TYPE=WORK è quello letto da Maps su Android."""
    vcard = f"""BEGIN:VCARD
VERSION:3.0
N:{cognome};{nome};;;
FN:{nome} {cognome}
ORG:{azienda}
TEL;TYPE=CELL:{cellulare}
TEL;TYPE=WORK,VOICE:{tel_ufficio}
EMAIL;TYPE=WORK:{email}
ADR;TYPE=WORK:;;{indirizzo};;;;
END:VCARD"""
    return vcard

# --- INTERFACCIA OTTIMIZZATA PER MOBILE ---

st.set_page_config(page_title="Scanner Contatti", page_icon="📱", layout="centered")

st.title("📱 Aggiungi Contatto")

# --- FIRMA 'MICHELONE.JPG' DOPO IL TITOLO ---
# Il trucchetto per non sgranare: usiamo Pillow per ridimensionare 
# con alta qualità (filtro LANCZOS) prima di passarla a Streamlit
target_height = 60
image_path = "michelone.jpg"

if os.path.exists(image_path):
    try:
        # Apriamo l'immagine originale
        signature_img = Image.open(image_path)
        # Calcoliamo la larghezza proporzionale per mantenere le proporzioni
        w, h = signature_img.size
        # Calcoliamo la nuova larghezza mantenendo l'altezza a 60px
        target_width = int((target_height / h) * w)
        
        # Ridimensioniamo con filtro LANCZOS (altissima qualità)
        # Resampling.LANCZOS è disponibile nelle versioni Pillow >= 9.1.0
        # Se hai una versione vecchia, potrebbe servire Image.ANTIALIAS
        resized_signature = signature_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Visualizziamo l'immagine nitida. Usiamo use_container_width=False 
        # perché abbiamo già fissato la dimensione esatta.
        st.image(resized_signature, use_container_width=False)
    except Exception as e:
        st.caption(f"(Firma michelone.jpg non caricabile: {e})")
else:
    # Se il file non esiste ancora sul repository GitHub, mostriamo un avviso
    st.caption("(⚠️ Firma michelone.jpg mancante nel repository GitHub)")

st.divider()

st.write("Fai tap per caricare la foto o scattarne una nuova.")

# Acquisizione Immagine - Solo uploader
file_caricato = st.file_uploader("Scegli immagine", type=["jpg", "png", "jpeg"])

if file_caricato:
    img = Image.open(file_caricato)
    
    if st.button("✨ ESTRAI DATI", type="primary", use_container_width=True):
        with st.spinner("Analisi in corso..."):
            try:
                dati = analizza_biglietto(img)
                st.session_state['dati_android'] = dati
                st.success("Dati estratti con successo!")
            except Exception as e:
                st.error(f"Errore di lettura. Riprova. Dettagli: {e}")

# Visualizzazione e Modifica Dati
if 'dati_android' in st.session_state:
    d = st.session_state['dati_android']
    
    nome = st.text_input("Nome", value=d.get("nome", ""))
    cognome = st.text_input("Cognome", value=d.get("cognome", ""))
    azienda = st.text_input("Azienda", value=d.get("azienda", ""))
    indirizzo = st.text_input("Indirizzo", value=d.get("indirizzo", ""))
    cellulare = st.text_input("Cellulare", value=d.get("cellulare", ""))
    tel_ufficio = st.text_input("Telefono Ufficio", value=d.get("telefono_ufficio", ""))
    email = st.text_input("Email", value=d.get("email", ""))

    st.divider()
    
    # --- AZIONE 1: RUBRICA ---
    vcard_str = genera_vcard(nome, cognome, azienda, cellulare, tel_ufficio, email, indirizzo)
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
    corpo_email = f"Nuovo contatto:\n\nNome: {nome} {cognome}\nAzienda: {azienda}\nIndirizzo: {indirizzo}\nCellulare: {cellulare}\nUfficio: {tel_ufficio}\nEmail: {email}"
    
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
