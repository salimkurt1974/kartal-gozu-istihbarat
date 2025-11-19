import os
import streamlit as st
from gnews import GNews
import pandas as pd
import plotly.express as px
import feedparser
import re
from deep_translator import GoogleTranslator
from textblob import TextBlob
from datetime import datetime, date
import time
import requests
from fpdf import FPDF
import base64
from newspaper import Article, Config
import sqlite3
import arxiv
import matplotlib.pyplot as plt

# --- GÜVENLİ İMPORT (WORDCLOUD) ---
try:
    from wordcloud import WordCloud
    WORDCLOUD_AKTIF = True
except ImportError:
    WORDCLOUD_AKTIF = False

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Kartal Gözü v15.0", layout="wide", page_icon="🦅")

# --- CSS TASARIM ---
st.markdown("""
<style>
    .risk-card { border-left: 6px solid #ff2b2b; background-color: #1e2130; padding: 15px; margin-bottom: 10px; border-radius: 8px; }
    .tech-card { border-left: 6px solid #00cc96; background-color: #182925; padding: 15px; margin-bottom: 10px; border-radius: 8px; }
    .neutral-card { border-left: 6px solid #808495; background-color: #1e2130; padding: 15px; margin-bottom: 10px; border-radius: 8px; }
    .stButton button { width: 100%; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🦅 Kartal Gözü: Teknoloji İstihbaratı")
    st.caption(f"Yalın Sürüm (v15.0) | Veritabanı: AKTİF | Saat: {datetime.now().strftime('%H:%M')}")
with c2:
    st.empty()
st.markdown("---")

# --- VERİTABANI YÖNETİMİ ---
def db_baglan(): return sqlite3.connect('istihbarat_master.db')

def tablo_olustur():
    conn = db_baglan()
    c = conn.cursor()
    # İstihbarat Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS haberler (id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, konu TEXT, baslik TEXT, ozet TEXT, durum TEXT, kaynak TEXT, link TEXT UNIQUE)''')
    # Basit Görev Listesi (Okuma Listesi)
    c.execute('''CREATE TABLE IF NOT EXISTS okuma_listesi (id INTEGER PRIMARY KEY AUTOINCREMENT, baslik TEXT, link TEXT, eklendigi_tarih DATE, durum TEXT)''')
    conn.commit()
    conn.close()

def veritabanina_kaydet(veri_listesi):
    conn = db_baglan()
    c = conn.cursor()
    eklenen = 0
    for veri in veri_listesi:
        try:
            standart_tarih = datetime.now().strftime("%Y-%m-%d") 
            c.execute('''INSERT INTO haberler (tarih, konu, baslik, ozet, durum, kaynak, link) VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                      (standart_tarih, veri['Konu'], veri['Başlık'], veri['Özet'], veri['Durum'], veri['Kaynak'], veri['Link']))
            eklenen += 1
        except sqlite3.IntegrityError: pass
    conn.commit()
    conn.close()
    return eklenen

def okuma_listesine_ekle(baslik, link):
    conn = db_baglan()
    c = conn.cursor()
    bugun = date.today()
    try:
        c.execute("INSERT INTO okuma_listesi (baslik, link, eklendigi_tarih, durum) VALUES (?, ?, ?, ?)", 
                  (baslik, link, bugun, "Okunacak"))
        conn.commit()
        sonuc = True
    except: sonuc = False
    conn.close()
    return sonuc

def gecmisi_getir():
    conn = db_baglan()
    df = pd.read_sql_query("SELECT * FROM haberler", conn)
    conn.close()
    if not df.empty:
        try:
            df['tarih'] = pd.to_datetime(df['tarih'], format='mixed', errors='coerce')
        except: pass 
    return df

def veritabani_sifirla():
    conn = db_baglan()
    c = conn.cursor()
    c.execute("DELETE FROM haberler")
    conn.commit()
    conn.close()

tablo_olustur()

# --- KAYNAKLAR ---
rss_kaynaklari = {
    "Defense News": "https://www.defensenews.com/arc/outboundfeeds/rss/",
    "Defense One": "https://www.defenseone.com/rss/all/",
    "Army Technology": "https://www.army-technology.com/feed/",
    "Breaking Defense": "https://breakingdefense.com/feed/"
}
KRITIK_RISK_KELIMELERI = ["breach", "casualty", "explosion", "attack", "threat", "crash", "violation", "danger", "warning", "conflict", "killed"]

# --- FONKSİYONLAR (ARAMA, ANALİZ, PDF) ---
def kelime_bulutu_olustur(df):
    if not WORDCLOUD_AKTIF: return None
    try:
        text = " ".join(str(baslik) for baslik in df.baslik)
        stopwords = set(["ve", "ile", "bir", "the", "in", "of", "to", "for", "on", "with", "is", "at", "by", "an", "as", "from", "new", "us", "report", "says", "defense", "security"])
        wordcloud = WordCloud(width=800, height=350, background_color='#0e1117', colormap='Reds', stopwords=stopwords).generate(text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        fig.patch.set_alpha(0) 
        return fig
    except: return None

def arxiv_tarama(konu_eng, limit=3):
    sonuclar = []
    try:
        search = arxiv.Search(query=f'"{konu_eng}"', max_results=limit, sort_by=arxiv.SortCriterion.SubmittedDate)
        for result in search.results():
            ozet = result.summary if result.summary else "Özet yok."
            baslik = result.title if result.title else "Başlıksız"
            sonuclar.append({'Durum': '🧪 AR-GE (ArXiv)', 'Konu': konu_eng, 'Başlık': baslik, 'Özet': ozet, 'Kaynak': 'ArXiv', 'Link': result.entry_id, 'Tam_Icerik': ozet})
    except: pass
    return sonuclar

def semantic_scholar_tarama(konu_eng, limit=3):
    sonuclar = []
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {'query': f"{konu_eng} defense", 'limit': limit, 'fields': 'title,abstract,url,year,venue'}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if 'data' in data:
            for paper in data['data']:
                ozet = paper.get('abstract', '')
                if not ozet: ozet = "Özet bilgisi sağlanmamış."
                baslik = paper.get('title', 'Başlıksız')
                link = paper.get('url', '')
                sonuclar.append({'Durum': '🧪 AR-GE (Semantic)', 'Konu': konu_eng, 'Başlık': baslik, 'Özet': ozet, 'Kaynak': 'Semantic Scholar', 'Link': link, 'Tam_Icerik': ozet})
    except: pass
    return sonuclar

def siteyi_oku_akilli(url, yedek_ozet):
    metin = ""
    try:
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0'
        config.request_timeout = 4
        article = Article(url, config=config)
        article.download()
        article.parse()
        metin = article.text
    except: pass
    if len(metin) < 100:
        kullanilacak_ozet = yedek_ozet if len(yedek_ozet) > 10 else "Özet bilgisi çekilemedi."
        return f"{kullanilacak_ozet}\n\n--- (Tam metin erişimi kısıtlı, stratejik özet gösterilmektedir) ---"
    return metin

def pdf_metin_temizle(text):
    if not isinstance(text, str): return str(text)
    text = text.replace("🔴", "[RISK] ").replace("🟢", "[FIRSAT] ").replace("🧪", "[AR-GE] ").replace("🟠", "[NEGATIF] ").replace("⚪", "[NOTR] ")
    replacements = {'ğ': 'g', 'Ğ': 'G', 'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C', '’': "'", '“': '"', '”': '"', '–': '-', '…': '...'}
    for turkce, latin in replacements.items(): text = text.replace(turkce, latin)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def pdf_olustur(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, txt="STRATEJIK ISTIHBARAT RAPORU", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, txt=f"Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    for index, row in dataframe.iterrows():
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(0, 51, 102)
        baslik = pdf_metin_temizle(f"{index+1}. {row['Başlık']}")
        pdf.multi_cell(0, 8, baslik)
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(100, 100, 100)
        meta = f"Durum: {pdf_metin_temizle(row['Durum'])} | Kaynak: {pdf_metin_temizle(row['Kaynak'])}"
        pdf.multi_cell(0, 6, meta)
        pdf.set_text_color(0, 0, 255)
        pdf.set_font("Arial", "U", 9)
        pdf.cell(0, 6, txt=">> ORJINAL KAYNAGA GITMEK ICIN TIKLAYINIZ <<", ln=True, link=row['Link'])
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(0, 0, 0)
        icerik = pdf_metin_temizle(row.get('Tam_Icerik', row['Özet']))
        pdf.multi_cell(0, 5, icerik[:3000])
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

def html_temizle(metin):
    if not metin: return ""
    return re.sub(re.compile('<.*?>'), '', metin)

def operasyonel_analiz(metin_eng):
    metin_lower = metin_eng.lower()
    for kelime in KRITIK_RISK_KELIMELERI:
        if kelime in metin_lower: return "🔴 KRİTİK RİSK"
    skor = TextBlob(metin_eng).sentiment.polarity
    if skor > 0.1: return "🟢 Fırsat"
    elif skor < -0.1: return "🟠 Negatif"
    else: return "⚪ Nötr"

def cevir_tr(metin):
    try:
        if not metin or len(metin) < 3: return str(metin)
        return GoogleTranslator(source='auto', target='tr').translate(metin[:999])
    except: return str(metin)

def convert_df(df): return df.to_csv(index=False).encode('utf-8-sig')

# --- SOL PANEL (KOMUTA KONTROL) ---
with st.sidebar:
    st.header("⚙️ İstihbarat Parametreleri")
    
    kaynak_turu = st.radio("Mod:", ["Hibrit (Tümü)", "Sadece RSS", "Sadece Google", "🧪 Sadece Akademik (Ar-Ge)"])
    
    nis_teknolojiler = ["Border security", "Quantum Ghost Imaging", "Passive Radar", "Neuromorphic Sensors", "Swarm Intelligence", "Cognitive Electronic Warfare", "Edge AI", "HAPS", "Li-Fi", "Metamaterials", "Solid-state Battery"]
    
    secilen_konular = st.multiselect("Hedef Konu:", nis_teknolojiler, default=["Quantum Ghost Imaging"])
    ozel_kelimeler = st.text_input("Özel Kelime:", placeholder="Örn: Hyperspectral")
    
    st.markdown("---")
    gun_araligi = st.slider("🕒 Geçmiş (Gün):", 1, 30, 3)
    web_oku = st.checkbox("🌍 Rapor Modu (PDF İçin)", value=True)
    arama_butonu = st.button("Analizi Başlat 🚀", type="primary")
    
    # --- (Sol Panel Kodunun En Altı) ---
    st.markdown("---")
    with st.expander("🗄️ Veritabanı Yönetimi"):
        # Veritabanı boyutunu hesapla
        try:
            db_size = os.path.getsize("istihbarat.db") / 1024 # KB
            st.caption(f"Veritabanı Boyutu: {db_size:.2f} KB")
        except: pass
        
        # Güvenli Silme (Onay Kutusu)
        onay = st.checkbox("Silme kilidini aç")
        if st.button("Tüm Verileri Sil", disabled=not onay):
            veritabani_sifirla()
            st.warning("Tüm istihbarat hafızası silindi!")
            time.sleep(1)
            st.rerun()

# --- ANA AKIŞ ---
if arama_butonu:
    final_liste = list(secilen_konular)
    if ozel_kelimeler:
        ekler = [k.strip() for k in ozel_kelimeler.split(',') if k.strip()]
        final_liste.extend(ekler)
    
    msg = st.toast(f"🛰️ Uydular yönlendiriliyor...", icon="📡")
    time.sleep(1)
    tum_veriler = []
    
    # 1. AKADEMİK
    if kaynak_turu in ["Hibrit (Tümü)", "🧪 Sadece Akademik (Ar-Ge)"]:
        msg.toast("🧪 Akademik veritabanları taranıyor...", icon="🔬")
        for konu in final_liste:
            try: konu_eng = GoogleTranslator(source='auto', target='en').translate(konu)
            except: konu_eng = konu
            
            makaleler_arxiv = arxiv_tarama(konu_eng, limit=2)
            for makale in makaleler_arxiv:
                makale['Başlık'] = cevir_tr(makale['Başlık'])
                ham_ozet = makale.get('Özet', '')
                makale['Özet'] = cevir_tr(ham_ozet[:600]) + "..." if ham_ozet else "Özet Yok."
                makale['Tam_Icerik'] = makale['Özet']
                tum_veriler.append(makale)
                
            makaleler_semantic = semantic_scholar_tarama(konu_eng, limit=2)
            for makale in makaleler_semantic:
                makale['Başlık'] = cevir_tr(makale['Başlık'])
                ham_ozet = makale.get('Özet', '')
                makale['Özet'] = cevir_tr(ham_ozet[:600]) + "..." if ham_ozet else "Özet Yok."
                makale['Tam_Icerik'] = makale['Özet']
                tum_veriler.append(makale)

    # 2. RSS
    if kaynak_turu in ["Hibrit (Tümü)", "Sadece RSS"]:
        msg.toast("📡 Haber kaynakları taranıyor...", icon="📰")
        for k_adi, url in rss_kaynaklari.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    full_text = (entry.title + " " + html_temizle(entry.get('summary', ''))).lower()
                    for konu in final_liste:
                        if konu.lower() in full_text:
                            durum = operasyonel_analiz(full_text)
                            baslik = cevir_tr(entry.title)
                            ozet_ham = html_temizle(entry.get('summary', ''))
                            if len(ozet_ham) < 10: ozet_ham = entry.title
                            ozet_tr = cevir_tr(ozet_ham)
                            tam_icerik = "Rapor modu kapalı."
                            if web_oku:
                                ham_icerik = siteyi_oku_akilli(entry.link, ozet_ham)
                                tam_icerik = cevir_tr(ham_icerik[:1500])
                            tum_veriler.append({'Durum': durum, 'Konu': konu, 'Başlık': baslik, 'Özet': ozet_tr, 'Tam_Icerik': tam_icerik, 'Kaynak': k_adi, 'Link': entry.link})
                            break
            except: continue
    
    # 3. GOOGLE
    if kaynak_turu in ["Hibrit (Tümü)", "Sadece Google"]:
        try:
            google_news = GNews(language='en', country='US', period=f'{gun_araligi}d', max_results=5)
            for konu in final_liste:
                results = google_news.get_news(konu)
                for item in results:
                    durum = operasyonel_analiz(item['title'])
                    baslik = cevir_tr(item['title'])
                    tam_icerik = "Rapor modu kapalı."
                    if web_oku:
                        msg.toast("Google taranıyor...", icon="🌐")
                        ham_icerik = siteyi_oku_akilli(item['url'], item['title']) 
                        tam_icerik = cevir_tr(ham_icerik[:1500])
                    tum_veriler.append({'Durum': durum, 'Konu': konu, 'Başlık': baslik, 'Özet': "Google News", 'Tam_Icerik': tam_icerik, 'Kaynak': item['publisher']['title'], 'Link': item['url']})
        except: pass

    if tum_veriler:
        yeni = veritabanina_kaydet(tum_veriler)
        msg.toast(f"✅ {yeni} kayıt arşive eklendi.", icon="💾")
        df_yeni = pd.DataFrame(tum_veriler)
        st.success(f"Tarama Bitti. {len(df_yeni)} yeni veri bulundu.")
        if web_oku:
            try:
                pdf_data = pdf_olustur(df_yeni)
                b64 = base64.b64encode(pdf_data).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="Istihbarat_Raporu.pdf" style="background-color:#cc0000; color:white; padding:10px; border-radius:5px; text-decoration:none;">📄 GÜNCEL RAPORU İNDİR (PDF)</a>'
                st.markdown(href, unsafe_allow_html=True)
            except Exception as e: st.error(f"PDF Hatası: {e}")

# --- EKRAN DÜZENİ ---
st.markdown("### 🗄️ İstihbarat Analiz Merkezi")
df_arsiv = gecmisi_getir()

if not df_arsiv.empty:
    tab1, tab2, tab3 = st.tabs(["☁️ KELİME BULUTU", "⚡ AKIŞ & GÖREVLER", "🧪 AR-GE"])

    with tab1:
        st.subheader("Gündem Analizi (Word Cloud)")
        if WORDCLOUD_AKTIF:
            df_cloud = df_arsiv.sort_values(by='id', ascending=False).head(100)
            fig_cloud = kelime_bulutu_olustur(df_cloud)
            if fig_cloud:
                st.pyplot(fig_cloud)
            else: st.warning("Veri yetersiz.")
        else: st.error("WordCloud modülü yüklü değil.")

    with tab2:
        st.subheader("İstihbarat Akışı")
        df_haber = df_arsiv[~df_arsiv['durum'].str.contains("AR-GE", na=False)].sort_values(by='id', ascending=False)
        
        for _, row in df_haber.iterrows():
            css = "neutral-card"
            if "KRİTİK" in row['durum']: css = "risk-card"
            elif "Fırsat" in row['durum']: css = "tech-card"
            
            c_text, c_btn = st.columns([5, 1])
            with c_text:
                st.markdown(f"""<div class="{css}"><small>{row['tarih']} | {row['kaynak']}</small><h4>{row['durum']} | {row['baslik']}</h4><a href="{row['link']}" target="_blank" style="color: #4da6ff;">Habere Git</a></div>""", unsafe_allow_html=True)
            with c_btn:
                st.write("")
                if st.button("📌 Kaydet", key=f"h_{row['id']}"):
                    okuma_listesine_ekle(row['baslik'], row['link'])
                    st.toast("Okuma listesine eklendi!", icon="✅")

    with tab3:
        st.subheader("Akademik Keşifler")
        df_arge = df_arsiv[df_arsiv['durum'].str.contains("AR-GE", na=False)].sort_values(by='id', ascending=False)
        if not df_arge.empty:
            for _, row in df_arge.iterrows():
                c_text, c_btn = st.columns([5, 1])
                with c_text:
                    st.markdown(f"""<div class="tech-card"><small style="color:#ffcc00">🧪 {row['kaynak']}</small><h4>{row['baslik']}</h4><p style="color:#ddd; font-size:14px;">{row['ozet']}</p><a href="{row['link']}" target="_blank" style="color: #fff;">📄 İncele</a></div>""", unsafe_allow_html=True)
                with c_btn:
                    st.write("")
                    if st.button("📌 Kaydet", key=f"a_{row['id']}"):
                        okuma_listesine_ekle(row['baslik'], row['link'])
                        st.toast("Ar-Ge görevi kaydedildi!", icon="🧪")
        else: st.warning("Veri yok.")
else:
    st.info("Veritabanı boş. Tarama başlatın.")