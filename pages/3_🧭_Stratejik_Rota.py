import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import sqlite3

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="2028 Stratejik Rota", layout="wide", page_icon="🧭")

# --- CSS ---
st.markdown("""
<style>
    .milestone-card { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #00cc96; margin-bottom: 10px; }
    .task-card { background-color: #262730; padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #4da6ff; }
</style>
""", unsafe_allow_html=True)

st.title("🧭 2028 Stratejik Rota & Ajanda")
st.caption(f"Hedef: Ağustos 2028 | Kalan Süre: ~{(datetime(2028, 8, 1) - datetime.now()).days} Gün")
st.markdown("---")

# --- VERİTABANI (AJANDA İÇİN) ---
def db_baglan(): return sqlite3.connect('istihbarat.db') # Aynı veritabanını kullanıyoruz

def tablo_olustur():
    conn = db_baglan()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ajanda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gorev TEXT,
            kategori TEXT,
            oncelik TEXT,
            son_tarih DATE,
            durum TEXT
        )
    ''')
    conn.commit()
    conn.close()

def gorev_ekle(gorev, kategori, oncelik, son_tarih):
    conn = db_baglan()
    c = conn.cursor()
    c.execute("INSERT INTO ajanda (gorev, kategori, oncelik, son_tarih, durum) VALUES (?, ?, ?, ?, ?)", 
              (gorev, kategori, oncelik, son_tarih, "Yapılacak"))
    conn.commit()
    conn.close()

def gorev_guncelle(id, yeni_durum):
    conn = db_baglan()
    c = conn.cursor()
    c.execute("UPDATE ajanda SET durum = ? WHERE id = ?", (yeni_durum, id))
    conn.commit()
    conn.close()

def gorev_sil(id):
    conn = db_baglan()
    c = conn.cursor()
    c.execute("DELETE FROM ajanda WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def verileri_getir():
    conn = db_baglan()
    df = pd.read_sql_query("SELECT * FROM ajanda", conn)
    conn.close()
    return df

tablo_olustur()

# --- STRATEJİK VERİ SETLERİ (GANTT) ---
timeline_data = [
    dict(Task="Python & Veri Analizi (Temel)", Start='2025-11-01', Finish='2026-06-01', Phase="1. Hazırlık (2026)", Kaynak="Teknik"),
    dict(Task="PMP Sertifikası (Hazırlık + Sınav)", Start='2026-01-01', Finish='2026-08-01', Phase="1. Hazırlık (2026)", Kaynak="Sertifika"),
    dict(Task="Yüksek Lisans Araştırma & Başvuru", Start='2026-06-01', Finish='2026-12-01', Phase="1. Hazırlık (2026)", Kaynak="Akademik"),
    dict(Task="Online AI Master Programı (1. Yıl)", Start='2027-01-01', Finish='2027-12-31', Phase="2. Gelişim (2027)", Kaynak="Akademik"),
    dict(Task="İstihbarat Yazılımı v11 (SQL Entegre)", Start='2026-09-01', Finish='2027-03-01', Phase="2. Gelişim (2027)", Kaynak="Yazılım"),
    dict(Task="Online AI Master (Mezuniyet)", Start='2028-01-01', Finish='2028-06-01', Phase="3. Sonuç (2028)", Kaynak="Akademik"),
    dict(Task="EMEKLİLİK (Ağustos 2028)", Start='2028-08-01', Finish='2028-08-30', Phase="3. Sonuç (2028)", Kaynak="Kariyer"),
]

skills = {
    'Yetenek': ['Askeri Tecrübe', 'PMP (Proje Yön.)', 'AI/Yazılım (Akademik)', 'Sektörel Network', 'Ticari İngilizce'],
    'Mevcut': [100, 50, 30, 40, 85],
    '2028 Hedef': [100, 100, 90, 85, 95]
}

# --- ARAYÜZ ---
tab1, tab2, tab3 = st.tabs(["📅 GÜNLÜK AJANDA", "🗺️ 2028 YOL HARİTASI", "📊 GELİŞİM RADARI"])

# --- TAB 1: AJANDA (GÜNLÜK İŞLER) ---
with tab1:
    col_add, col_list = st.columns([1, 2])
    
    with col_add:
        st.subheader("➕ Görev Ekle")
        with st.form("yeni_gorev_form", clear_on_submit=True):
            yeni_gorev = st.text_input("Görev Tanımı")
            kategori = st.selectbox("Kategori", ["PMP Çalışması", "Yazılım Geliştirme", "Master Başvurusu", "İstihbarat Okuması", "Diğer"])
            oncelik = st.selectbox("Öncelik", ["🔴 Yüksek", "🟡 Orta", "🔵 Düşük"])
            tarih = st.date_input("Son Tarih", min_value=date.today())
            submit = st.form_submit_button("Kaydet")
            
            if submit and yeni_gorev:
                gorev_ekle(yeni_gorev, kategori, oncelik, tarih)
                st.success("Eklendi!")
                st.rerun()

    with col_list:
        st.subheader("📋 Yapılacaklar Listesi")
        df_ajanda = verileri_getir()
        
        if not df_ajanda.empty:
            # Sadece 'Yapılacak' olanları göster
            df_aktif = df_ajanda[df_ajanda['durum'] == "Yapılacak"].sort_values(by='son_tarih')
            
            if not df_aktif.empty:
                for index, row in df_aktif.iterrows():
                    c1, c2, c3 = st.columns([4, 2, 1])
                    with c1:
                        st.markdown(f"**{row['gorev']}**")
                        st.caption(f"{row['kategori']} | 📅 {row['son_tarih']} | {row['oncelik']}")
                    with c2:
                        pass
                    with c3:
                        if st.button("✅", key=f"bitir_{row['id']}", help="Tamamla"):
                            gorev_guncelle(row['id'], "Tamamlandı")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Aktif görev yok. Harika!")
                
            with st.expander("Tamamlanan Görevler"):
                df_biten = df_ajanda[df_ajanda['durum'] == "Tamamlandı"]
                st.dataframe(df_biten)
                if st.button("Tümünü Temizle (Tamamlananlar)"):
                    # Sadece tamamlananları silmek için döngü
                    for i, r in df_biten.iterrows():
                        gorev_sil(r['id'])
                    st.rerun()
        else:
            st.info("Ajanda boş.")

# --- TAB 2: YOL HARİTASI (BÜYÜK RESİM) ---
with tab2:
    st.subheader("2025-2028 Stratejik Planı")
    df_timeline = pd.DataFrame(timeline_data)
    df_timeline['Start'] = pd.to_datetime(df_timeline['Start'])
    df_timeline['Finish'] = pd.to_datetime(df_timeline['Finish'])

    fig_gantt = px.timeline(df_timeline, x_start="Start", x_end="Finish", y="Task", color="Phase", 
                            height=400,
                            color_discrete_map={"1. Hazırlık (2026)": "#00cc96", "2. Gelişim (2027)": "#4da6ff", "3. Sonuç (2028)": "#ffa500"})
    fig_gantt.update_yaxes(autorange="reversed")
    
    # Bugün Çizgisi (Manuel Yöntem - Hatasız)
    bugun = datetime.now()
    fig_gantt.add_shape(type="line", x0=bugun, y0=0, x1=bugun, y1=1, xref="x", yref="paper", line=dict(color="white", width=2, dash="dash"))
    fig_gantt.add_annotation(x=bugun, y=1.1, xref="x", yref="paper", text="BUGÜN", showarrow=False, font=dict(color="white"))
    
    st.plotly_chart(fig_gantt, use_container_width=True)

# --- TAB 3: RADAR ---
with tab3:
    col1, col2 = st.columns([2, 1])
    with col1:
        categories = skills['Yetenek']
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=skills['Mevcut'], theta=categories, fill='toself', name='Mevcut Durum'))
        fig_radar.add_trace(go.Scatterpolar(r=skills['2028 Hedef'], theta=categories, fill='toself', name='2028 Vizyonu'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col2:
        st.info("Bu radar, 'Emekli Subay' profilinden 'Teknoloji Lideri' profiline dönüşümün matematiksel özetidir.")