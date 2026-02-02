import streamlit as st
import scrapetube
import pandas as pd
import numpy as np
from datetime import datetime
import time
import re
from collections import Counter
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket

# Sayfa ayarları
st.set_page_config(
    page_title="Niche Oracle Strategist",
    page_icon="🧠",
    layout="wide"
)

# Niche Oracle™ Strategist Tasarım
st.markdown("""
    <style>
    .main { background-color: #050505; color: #e5e5e5; }
    .stTextInput>div>div>input { background-color: #111; color: white; border: 1px solid #222; border-radius: 8px; padding: 12px; }
    .stButton>button { width: 100%; background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%); color: white; border-radius: 8px; padding: 12px; font-weight: 700; border: none; transition: all 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4); }
    .decision-card {
        border: 2px solid #6366f1;
        background: linear-gradient(145deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
        padding: 40px;
        border-radius: 24px;
        margin-bottom: 40px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .score-value { font-size: 4rem; font-weight: 900; color: #6366f1; line-height: 1; }
    .score-label { font-size: 1.2rem; color: #a1a1aa; text-transform: uppercase; letter-spacing: 2px; }
    .card {
        border: 1px solid #1a1a1a;
        background: #0f0f0f;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .vph-badge {
        background: #10b981;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .strategy-box {
        background: #111;
        border-left: 4px solid #a855f7;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }
    .error-box {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid #ef4444;
        color: #fca5a5;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Niche Oracle Ghost Protocol (V22)")
st.markdown("Güncel Pazar Analizi: Gelişmiş Erişim Koruması ve Trend Takibi")

# DNS ve Bağlantı Kontrolü
def check_youtube_access():
    try:
        # DNS Çözümleme Testi
        socket.gethostbyname("www.youtube.com")
        return True, "DNS OK"
    except socket.gaierror:
        return False, "DNS_ERROR: Sunucu YouTube adresini çözemiyor (Hugging Face kısıtlaması)."
    except Exception as e:
        return False, f"UNKNOWN_ERROR: {str(e)}"

# Yardımcı Fonksiyonlar
def parse_duration(duration_str):
    if not duration_str: return 0
    parts = duration_str.split(':')
    if len(parts) == 2: return int(parts[0])
    elif len(parts) == 3: return int(parts[0]) * 60 + int(parts[1])
    return 0

def parse_views(view_text):
    if not view_text: return 0
    view_text = view_text.lower().replace('views', '').replace('izlenme', '').strip()
    try:
        if 'k' in view_text or 'bin' in view_text: return int(float(view_text.replace('k', '').replace('bin', '').replace(',', '.')) * 1000)
        if 'm' in view_text or 'mn' in view_text: return int(float(view_text.replace('m', '').replace('mn', '').replace(',', '.')) * 1000000)
        return int(''.join(filter(str.isdigit, view_text)))
    except: return 0

def get_vph(views, published_text):
    try:
        hours = 1
        num = int(re.search(r'\d+', published_text).group()) if re.search(r'\d+', published_text) else 1
        if 'hour' in published_text or 'saat' in published_text: hours = num
        elif 'day' in published_text or 'gün' in published_text: hours = num * 24
        elif 'week' in published_text or 'hafta' in published_text: hours = num * 24 * 7
        elif 'month' in published_text or 'ay' in published_text: hours = num * 24 * 30
        elif 'year' in published_text or 'yıl' in published_text: hours = num * 24 * 365
        
        vph = views / hours
        return vph if vph < views else views / (24 * 30)
    except:
        return 0

def get_channel_stats(channel_id):
    try:
        videos = list(scrapetube.get_channel(channel_id, limit=10))
        views = []
        for v in videos:
            v_views = parse_views(v.get('viewCountText', {}).get('simpleText', '0'))
            if v_views > 0: views.append(v_views)
        
        median = np.median(views) if views else 1
        return {"median": median}
    except: return {"median": 1}

def analyze_titles(titles):
    words = []
    for t in titles:
        w = re.findall(r'\w+', t.lower())
        words.extend([word for word in w if len(word) > 3])
    common = Counter(words).most_common(10)
    return common

# Yan Panel
with st.sidebar:
    st.header("⚙️ Trend Ayarları")
    scan_limit = st.slider("Tarama Derinliği", 100, 1000, 500)
    min_duration = st.slider("Min. Süre (Dakika)", 1, 60, 10)
    time_range = st.selectbox("Zaman Aralığı", ["Son 1 Ay", "Son 3 Ay", "Son 6 Ay", "Tüm Zamanlar"], index=2)
    st.divider()
    st.caption("V22: Ghost Protocol - Gelişmiş Erişim Koruması")

# Ana Arama
query = st.text_input("Niş veya Anahtar Kelime", placeholder="Örn: AI News, Survival Skills, Luxury Travel...")

if query:
    with st.spinner(f"'{query}' nişi için stratejik analiz yapılıyor..."):
        # DNS Kontrolü
        is_ok, msg = check_youtube_access()
        if not is_ok:
            st.markdown(f"""
            <div class="error-box">
                ⚠️ <b>Erişim Engeli Tespit Edildi:</b> {msg}<br><br>
                <b>Neden:</b> Hugging Face sunucuları YouTube'a erişimi DNS seviyesinde engelliyor.<br>
                <b>Çözüm:</b> Bu sorunu aşmak için uygulamayı <b>Streamlit Cloud</b> veya <b>Render</b> platformuna taşımanız gerekmektedir. 
                Manus üzerinden size gönderilen <b>app.py</b> ve <b>requirements.txt</b> dosyalarını kullanarak kendi Streamlit Cloud hesabınızda saniyeler içinde yayına alabilirsiniz.
            </div>
            """, unsafe_allow_html=True)
            st.stop()

        try:
            videos = scrapetube.get_search(query, limit=scan_limit, sort_by="upload_date")
            
            results = []
            titles = []
            total_views = 0
            outlier_count = 0
            small_channel_success = 0
            
            progress = st.progress(0)
            
            video_list = list(videos)
            if not video_list:
                st.warning("Hiç video bulunamadı. Lütfen arama teriminizi kontrol edin.")
                st.stop()

            for i, v in enumerate(video_list):
                if i % 20 == 0: progress.progress(min(i / len(video_list), 1.0))
                
                v_duration_str = v.get('lengthText', {}).get('simpleText', '')
                if parse_duration(v_duration_str) < min_duration: continue
                
                v_id = v.get('videoId')
                v_title = v.get('title', {}).get('runs', [{}])[0].get('text', '')
                
                # Hassas Filtreleme
                negative_keywords = ['peppa', 'pig', 'cartoon', 'kids', 'animation', 'toy', 'gameplay', 'roblox', 'minecraft']
                if any(neg in v_title.lower() for neg in negative_keywords): continue
                
                search_terms = query.lower().split()
                if not all(term in v_title.lower() for term in search_terms): continue

                v_views = parse_views(v.get('viewCountText', {}).get('simpleText', '0'))
                v_channel_id = v.get('ownerText', {}).get('runs', [{}])[0].get('navigationEndpoint', {}).get('browseEndpoint', {}).get('browseId', '')
                v_channel_name = v.get('ownerText', {}).get('runs', [{}])[0].get('text', '')
                v_published = v.get('publishedTimeText', {}).get('simpleText', '')
                
                # Zaman Filtresi
                if time_range != "Tüm Zamanlar":
                    is_old = any(x in v_published.lower() for x in ['year', 'yıl'])
                    if time_range == "Son 1 Ay":
                        if is_old or any(x in v_published.lower() for x in ['month', 'ay']) and not '1' in v_published: continue
                    elif time_range == "Son 3 Ay":
                        if is_old: continue
                        if 'month' in v_published.lower() or 'ay' in v_published.lower():
                            months_match = re.search(r'\d+', v_published)
                            if months_match and int(months_match.group()) > 3: continue
                    elif time_range == "Son 6 Ay":
                        if is_old: continue
                        if 'month' in v_published.lower() or 'ay' in v_published.lower():
                            months_match = re.search(r'\d+', v_published)
                            if months_match and int(months_match.group()) > 6: continue

                if v_views < 1000: continue
                
                vph = get_vph(v_views, v_published)
                total_views += v_views
                titles.append(v_title)
                
                if i % 10 == 0:
                    stats = get_channel_stats(v_channel_id)
                    median = stats["median"]
                    outlier_score = v_views / median
                    if outlier_score > 5: outlier_count += 1
                    if v_views > 100000: small_channel_success += 1
                
                results.append({
                    'id': v_id,
                    'title': v_title,
                    'views': v_views,
                    'vph': vph,
                    'channel': v_channel_name,
                    'duration': v_duration_str,
                    'published': v_published,
                    'link': f"https://www.youtube.com/watch?v={v_id}",
                    'thumb': f"https://img.youtube.com/vi/{v_id}/maxresdefault.jpg"
                })
            
            progress.empty()
            
            if results:
                # Skorlama Algoritması
                outlier_density = (outlier_count / (len(results)/10)) * 100 if results else 0
                score_outlier = min(40, outlier_density * 0.4)
                small_success_rate = (small_channel_success / len(results)) * 100 if results else 0
                score_small_biz = min(30, small_success_rate * 3)
                avg_views = total_views / len(results) if results else 0
                score_volume = min(30, (avg_views / 50000) * 30)
                
                niche_score = int(score_outlier + score_small_biz + score_volume)
                niche_score = min(100, max(0, niche_score))
                
                # Karar Paneli
                st.markdown(f"""
                <div class="decision-card">
                    <div class="score-label">Niche Oracle™ Skoru</div>
                    <div class="score-value">{niche_score}/100</div>
                    <div style="margin-top: 20px; font-size: 1.5rem; font-weight: 700; color: #fff;">
                        STRATEJİ: { "🚀 AGRESİF YATIRIM - YÜKSEK VİRAL POTANSİYEL" if niche_score > 70 else ("✅ İSTİKRARLI BÜYÜME - DOĞRU SEO ODAKLI" if niche_score > 40 else "⚠️ NİŞ DEĞİŞTİRİN VEYA ÇOK ÖZGÜN OLUN") }
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                tab1, tab2, tab3 = st.tabs(["💎 Fırsat Videoları", "📊 Strateji Raporu", "🧠 AI Hook Analizi"])
                
                with tab1:
                    st.subheader("En Yüksek VPH (Hız) Alan Videolar")
                    sorted_results = sorted(results, key=lambda x: x['vph'], reverse=True)
                    for row in sorted_results[:30]:
                        st.markdown(f"""
                        <div class="card">
                            <div style="display: flex; gap: 20px; align-items: center;">
                                <img src="{row['thumb']}" style="width: 180px; border-radius: 10px;">
                                <div style="flex: 1;">
                                    <a href="{row['link']}" target="_blank" style="color: #fff; font-size: 1.1rem; font-weight: 700; text-decoration: none;">{row['title']}</a>
                                    <div style="margin-top: 5px; color: #a1a1aa; font-size: 0.9rem;">
                                        📺 {row['channel']} • 🕒 {row['published']} • ⏱️ {row['duration']}
                                    </div>
                                    <div style="margin-top: 10px; display: flex; gap: 10px;">
                                        <span class="vph-badge">🔥 {int(row['vph']):,} VPH</span>
                                        <span style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">👁️ {row['views']:,} İzlenme</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Analiz Edilen Video", len(results))
                        st.metric("Ortalama İzlenme", f"{int(avg_views):,}")
                    with col2:
                        st.metric("Outlier Yoğunluğu", f"%{int(outlier_density)}")
                        st.metric("Küçük Kanal Başarısı", f"%{int(small_success_rate)}")
                    
                    st.markdown("### 🗺️ Pazar Sağlık Haritası")
                    st.info(f"Bu nişte yeni bir kanalın başarılı olma şansı: **%{niche_score}**. " + 
                            ("Pazar şu an çok sıcak, içerik üretmek için mükemmel zaman!" if niche_score > 60 else "Pazar doygun veya talep düşük, farklı bir açı bulmalısınız."))

                with tab3:
                    st.subheader("🧠 Viral Başlık ve Kelime Analizi")
                    common_words = analyze_titles(titles)
                    
                    cols = st.columns(2)
                    with cols[0]:
                        st.markdown("#### 🔑 En Çok Tıklanan Kelimeler")
                        for word, count in common_words:
                            st.write(f"- **{word}** ({count} kez)")
                    
                    with cols[1]:
                        st.markdown("#### 📝 Önerilen Viral Başlık Yapıları")
                        st.markdown(f"""
                        <div class="strategy-box">1. "{query} Secret: Why Everyone is Talking About It"</div>
                        <div class="strategy-box">2. "I Tried {query} for 30 Days (Results)"</div>
                        <div class="strategy-box">3. "The Truth About {query} in 2024"</div>
                        """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Beklenmedik bir hata oluştu: {str(e)}")
            st.info("Lütfen sayfayı yenileyip tekrar deneyin.")
