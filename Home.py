import streamlit as st
import sqlite3
import os
from datetime import datetime

# --- SAYFA AYARLARI ---
# --- MEVCUT KODLARINIZIN ALTINA (BAŞLIKTAN SONRA) ŞUNU EKLEYİN ---

# HEDEF TARİHİ
hedef_tarih = datetime(2028, 8, 30) # 30 Ağustos 2028
bugun = datetime.now()
kalan = hedef_tarih - bugun

# --- CANLI DURUM PANELİ (YENİ) ---
st.info(f"🎯 **BÜYÜK HEDEF:** 30 Ağustos 2028 | ⏳ **Kalan Süre:** {kalan.days} Gün")

# İstatistikler (Veritabanından Canlı Veri)
conn = sqlite3.connect('istihbarat.db')
c = conn.cursor()
try:
    # Eğer tablolar henüz yoksa hata vermesin diye try-except
    c.execute("SELECT Count(*) FROM haberler")
    haber_sayisi = c.fetchone()[0]
    c.execute("SELECT Count(*) FROM ajanda WHERE durum='Yapılacak'")
    gorev_sayisi = c.fetchone()[0]
except:
    haber_sayisi = 0
    gorev_sayisi = 0
conn.close()

# Metrikler
m1, m2, m3 = st.columns(3)
m1.metric("Toplanan İstihbarat", f"{haber_sayisi} Adet", "Veritabanı Aktif")
m2.metric("Bekleyen Görevler", f"{gorev_sayisi} Adet", "Ajanda Entegre")
m3.metric("Sistem Durumu", "ONLINE", "v15.0")

st.markdown("---")
# --- (Buradan sonra mevcut modül kartları kodunuz devam etsin) ---
st.set_page_config(
    page_title="Entegre Komuta Merkezi",
    page_icon="🇹🇷",
    layout="wide"
)

# --- CSS TASARIM ---
st.markdown("""
<style>
    .main-header {font-size: 40px; font-weight: bold; color: #4da6ff; text-align: center; margin-bottom: 10px;}
    .status-card {background-color: #1e2130; padding: 20px; border-radius: 10px; border: 1px solid #30334e; text-align: center;}
    .module-card {
        background-color: #262730; padding: 20px; border-radius: 10px; 
        border-left: 5px solid #00cc96; margin-bottom: 20px;
        transition: transform 0.3s;
    }
    .module-card:hover {transform: scale(1.02); border-left: 5px solid #4da6ff;}
</style>
""", unsafe_allow_html=True)

# --- SİSTEM DURUM KONTROLÜ ---
def sistem_kontrolu():
    durum = {"db": False, "db_size": 0}
    if os.path.exists("istihbarat.db"):
        durum["db"] = True
        durum["db_size"] = os.path.getsize("istihbarat.db") / 1024 # KB cinsinden
    return durum

durum = sistem_kontrolu()

# --- BAŞLIK ---
st.markdown('<div class="main-header">🇹🇷 ENTEGRE KOMUTA KONTROL MERKEZİ</div>', unsafe_allow_html=True)
st.markdown(f"<div style='text-align: center; color: gray;'>Sistem Saati: {datetime.now().strftime('%d %B %Y - %H:%M')}</div>", unsafe_allow_html=True)
st.markdown("---")

# --- DURUM METRİKLERİ ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="status-card">
        <h3 style="margin:0">Veritabanı</h3>
        <p style="font-size: 24px; color: {'#00cc96' if durum['db'] else '#ff4b4b'}">{'AKTİF' if durum['db'] else 'PASİF'}</p>
        <small>Boyut: {durum['db_size']:.2f} KB</small>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="status-card">
        <h3 style="margin:0">Operasyonel Modüller</h3>
        <p style="font-size: 24px; color: #4da6ff">3 ADET</p>
        <small>İstihbarat | CV | Rota</small>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="status-card">
        <h3 style="margin:0">Hedef Tarih</h3>
        <p style="font-size: 24px; color: #ffa500">AĞUSTOS 2028</p>
        <small>Kalan: ~3 Yıl</small>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- MODÜL TANITIMLARI ---
st.subheader("🚀 Operasyonel Modüller")
st.info("👈 Sol taraftaki menüden ilgili modülü seçerek göreve başlayabilirsiniz.")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="module-card">
        <h3>🦅 Teknoloji İstihbaratı</h3>
        <p><b>Görev:</b> Global ve akademik kaynaklardan (ArXiv, Google, RSS) veri toplar, veritabanına işler ve trend analizi yapar.</p>
        <ul>
            <li>Haber Takibi</li>
            <li>Akademik Ar-Ge Tarama</li>
            <li>Gelecek Tahmini (AI)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="module-card">
        <h3>📝 CV Komuta Merkezi</h3>
        <p><b>Görev:</b> Dinamik, fotoğraflı ve uluslararası standartlarda profesyonel özgeçmiş oluşturur ve PDF olarak basar.</p>
        <ul>
            <li>Dinamik Deneyim Ekleme</li>
            <li>Fotoğraf Entegrasyonu</li>
            <li>İnfografik Tasarım</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="module-card">
        <h3>🧭 Stratejik Rota</h3>
        <p><b>Görev:</b> 2028 Emeklilik hedefine giden yoldaki eğitim, sertifikasyon ve teknik gelişim süreçlerini yönetir.</p>
        <ul>
            <li>Gantt Şeması (3 Yıllık)</li>
            <li>Kişisel Ajanda (SQL)</li>
            <li>Yetkinlik Analizi</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)