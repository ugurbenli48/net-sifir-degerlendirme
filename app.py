import streamlit as st
import json
from datetime import datetime
import itertools

# Google Sheets için
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

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
            ("a", "Düşük Karbonlu Alternatif Yakıtlar", "Elektrifikasyonun mümkün olmadığı ulaşım modlarında kullanılmak üzere yeşil hidrojen, biyoyakıtlar ve sentetik e-yakıtlar gibi düşük karbonlu alternatif yakıtların geliştirilmesi ve uygulanması."),
            ("b", "Yük Taşımacılığının Karbonsuzlaştırılması", "Lojistik araçlarının alternatif yakıtlı/elektrikli lojistik araçlarına geçilmesi."),
            ("c", "Hidrojen/Elektrikli Araç Filo Dönüşümü", "Hidrojen ve elektrikli araçların kamu veya özel filo yapılarında satın alınarak mevcut dizel/benzinli araçların aşamalı biçimde düşük emisyonlu araçlarla değiştirilmesi."),
            ("d", "Toplu Taşıma", "Düşük karbonlu toplu taşıma seçeneklerinin payını artırılması."),
            ("e", "Yürüme ve Bisiklet Altyapısı", "Yaya dostu kentsel alanlar ve bisiklet yollarının geliştirilmesi."),
            ("f", "Paylaşımlı Mobilite", "Bisiklet paylaşımı ve e-scooter sistemleri."),
        ]
    },
    "stage3": {
        "name": "3. Aşama - Olgunluk Değerlendirmesi",
        "criteria": [
            ("a", "Teknik Açıklamaların Varlığı", "Projenin teknik bileşenlerinin yeterince açıklanıp açıklanmadığını ve verilen teknik bilgilerin proje gereksinimleriyle uyumu değerlendirilir."),
            ("b", "CAPEX/OPEX Analizi", "Projenin sermaye (CAPEX) ve işletme (OPEX) maliyetlerinin analiz edilip edilmediğini ve karar sürecini destekleyecek maliyet yapısının net olarak ortaya konup konmadığı değerlendirilir."),
            ("c", "Finansal Analizin Varlığı", "Projenin finansal fizibilitesinin ve karar sürecini destekleyecek analizlerin mevcut olup olmadığı değerlendirilir."),
            ("d", "Uygulama/Yatırım Kararı", "Proje için daha önce alınmış uygulama veya yatırım kararlarının varlığını ve hazırlık düzeyinin değerlendirilmesi."),
            ("e", "İzin/Ruhsat Durumu", "Gerekli izin, ruhsat ve onay süreçlerinin tamamlanma durumunun değerlendirilmesi."),
            ("f", "Zaman Planı Gerçekçiliği", "Projenin önerilen takviminin uygulanabilirliğini, faaliyetlerin süre tahminlerinin gerçekçiliğinin değerlendirilmesi."),
            ("g", "Risk Yönetimi Planı", "Proje risklerinin tanımlanıp yönetim stratejilerinin/analizlerinin oluşturulup oluşturulmadığını değerlendirir."),
        ]
    },
    "stage4": {
        "name": "4. Aşama - Etki ve Kalite",
        "criteria": [
            ("a", "Ölçek Etkisi", "Projenin etkilediği nüfusun ve coğrafi alanın büyüklüğünü değerlendirir."),
            ("b", "Çevresel Etki", "Projenin çevresel etkilerini; GHG azaltımı (CO₂, CH₄, N₂O), enerji tüketimindeki düşüş ve hava kalitesindeki iyileşme (NOx, PM10, NMHC) gibi göstergeler üzerinden değerlendirir."),
            ("c", "Çarpan Etkisi", "Projenin doğrudan çıktılarının ötesinde ek ekonomik, sosyal veya çevresel faydalar üretme potansiyelini değerlendirir."),
            ("d", "İnovasyon ve Uyarlanabilirlik", "Projenin inovatif yapısını, pilot uygulama niteliğini ve farklı bölge veya koşullara ölçeklenebilir ve uyarlanabilir olma kapasitesini değerlendirir."),
            ("e", "Sürdürülebilirlik", "Projenin uzun vadede sürdürülebilirliğini, operasyonel devamlılığını ve kalıcı etki yaratma kapasitesini değerlendirir."),
        ]
    },
    "stage_comparison": {
        "name": "Aşamalar Arası Karşılaştırma",
        "criteria": [
            ("a", "2. Aşama - Tema Önceliği", "Projenin hangi temaya odaklandığı ve bu temanın öncelik düzeyi."),
            ("b", "3. Aşama - Olgunluk Değerlendirmesi", "Projenin teknik, finansal ve operasyonel olgunluk seviyesi."),
            ("c", "4. Aşama - Etki ve Kalite", "Projenin sosyal, ekonomik, çevresel etkisi ve teknik kalitesi."),
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

def check_and_auto_save():
    """Tüm aşamalar tamamlandıysa otomatik kaydet"""
    # Zaten kaydedildi mi kontrol et
    if 'auto_saved' in st.session_state and st.session_state.auto_saved:
        return
    
    # Tüm aşamalar tamamlandı mı?
    all_completed = (
        'stage2' in st.session_state.responses and 
        len(st.session_state.responses['stage2']) == 253 and  # 23 kriter: C(23,2) = 253
        'stage3' in st.session_state.responses and 
        len(st.session_state.responses['stage3']) == 21 and   # 7 kriter: C(7,2) = 21
        'stage4' in st.session_state.responses and 
        len(st.session_state.responses['stage4']) == 10 and   # 5 kriter: C(5,2) = 10
        'stage_comparison' in st.session_state.responses and 
        len(st.session_state.responses['stage_comparison']) == 3  # 3 aşama: C(3,2) = 3
    )
    
    if all_completed:
        # Otomatik kaydet
        success = save_results_to_server()
        if success:
            st.session_state.auto_saved = True

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
        st.info(f"**Kriter {criterion_a[0].upper()}**\n\n**{criterion_a[1]}**\n\n_{criterion_a[2]}_")
    
    with col2:
        st.markdown("<h3 style='text-align: center;'>VS</h3>", unsafe_allow_html=True)
    
    with col3:
        st.success(f"**Kriter {criterion_b[0].upper()}**\n\n**{criterion_b[1]}**\n\n_{criterion_b[2]}_")
    
    st.markdown("---")
    
    # Soru
    st.markdown("### ❓ Hangi kriter daha önemlidir?")
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    
    with col_b:
        # Önce hangisinin önemli olduğunu seç
        choice = st.radio(
            "Daha önemli olan kriter:",
            [f"Kriter {criterion_a[0].upper()}: {criterion_a[1]}", 
             "Eşit önemde",
             f"Kriter {criterion_b[0].upper()}: {criterion_b[1]}"],
            key=f"choice_{stage_key}_{pair_key}",
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
                key=f"importance_{stage_key}_{pair_key}"
            )
    
    # Yanıtı kaydet ve devam et
    col_prev, col_next = st.columns(2)
    
    with col_prev:
        if pair_idx > 0:
            if st.button("⬅️ Önceki", key=f"prev_{stage_key}_{pair_idx}"):
                st.session_state[f'pair_idx_{stage_key}'] = pair_idx - 1
                st.rerun()
    
    with col_next:
        if st.button("Devam ➡️" if pair_idx < len(pairs) - 1 else "Bu Aşamayı Tamamla ✓", key=f"next_{stage_key}_{pair_idx}"):
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
            
            # Otomatik kayıt: Tüm aşamalar tamamlandı mı kontrol et
            check_and_auto_save()
            
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
    
    st.markdown(f"**Uzman:** {st.session_state.expert_name}")
    
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
            st.info("👉 Üstteki **'3️⃣ Olgunluk'** sekmesine tıklayarak devam edin.")
    
    # 3. Aşama
    with tabs[1]:
        st.header(CRITERIA["stage3"]["name"])
        if 'stage2' in st.session_state.responses and len(st.session_state.responses['stage2']) > 0:
            if f'pair_idx_stage3' not in st.session_state:
                st.session_state['pair_idx_stage3'] = 0
            
            completed = display_comparison("stage3", st.session_state['pair_idx_stage3'])
            if completed:
                st.success("✅ 3. Aşama tamamlandı!")
                st.info("👉 Üstteki **'4️⃣ Etki ve Kalite'** sekmesine tıklayarak devam edin.")
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
                st.info("👉 Üstteki **'🔗 Aşamalar Arası'** sekmesine tıklayarak devam edin.")
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
                
                # Otomatik kaydet (henüz kaydedilmemişse)
                if not st.session_state.get('auto_saved', False):
                    with st.spinner('Değerlendirmeniz kaydediliyor...'):
                        success = save_results_to_server()
                        if success:
                            st.session_state.auto_saved = True
                            st.success("✅ Değerlendirmeniz otomatik olarak kaydedildi!")
                            st.balloons()
                        else:
                            st.error("⚠️ Otomatik kayıt başarısız. Lütfen 'Sonuçlar' sekmesinden manuel olarak kaydedin.")
                else:
                    st.info("✅ Değerlendirmeniz daha önce kaydedildi.")
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
    
    # Özet bilgiler
    for stage_key, responses in st.session_state.responses.items():
        stage_name = CRITERIA[stage_key]["name"]
        st.write(f"**{stage_name}:** {len(responses)} karşılaştırma tamamlandı ✅")
    
    st.markdown("---")
    
    # Tüm aşamalar tamamlandı mı kontrol et
    all_completed = (
        'stage2' in st.session_state.responses and 
        'stage3' in st.session_state.responses and 
        'stage4' in st.session_state.responses and 
        'stage_comparison' in st.session_state.responses
    )
    
    if all_completed:
        # Otomatik kayıt yapıldı mı bildir
        if st.session_state.get('auto_saved', False):
            st.success("✅ Değerlendirmeniz otomatik olarak kaydedildi!")
        
        st.success("🎉 Tüm aşamalar tamamlandı!")
        
        if st.button("💾 Sonuçları Tekrar Kaydet", type="primary"):
            # Manuel kayıt (yedek için)
            success = save_results_to_server()
            if success:
                st.success("✅ Değerlendirmeniz yeniden kaydedildi!")
                st.balloons()
                st.info("Teşekkür ederiz! Sayfayı kapatabilirsiniz.")
            else:
                st.error("❌ Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.")
    else:
        st.warning("⚠️ Lütfen tüm aşamaları tamamlayın.")

def save_results_to_server():
    """Sonuçları Google Sheets'e kaydet (sadece JSON olarak)"""
    try:
        # Google Sheets credentials
        credentials_dict = st.secrets.get("gcp_service_account", None)
        
        if not credentials_dict or not GOOGLE_SHEETS_AVAILABLE:
            # Fallback: Local kayıt
            return save_to_local_temp()
        
        # Google Sheets bağlantısı
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict, scope)
        client = gspread.authorize(credentials)
        
        # Spreadsheet aç (ID Streamlit secrets'ta)
        spreadsheet_id = st.secrets.get("spreadsheet_id", None)
        if not spreadsheet_id:
            return save_to_local_temp()
        
        sheet = client.open_by_key(spreadsheet_id).sheet1
        
        # Veri hazırla - SADECE 4 SÜTUN
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        expert_name = st.session_state.expert_name
        expert_org = st.session_state.get('expert_org', '')
        
        # Tüm veriyi JSON olarak
        json_data = json.dumps(st.session_state.responses, ensure_ascii=False)
        
        # Tek satır, 4 sütun
        row_data = [timestamp, expert_name, expert_org, json_data]
        
        # Satırı ekle
        sheet.append_row(row_data)
        
        return True
        
    except Exception as e:
        print(f"Google Sheets kayıt hatası: {e}")
        # Fallback: Local kayıt
        return save_to_local_temp()

def save_to_local_temp():
    """Yedek: Local temp klasörüne kaydet"""
    try:
        data = {
            "expert_name": st.session_state.expert_name,
            "expert_org": st.session_state.get('expert_org', ''),
            "timestamp": datetime.now().isoformat(),
            "responses": st.session_state.responses
        }
        
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        safe_name = st.session_state.expert_name.replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"degerlendirme_{safe_name}_{timestamp}.json"
        
        save_path = f"/tmp/{filename}"
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        return True
        
    except Exception as e:
        print(f"Local kayıt hatası: {e}")
        return False

# Ana uygulama
def main():
    if st.session_state.current_stage == "welcome":
        welcome_page()
    else:
        main_evaluation()

if __name__ == "__main__":
    main()
