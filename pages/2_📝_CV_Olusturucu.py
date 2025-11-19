import streamlit as st
from fpdf import FPDF
import base64
from PIL import Image
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="CV Komuta Merkezi", page_icon="📝", layout="wide")

# --- OTURUM YÖNETİMİ ---
if 'deneyimler' not in st.session_state:
    st.session_state['deneyimler'] = [
        {"role": "Military Assistant / Advisor to COS", "place": "NATO JFC | Naples, Italy", "year": "2021 - 2024", "desc": "Provided strategic risk analysis to Chief of Staff."},
        {"role": "Border Battalion Commander", "place": "Turkish Land Forces | Cukurca", "year": "2019 - 2021", "desc": "Commanded 24/7 counter-terrorism ops in high-threat zone."},
        {"role": "Project Manager (EU Funded)", "place": "Land Forces HQ | Ankara", "year": "2015 - 2019", "desc": "Managed 4 major EU border security projects."}
    ]
if 'profile_pic_data' not in st.session_state:
    st.session_state['profile_pic_data'] = None

# --- FONKSİYONLAR ---
def deneyim_ekle():
    st.session_state['deneyimler'].insert(0, {"role": "", "place": "", "year": "", "desc": ""})

def deneyim_sil(index):
    st.session_state['deneyimler'].pop(index)

# --- PDF MOTORU ---
class ModernPDF(FPDF):
    def clean_text(self, text):
        if not isinstance(text, str): return str(text)
        replacements = {'ğ': 'g', 'Ğ': 'G', 'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'}
        for tr, eng in replacements.items(): text = text.replace(tr, eng)
        return text.encode('latin-1', 'ignore').decode('latin-1')

    def create_cv(self, data, experiences, skills, profile_pic_path=None):
        self.add_page()
        
        # Üst Siyah Bar
        self.set_fill_color(10, 25, 47) 
        self.rect(0, 0, 210, 50, 'F')
        
        # Fotoğrafı Sağ Üste Ekle
        if profile_pic_path:
            self.image(profile_pic_path, x=170, y=10, w=25, h=25, type='PNG') # x, y, width, height
        
        # Başlık ve İsim
        self_x_after_pic = 10 if not profile_pic_path else 20
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.set_xy(self_x_after_pic, 15)
        self.cell(0, 10, self.clean_text(data['name']), 0, 1, 'L') # Sola Hizala
        
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, self.clean_text(data['title']), 0, 1, 'L')
        self.ln(5) # İsim ve unvan arasındaki boşluğu azalt

        # İletişim bilgileri
        self.set_text_color(200, 200, 200) # Açık gri
        self.set_font('Arial', '', 9)
        self.set_xy(self_x_after_pic, 40) # İletişim bilgilerini üst barın içine taşı
        self.cell(0, 5, self.clean_text(data['contact']), 0, 1, 'L')
        self.ln(10) # Barın dışına çıkmak için boşluk

        # Deneyimler
        self.set_font('Arial', 'B', 12)
        self.set_text_color(10, 25, 47)
        self.cell(0, 10, "PROFESSIONAL EXPERIENCE", 0, 1, 'L')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
        
        for exp in experiences:
            self.set_font('Arial', 'B', 11)
            self.set_text_color(0, 0, 0)
            self.cell(140, 8, self.clean_text(exp['role']))
            self.set_font('Arial', 'I', 10)
            self.cell(50, 8, self.clean_text(exp['year']), 0, 1, 'R')
            
            self.set_font('Arial', 'I', 10)
            self.set_text_color(80, 80, 80)
            self.cell(0, 6, self.clean_text(exp['place']), 0, 1)
            
            self.set_font('Arial', '', 10)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 5, self.clean_text(exp['desc']))
            self.ln(5)

        # Yetenekler
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(10, 25, 47)
        self.cell(0, 10, "KEY COMPETENCIES", 0, 1, 'L')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, self.clean_text(skills))
        
        return self.output(dest='S').encode('latin-1')

# --- ARAYÜZ ---
st.title("📝 CV Komuta Merkezi")

# --- KİMLİK BİLGİLERİ VE FOTOĞRAF ---
col_info, col_pic = st.columns([2, 1])

with col_info:
    name = st.text_input("Ad Soyad", "ISIM SOYISIM")
    title = st.text_input("Unvan", "SENIOR DEFENSE STRATEGIST")
    contact = st.text_input("İletişim", "Ankara | +90 5XX XXX XX XX")

with col_pic:
    st.write("Profil Fotoğrafı")
    uploaded_file = st.file_uploader("JPG/PNG Yükle", type=["jpg", "png"])

    if uploaded_file is not None:
        # Fotoğrafı byte olarak sakla
        st.session_state['profile_pic_data'] = uploaded_file.getvalue()
        st.image(uploaded_file, width=100) # Önizleme
    elif st.session_state['profile_pic_data'] is not None:
        # Daha önce yüklenmiş bir fotoğraf varsa göster
        st.image(st.session_state['profile_pic_data'], width=100)


st.markdown("---")

skills = st.text_area("Yetkinlikler", "Global Border Security, NATO Standards, Python, OSINT, Crisis Management, Strategic Planning", height=100)

st.markdown("---")
c_h, c_b = st.columns([4, 1])
with c_h: st.subheader("Deneyimler")
with c_b: 
    if st.button("➕ Yeni Ekle"):
        deneyim_ekle()
        st.rerun()

for i, exp in enumerate(st.session_state['deneyimler']):
    with st.expander(f"{exp['year']} | {exp['role']}", expanded=True):
        c1, c2 = st.columns(2)
        st.session_state['deneyimler'][i]['role'] = c1.text_input("Görev", exp['role'], key=f"r{i}")
        st.session_state['deneyimler'][i]['year'] = c2.text_input("Yıl", exp['year'], key=f"y{i}")
        st.session_state['deneyimler'][i]['place'] = st.text_input("Yer", exp['place'], key=f"p{i}")
        st.session_state['deneyimler'][i]['desc'] = st.text_area("Açıklama", exp['desc'], key=f"d{i}")
        if st.button("Sil", key=f"s{i}"):
            deneyim_sil(i)
            st.rerun()

st.markdown("---")
# --- PDF ÇIKTISI VE ÖNİZLEME (GÜNCELLENDİ) ---
st.markdown("---")
col_preview, col_download = st.columns([1, 1])

if st.button("CV'Yİ HAZIRLA VE GÖSTER", type="primary", use_container_width=True):
    data = {'name': name, 'title': title, 'contact': contact}
    
    # Fotoğraf İşleme (Aynı kalacak)
    profile_pic_path = None
    if st.session_state.get('profile_pic_data'):
        try:
            image = Image.open(io.BytesIO(st.session_state['profile_pic_data']))
            if image.mode in ("RGBA", "P"): image = image.convert("RGB")
            profile_pic_path = "temp_cv_photo.jpg"
            image.save(profile_pic_path)
        except: pass

    try:
        pdf = ModernPDF()
        pdf_data = pdf.create_cv(data, st.session_state['deneyimler'], skills, profile_pic_path)
        
        # 1. PDF'i Base64'e çevir (Hem indirme hem önizleme için)
        b64_pdf = base64.b64encode(pdf_data).decode('utf-8')

        # 2. İndirme Butonu Oluştur
        href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="CV_{name}.pdf" style="text-decoration:none; font-size:20px; background-color:#28a745; color:white; padding:10px 20px; border-radius:5px; display:block; text-align:center;">📥 PDF İNDİR</a>'
        
        # 3. Ekrana Bas
        st.success("CV Hazırlandı!")
        st.markdown(href, unsafe_allow_html=True)
        
        # 4. CANLI ÖNİZLEME (YENİ ÖZELLİK)
        st.markdown("### 📄 Canlı Önizleme")
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Hata: {e}")
    
    # Temizlik
    if profile_pic_path and os.path.exists(profile_pic_path):
        os.remove(profile_pic_path)