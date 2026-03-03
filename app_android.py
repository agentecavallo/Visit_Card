import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import urllib.parse
import os

# Configurazione API Gemini (sicura tramite st.secrets)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def analizza_biglietto(immagine):
    """Invia l'immagine a Gemini 2.5 Flash per l'estrazione dati."""
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = """
    Estrai i dati da questo biglietto da visita e restituisci SOLO un JSON valido con queste chiavi:
    {
        "nome": "Solo il nome",
        "cognome": "Solo il cognome",
        "azienda": "Nome dell'azienda",
        "cellulare": "Numero di cellulare",
        "telefono_ufficio": "Numero di telefono fisso/ufficio",
        "email": "Indirizzo email",
        "indirizzo": "Indirizzo completo (via, numero civico, CAP, città, provincia)"
    }
    Se un dato non è presente, lascia la stringa vuota "". Non aggiungere markdown o altro testo.
    """
    
    response = model.generate_content([prompt, immagine])
    testo_risposta = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(testo_risposta)

def genera_vcard(nome, cognome, azienda, cellulare, tel_ufficio, email, indirizzo):
    """Genera la vCard ottimizzata per Android con indirizzo per Maps."""
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

# --- TITOLO E FIRMA SULLA STESSA LINEA ---
# Usiamo le colonne per affiancare il testo e l'immagine
col1, col2 = st.columns([2, 1], vertical_alignment="center")

with col1:
    st.title("📱 Aggiungi Contatto")

with col2:
    target_height = 120
    image_path = "michelone.jpg"
    
    if os.path.exists(image_path):
        try:
            signature_img = Image.open(image_path)
            w, h = signature_img.size
            target_width = int((target_height / h) * w)
            # Ridimensionamento ad alta qualità per evitare sgranature
            resized_signature = signature_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            st.image(resized_signature, use_container_width=False)
        except Exception:
            pass # Se l'immagine ha problemi, non mostriamo nulla per non rompere il layout
    else:
        st.caption("(Manca michelone.jpg)")

st.divider()
st.write("Fai tap per caricare o scattare la foto.")

# Caricamento immagine (Galleria o Fotocamera nativa Android)
file_caricato = st.file_uploader("Scegli immagine", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

if file_caricato:
    img = Image.open(file_caricato)
    
    if st.button("✨ ESTRAI DATI", type="primary", use_container_width=True):
        with st.spinner("Analisi in corso..."):
            try:
                dati = analizza_biglietto(img)
                st.session_state['dati_android'] = dati
                st.success("Dati estratti!")
            except Exception as e:
                st.error(f"Errore. Dettagli: {e}")

# Visualizzazione e Modifica Dati
if 'dati_android' in st.session_state:
    d = st.session_state['dati_android']
    
    st.markdown("### Controlla i dati")
    nome = st.text_input("Nome", value=d.get("nome", ""))
    cognome = st.text_input("Cognome", value=d.get("cognome", ""))
    azienda = st.text_input("Azienda", value=d.get("azienda", ""))
    indirizzo = st.text_input("Indirizzo", value=d.get("indirizzo", ""))
    cellulare = st.text_input("Cellulare", value=d.get("cellulare", ""))
    tel_ufficio = st.text_input("Telefono Ufficio", value=d.get("telefono_ufficio", ""))
    email = st.text_input("Email", value=d.get("email", ""))

    st.divider()
    
    # PULSANTE RUBRICA
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

    # PULSANTE EMAIL
    destinatario = st.text_input("Invia copia a:", placeholder="indirizzo@email.it")
    oggetto_url = urllib.parse.quote(f"Contatto: {nome} {cognome} - {azienda}")
    corpo_email = f"Nuovo contatto:\n\nNome: {nome} {cognome}\nAzienda: {azienda}\nIndirizzo: {indirizzo}\nCellulare: {cellulare}\nUfficio: {tel_ufficio}\nEmail: {email}"
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
