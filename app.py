import streamlit as st
import pandas as pd
import json
from datetime import datetime
import itertools

# Sayfa yapılandırması
st.set_page_config(
    page_title="Net Sıfır Proje Değerlendirme",
    page_icon="🌱",
    layout="wide"
)

# Kriterleri tanımla
CRITERIA = {
    "stage2": {
        "name": "2. Aşama - Tema Önceliği",
        "criteria": [
            ("a", "Düşük Karbonlu Alternatif Yakıtlar"),
            ("b", "Yük Taşımacılığının Karbonsuzlaştırılması"),
            ("c", "Hidrojen/Elektrikli Araç Filo Dönüşümü"),
            ("d", "Toplu Taşıma"),
            ("e", "Yürüme ve Bisiklet Altyapısı"),
            ("f", "Paylaşımlı Mobilite"),
            ("g", "Yük Lojistiği"),
            ("h", "Mobility-as-a-Service (MaaS)"),
            ("i", "Akıllı Araç, Şarj Altyapısı"),
            ("j", "Yeşil Liman / Havalimanı"),
            ("k", "Demiryolu Modernizasyonu"),
            ("l", "Araç Filolarında Enerji İzleme"),
            ("m", "Davranışsal Değişim Girişimleri"),
            ("n", "İstihdam ve Ekonomiye Katkı"),
            ("o", "Erişilebilirlik ve Kapsayıcılık"),
            ("p", "Acil Durum Lojistiği"),
            ("q", "Akıllı Altyapı İzleme"),
            ("r", "Akıllı Ulaşım Sistemleri (AUS)"),
            ("s", "Dijital Lojistik Yönetimi"),
            ("t", "Siber Güvenlik"),
            ("u", "Trafik İzleme ve Yapay Zeka"),
            ("v", "Sürdürülebilir Mobilite Platformları"),
            ("w", "Akıllı Otopark Yönetimi"),
        ]
    },
    "stage3": {
        "name": "3. Aşama - Olgunluk Değerlendirmesi",
        "criteria": [
            ("a", "Teknik Açıklamaların Varlığı"),
            ("b", "CAPEX/OPEX Analizi Mevcudiyeti"),
            ("c", "Finansal Analizin Varlığı"),
            ("d", "Uygulama/Yatırım Kararı"),
            ("e", "İzin/Ruhsat Durumu"),
            ("f", "Zaman Planı Gerçekçiliği"),
            ("g", "Risk Yönetimi Planı"),
        ]
    },
    "stage4": {
        "name": "4. Aşama - Etki ve Kalite",
        "criteria": [
            ("a", "Ölçek Etkisi"),
            ("b", "Çevresel Etki"),
            ("c", "Çarpan Etkisi"),
            ("d", "İnovasyon ve Uyarlanabilirlik"),
            ("e", "Sürdürülebilirlik"),
        ]
    },
    "stage_comparison": {
        "name": "Aşamalar Arası Karşılaştırma",
        "criteria": [
            ("a", "2. Aşama - Tema Önceliği"),
            ("b", "3. Aşama - Olgunluk Değerlendirmesi"),
            ("c", "4. Aşama - Etki ve Kalite"),
        ]
    }
}

# Session state başlat
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'expert_name' not in st.session_state:
    st.session_state.expert_name = ""
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = "welcome"

def generate_pairs(criteria_list):
    """Tüm kriter çiftlerini oluştur"""
    return list(itertools.combinations(criteria_list, 2))

def save_response(stage, pair_key, response):
    """Yanıtı kaydet"""
    if stage not in st.session_state.responses:
        st.session_state.responses[stage] = {}
    st.session_state.responses[stage][pair_key] = response

def display_comparison(stage_key, pair_idx):
    """Kriter karşılaştırma arayüzü"""
    stage_data = CRITERIA[stage_key]
    criteria_list = stage_data["criteria"]
    pairs = generate_pairs(criteria_list)
    
    if pair_idx >= len(pairs):
        return True  # Tamamlandı
    
    pair = pairs[pair_idx]
    criterion_a = pair[0]
    criterion_b = pair[1]
    
    pair_key = f"{criterion_a[0]}_{criterion_b[0]}"
    
    # Progress bar
    progress = (pair_idx + 1) / len(pairs)
    st.progress(progress, text=f"İlerleme: {pair_idx + 1}/{len(pairs)}")
    
    st.markdown("---")
    st.subheader("🔍 Kriter Karşılaştırması")
    
    # İki kriteri yan yana göster
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.info(f"**{criterion_a[0].upper()}**\n\n{criterion_a[1]}")
    
    with col2:
        st.markdown("<h3 style='text-align: center;'>VS</h3>", unsafe_allow_html=True)
    
    with col3:
        st.success(f"**{criterion_b[0].upper()}**\n\n{criterion_b[1]}")
    
    st.markdown("---")
    
    # Soru
    st.markdown("### ❓ Hangi kriter daha önemlidir?")
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    
    with col_b:
        # Önce hangisinin önemli olduğunu seç
        choice = st.radio(
            "Daha önemli olan kriter:",
            [f"{criterion_a[0].upper()}: {criterion_a[1]}", 
             "Eşit önemde",
             f"{criterion_b[0].upper()}: {criterion_b[1]}"],
            key=f"choice_{pair_key}",
            index=1
        )
        
        # Önem derecesi
        importance = 0
        if choice != "Eşit önemde":
            importance = st.select_slider(
                "Önem derecesi:",
                options=[1, 2, 3],
                value=2,
                format_func=lambda x: {1: "Zayıf tercih", 2: "Orta düzey", 3: "Çok güçlü"}[x],
                key=f"importance_{pair_key}"
            )
    
    # Yanıtı kaydet ve devam et
    col_prev, col_next = st.columns(2)
    
    with col_prev:
        if pair_idx > 0:
            if st.button("⬅️ Önceki"):
                st.session_state[f'pair_idx_{stage_key}'] = pair_idx - 1
                st.rerun()
    
    with col_next:
        if st.button("Devam ➡️" if pair_idx < len(pairs) - 1 else "Bu Aşamayı Tamamla ✓"):
            # Yanıtı kaydet
            if choice == "Eşit önemde":
                response = "0"
            elif criterion_a[1] in choice:
                response = f"{importance}{criterion_a[0]}"
            else:
                response = f"{importance}{criterion_b[0]}"
            
            save_response(stage_key, pair_key, response)
            
            # Sonraki soruya geç
            st.session_state[f'pair_idx_{stage_key}'] = pair_idx + 1
            st.rerun()
    
    return False

def welcome_page():
    """Karşılama sayfası"""
    st.title("🌱 Net Sıfır Proje Değerlendirme Sistemi")
    st.markdown("---")
    
    st.markdown("""
    ### Hoş Geldiniz!
    
    Bu sistem, Net Sıfır Projesi kapsamındaki proje başvurularını değerlendirmek için tasarlanmıştır.
    
    #### 📋 Değerlendirme Aşamaları:
    1. **2. Aşama** - Tema Önceliği (23 kriter)
    2. **3. Aşama** - Olgunluk Değerlendirmesi (7 kriter)
    3. **4. Aşama** - Etki ve Kalite (5 kriter)
    4. **Aşamalar Arası** - Aşamaların önem karşılaştırması (3 kriter)
    
    #### 🎯 Nasıl Çalışır?
    - Her adımda iki kriter karşılaştırılır
    - Hangisinin daha önemli olduğunu seçersiniz
    - Önem derecesini belirlersiniz (zayıf, orta, güçlü)
    - Tüm değerlendirme otomatik olarak kaydedilir
    
    #### ⏱️ Tahmini Süre:
    - **2. Aşama**: ~30 dakika (253 karşılaştırma)
    - **3. Aşama**: ~5 dakika (21 karşılaştırma)
    - **4. Aşama**: ~3 dakika (10 karşılaştırma)
    - **Aşamalar Arası**: ~1 dakika (3 karşılaştırma)
    
    **Toplam**: Yaklaşık 40 dakika
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        expert_name = st.text_input("👤 Adınız Soyadınız:", value=st.session_state.expert_name)
    with col2:
        expert_org = st.text_input("🏢 Kurum/Organizasyon:")
    
    if st.button("🚀 Değerlendirmeye Başla"):
        if expert_name:
            st.session_state.expert_name = expert_name
            st.session_state.expert_org = expert_org
            st.session_state.current_stage = "stage2"
            st.session_state['pair_idx_stage2'] = 0
            st.rerun()
        else:
            st.error("Lütfen adınızı soyadınızı girin.")

def main_evaluation():
    """Ana değerlendirme sayfası"""
    st.title("🌱 Net Sıfır Proje Değerlendirme")
    
    # Header bilgisi
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Uzman:** {st.session_state.expert_name}")
    with col2:
        if st.button("💾 Kaydet ve Çık"):
            export_results()
            return
    
    st.markdown("---")
    
    # Aşama seçimi
    tabs = st.tabs([
        "2️⃣ Tema Önceliği",
        "3️⃣ Olgunluk",
        "4️⃣ Etki ve Kalite",
        "🔗 Aşamalar Arası",
        "📊 Sonuçlar"
    ])
    
    # 2. Aşama
    with tabs[0]:
        st.header(CRITERIA["stage2"]["name"])
        if f'pair_idx_stage2' not in st.session_state:
            st.session_state['pair_idx_stage2'] = 0
        
        completed = display_comparison("stage2", st.session_state['pair_idx_stage2'])
        if completed:
            st.success("✅ 2. Aşama tamamlandı!")
            if st.button("3. Aşamaya Geç ➡️"):
                st.session_state['pair_idx_stage3'] = 0
                st.rerun()
    
    # 3. Aşama
    with tabs[1]:
        st.header(CRITERIA["stage3"]["name"])
        if 'stage2' in st.session_state.responses and len(st.session_state.responses['stage2']) > 0:
            if f'pair_idx_stage3' not in st.session_state:
                st.session_state['pair_idx_stage3'] = 0
            
            completed = display_comparison("stage3", st.session_state['pair_idx_stage3'])
            if completed:
                st.success("✅ 3. Aşama tamamlandı!")
                if st.button("4. Aşamaya Geç ➡️"):
                    st.session_state['pair_idx_stage4'] = 0
                    st.rerun()
        else:
            st.warning("⚠️ Önce 2. Aşamayı tamamlayın.")
    
    # 4. Aşama
    with tabs[2]:
        st.header(CRITERIA["stage4"]["name"])
        if 'stage3' in st.session_state.responses and len(st.session_state.responses['stage3']) > 0:
            if f'pair_idx_stage4' not in st.session_state:
                st.session_state['pair_idx_stage4'] = 0
            
            completed = display_comparison("stage4", st.session_state['pair_idx_stage4'])
            if completed:
                st.success("✅ 4. Aşama tamamlandı!")
                if st.button("Aşamalar Arası Karşılaştırmaya Geç ➡️"):
                    st.session_state['pair_idx_stage_comparison'] = 0
                    st.rerun()
        else:
            st.warning("⚠️ Önce 3. Aşamayı tamamlayın.")
    
    # Aşamalar Arası
    with tabs[3]:
        st.header(CRITERIA["stage_comparison"]["name"])
        if 'stage4' in st.session_state.responses and len(st.session_state.responses['stage4']) > 0:
            if f'pair_idx_stage_comparison' not in st.session_state:
                st.session_state['pair_idx_stage_comparison'] = 0
            
            completed = display_comparison("stage_comparison", st.session_state['pair_idx_stage_comparison'])
            if completed:
                st.success("🎉 Tüm değerlendirme tamamlandı!")
                st.balloons()
        else:
            st.warning("⚠️ Önce 4. Aşamayı tamamlayın.")
    
    # Sonuçlar
    with tabs[4]:
        st.header("📊 Değerlendirme Sonuçları")
        display_results()

def display_results():
    """Sonuçları göster"""
    if not st.session_state.responses:
        st.info("Henüz değerlendirme yapılmadı.")
        return
    
    for stage_key, responses in st.session_state.responses.items():
        stage_name = CRITERIA[stage_key]["name"]
        st.subheader(stage_name)
        st.write(f"✅ {len(responses)} karşılaştırma tamamlandı")
        
        with st.expander("Detayları Gör"):
            df = pd.DataFrame([
                {"Karşılaştırma": k, "Sonuç": v}
                for k, v in responses.items()
            ])
            st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    if st.button("📥 Sonuçları İndir (JSON)"):
        export_results()

def export_results():
    """Sonuçları dışa aktar"""
    data = {
        "expert_name": st.session_state.expert_name,
        "expert_org": st.session_state.get('expert_org', ''),
        "timestamp": datetime.now().isoformat(),
        "responses": st.session_state.responses
    }
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="📥 JSON Olarak İndir",
        data=json_str,
        file_name=f"degerlendirme_{st.session_state.expert_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

# Ana uygulama
def main():
    if st.session_state.current_stage == "welcome":
        welcome_page()
    else:
        main_evaluation()

if __name__ == "__main__":
    main()
