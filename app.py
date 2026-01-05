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
    page_title="Net Zero Proje Değerlendirme",
    page_icon="🌱",
    layout="wide"
)

# 11 BENZERSİZ KRİTER - TÜM PROJE TÜRLERİNDE AYNI
COMMON_CRITERIA = [
    ("a", "Finansal Analiz", "Projenin finansal fizibilitesi ile maliyet ve kaynak kullanımının karar alma sürecini destekleyecek yeterlilikte analiz edilip edilmediği değerlendirilir."),
    ("b", "Çevresel Etki", "Projenin çevresel etkilerini; GHG azaltımı (CO₂, CH₄, N₂O), enerji tüketimindeki düşüş ve hava kalitesindeki iyileşme (NOₓ, PM10, NMHC) gibi göstergeler üzerinden değerlendirir."),
    ("c", "İzlenebilirlik", "Eytemin ilerlemesinin düzenli olarak takip edilebilmesi, süreç ve sonuç bilgilerinin şeffaf bir şekilde izlenebilir ve raporlanabilir olmasıdır."),
    ("d", "Ölçülebilirlik", "Eytemin başarısının nicel göstergelerle değerlendirilebilmesi, hedeflerin sayısal olarak tanımlanması ve sonuçların objektif biçimde ölçülebilmesidir."),
    ("e", "Zaman Etkisi", "Emisyon azaltımının ne zaman devreye girdiği– kısa vade etki 0-5 yıl, orta vade etki 5-10, uzun vadede etki 10+ yıl."),
    ("f", "Risk Yönetim Planı / Analizi", "Proje kapsamında teknik, idari ve yasal risklerin tanımlanma düzeyi, bu risklere yönelik önlemlerin azaltıcı stratejilerin yeterliliği değerlendirilir."),
    ("g", "İnovasyon ve Katma Değer", "Projenin yeni yöntemler, araçlar veya süreçler geliştirerek kurumsal, sektörel veya toplumsal düzeyde somut katma değer üretme potansiyelini değerlendirir."),
    ("h", "Yapılabilirlik", "Projenin mevcut kapasite, zaman, teknik koşullar ve ekip yetkinliği altında gerçekçi ve uygulanabilir olup olmadığı değerlendirilir."),
    ("i", "Bilgi Transferi", "Proje kapsamında üretilen bilgi ve yöntemlerin kurum personeline aktarılması ve proje sonrasında bağımsız şekilde kullanılabilir olması değerlendirilir."),
    ("j", "Çarpan Etkisi", "Projenin doğrudan çıktılarının ötesinde ek ekonomik, sosyal veya çevresel faydalar üretme potansiyelini değerlendirir."),
    ("k", "Ölçek Ekonomileri", "Projenin etkidiği nüfusun ve coğrafi alanın büyüklüğünü değerlendirir."),
]

# Proje türleri
PROJECT_TYPES = {
    "stage2": {
        "name": "İnovasyon ve Ar-Ge Projesi",
        "criteria": COMMON_CRITERIA
    },
    "stage3": {
        "name": "Teknik Destek Projesi",
        "criteria": COMMON_CRITERIA
    },
    "stage4": {
        "name": "Yapım İşleri / Altyapı Projesi",
        "criteria": COMMON_CRITERIA
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

def save_response(stage, pair_key, winner_choice, importance):
    """Yanıtı ESKİ FORMATTA kaydet: "e_f": "2e" """
    if stage not in st.session_state.responses:
        st.session_state.responses[stage] = {}
    
    # stage2 -> "2", stage3 -> "3", stage4 -> "4"
    stage_num = stage.replace("stage", "")
    
    # Eşit seçildiyse "0", değilse kazanan kriter + stage numarası
    if winner_choice == "equal":
        value = "0"
    else:
        # winner_choice "a" veya "b" gibi gelecek
        value = f"{stage_num}{winner_choice}"  # Örnek: "2e" veya "3a"
    
    st.session_state.responses[stage][pair_key] = value

def check_and_auto_save():
    """Tüm aşamalar tamamlandıysa otomatik kaydet"""
    if 'auto_saved' in st.session_state and st.session_state.auto_saved:
        return
    
    # 11 kriter: C(11,2) = 55 karşılaştırma
    all_completed = (
        'stage2' in st.session_state.responses and 
        len(st.session_state.responses['stage2']) == 55 and
        'stage3' in st.session_state.responses and 
        len(st.session_state.responses['stage3']) == 55 and
        'stage4' in st.session_state.responses and 
        len(st.session_state.responses['stage4']) == 55
    )
    
    if all_completed:
        success = save_results_to_server()
        if success:
            st.session_state.auto_saved = True

def display_comparison(stage_key, pair_idx):
    """Kriter karşılaştırma arayüzü"""
    stage_data = PROJECT_TYPES[stage_key]
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
        choice = st.radio(
            "Daha önemli olan kriter:",
            [f"Kriter {criterion_a[0].upper()}: {criterion_a[1]}", 
             "Eşit önemde",
             f"Kriter {criterion_b[0].upper()}: {criterion_b[1]}"],
            key=f"choice_{stage_key}_{pair_key}",
            index=1
        )
        
        importance = None
        if choice != "Eşit önemde":
            importance = st.select_slider(
                "Önem derecesi:",
                options=[
                    "1 - Az önemli",
                    "2 - Orta derecede önemli",
                    "3 - Önemli", 
                    "4 - Çok önemli",
                    "5 - Son derece önemli"
                ],
                value="3 - Önemli",
                key=f"importance_{stage_key}_{pair_key}"
            )
    
    # Butonlar
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Önceki", key=f"prev_{stage_key}_{pair_idx}", disabled=(pair_idx == 0)):
            st.session_state[f'pair_idx_{stage_key}'] = max(0, pair_idx - 1)
            st.rerun()
    
    with col2:
        if st.button("💾 Kaydet ve İlerle", key=f"save_{stage_key}_{pair_idx}", type="primary"):
            # Kazananı belirle
            if choice == "Eşit önemde":
                winner = "equal"
                importance_value = None
            elif choice.startswith(f"Kriter {criterion_a[0].upper()}"):
                winner = criterion_a[0]
                importance_value = importance.split(" - ")[0] if importance else "1"
            else:
                winner = criterion_b[0]
                importance_value = importance.split(" - ")[0] if importance else "1"
            
            # ESKİ FORMATTA KAYDET
            save_response(stage_key, pair_key, winner, importance_value)
            
            # Sonraki soruya geç
            if pair_idx < len(pairs) - 1:
                st.session_state[f'pair_idx_{stage_key}'] = pair_idx + 1
            st.rerun()
    
    with col3:
        if pair_idx < len(pairs) - 1:
            if st.button("➡️ Atla", key=f"next_{stage_key}_{pair_idx}"):
                st.session_state[f'pair_idx_{stage_key}'] = pair_idx + 1
                st.rerun()
    
    return False

def welcome_page():
    """Karşılama sayfası"""
    st.title("🌱 Net Sıfır Emisyon Proje Değerlendirme Sistemi")
    st.markdown("---")
    
    st.markdown("""
    ### Hoş Geldiniz! 👋
    
    Bu sistem, Net Sıfır Emisyon projelerinin değerlendirilmesi için geliştirilmiştir.
    
    #### 📋 Değerlendirilecek Proje Türleri:
    
    1. **İnovasyon ve Ar-Ge Projesi** (11 kriter - 55 karşılaştırma)
    2. **Teknik Destek Projesi** (11 kriter - 55 karşılaştırma)
    3. **Yapım İşleri / Altyapı Projesi** (11 kriter - 55 karşılaştırma)
    
    #### 🎯 11 Değerlendirme Kriteri:
    
    - Finansal Analiz
    - Çevresel Etki
    - İzlenebilirlik
    - Ölçülebilirlik
    - Zaman Etkisi
    - Risk Yönetim Planı / Analizi
    - İnovasyon ve Katma Değer
    - Yapılabilirlik
    - Bilgi Transferi
    - Çarpan Etkisi
    - Ölçek Ekonomileri
    
    #### 📝 Değerlendirme Süreci:
    
    Her proje türü için aynı 11 kriteri ikili karşılaştırma yöntemiyle değerlendireceksiniz.
    
    - Her karşılaştırmada hangi kriterin daha önemli olduğunu seçin
    - Önem derecesini 1-5 arasında belirleyin (1: Az önemli, 5: Son derece önemli)
    - Eşit önemde seçeneğini de kullanabilirsiniz
    
    #### ⏱️ Süre:
    Toplam 165 karşılaştırma - Ortalama 45-60 dakika
    
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        expert_name = st.text_input("👤 Adınız Soyadınız *", 
                                    value=st.session_state.expert_name,
                                    placeholder="Örn: Ahmet Yılmaz")
    
    with col2:
        expert_org = st.text_input("🏢 Kurumunuz (İsteğe bağlı)", 
                                   value=st.session_state.get('expert_org', ''),
                                   placeholder="Örn: Ulaştırma Bakanlığı")
    
    st.markdown("---")
    
    if st.button("🚀 Değerlendirmeye Başla", type="primary", disabled=not expert_name):
        st.session_state.expert_name = expert_name
        st.session_state.expert_org = expert_org
        st.session_state.current_stage = "evaluation"
        st.rerun()
    
    if not expert_name:
        st.warning("⚠️ Lütfen adınızı soyadınızı girin.")

def main_evaluation():
    """Ana değerlendirme ekranı"""
    st.title("🌱 Net Sıfır Emisyon Proje Değerlendirme")
    
    # Üst bilgi
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.info(f"👤 **Uzman:** {st.session_state.expert_name}")
    with col2:
        if st.session_state.get('expert_org'):
            st.info(f"🏢 **Kurum:** {st.session_state.expert_org}")
    with col3:
        if st.button("🔄 Yeniden Başla"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    
    # Sekmeler - 3 proje türü + Sonuçlar
    tabs = st.tabs([
        "🔬 " + PROJECT_TYPES["stage2"]["name"],
        "🛠️ " + PROJECT_TYPES["stage3"]["name"],
        "🏗️ " + PROJECT_TYPES["stage4"]["name"],
        "📊 Sonuçlar"
    ])
    
    # İnovasyon ve Ar-Ge
    with tabs[0]:
        st.header(PROJECT_TYPES["stage2"]["name"])
        st.write("**11 kriter - 55 karşılaştırma**")
        
        if f'pair_idx_stage2' not in st.session_state:
            st.session_state['pair_idx_stage2'] = 0
        
        completed = display_comparison("stage2", st.session_state['pair_idx_stage2'])
        if completed:
            st.success("✅ İnovasyon ve Ar-Ge Projesi değerlendirmesi tamamlandı!")
            st.info("📌 Lütfen yukarıdaki **'🛠️ Teknik Destek Projesi'** sekmesine tıklayarak devam edin.")
    
    # Teknik Destek
    with tabs[1]:
        st.header(PROJECT_TYPES["stage3"]["name"])
        st.write("**11 kriter - 55 karşılaştırma**")
        
        if f'pair_idx_stage3' not in st.session_state:
            st.session_state['pair_idx_stage3'] = 0
        
        completed = display_comparison("stage3", st.session_state['pair_idx_stage3'])
        if completed:
            st.success("✅ Teknik Destek Projesi değerlendirmesi tamamlandı!")
            st.info("📌 Lütfen yukarıdaki **'🏗️ Yapım İşleri / Altyapı Projesi'** sekmesine tıklayarak devam edin.")
    
    # Yapım İşleri
    with tabs[2]:
        st.header(PROJECT_TYPES["stage4"]["name"])
        st.write("**11 kriter - 55 karşılaştırma**")
        
        if f'pair_idx_stage4' not in st.session_state:
            st.session_state['pair_idx_stage4'] = 0
        
        completed = display_comparison("stage4", st.session_state['pair_idx_stage4'])
        if completed:
            st.success("✅ Yapım İşleri / Altyapı Projesi değerlendirmesi tamamlandı!")
            st.success("🎉 Tüm değerlendirme tamamlandı!")
            
            # Otomatik kaydet
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
            
            st.info("📌 Yukarıdaki **'📊 Sonuçlar'** sekmesine tıklayarak sonuçlarınızı görebilirsiniz.")
    
    # Sonuçlar
    with tabs[3]:
        st.header("📊 Değerlendirme Sonuçları")
        display_results()

def display_results():
    """Sonuçları göster"""
    if not st.session_state.responses:
        st.info("Henüz değerlendirme yapılmadı.")
        return
    
    # Özet bilgiler
    for stage_key, responses in st.session_state.responses.items():
        stage_name = PROJECT_TYPES[stage_key]["name"]
        total_pairs = 55  # 11 kriter: C(11,2) = 55
        completed = len(responses)
        
        if completed == total_pairs:
            st.write(f"**{stage_name}:** ✅ {completed}/{total_pairs} karşılaştırma tamamlandı")
        else:
            st.write(f"**{stage_name}:** ⏳ {completed}/{total_pairs} karşılaştırma tamamlandı")
    
    st.markdown("---")
    
    # Tüm değerlendirmeler tamamlandı mı
    all_completed = (
        'stage2' in st.session_state.responses and len(st.session_state.responses['stage2']) == 55 and
        'stage3' in st.session_state.responses and len(st.session_state.responses['stage3']) == 55 and
        'stage4' in st.session_state.responses and len(st.session_state.responses['stage4']) == 55
    )
    
    if all_completed:
        if st.session_state.get('auto_saved', False):
            st.success("✅ Değerlendirmeniz otomatik olarak kaydedildi!")
        
        st.success("🎉 Tüm proje türleri için değerlendirme tamamlandı!")
        
        if st.button("💾 Sonuçları Tekrar Kaydet", type="primary"):
            success = save_results_to_server()
            if success:
                st.success("✅ Değerlendirmeniz yeniden kaydedildi!")
                st.balloons()
                st.info("Teşekkür ederiz! Sayfayı kapatabilirsiniz.")
            else:
                st.error("❌ Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.")
        
        # Örnek format göster
        with st.expander("📄 Kaydedilen Veri Formatı (Önizleme)"):
            st.json(st.session_state.responses)
    else:
        st.warning("⚠️ Lütfen tüm proje türleri için değerlendirmeyi tamamlayın.")
        
        # Hangi aşamalar eksik?
        if 'stage2' not in st.session_state.responses or len(st.session_state.responses.get('stage2', {})) < 55:
            st.info("📌 İnovasyon ve Ar-Ge Projesi değerlendirmesini tamamlayın")
        if 'stage3' not in st.session_state.responses or len(st.session_state.responses.get('stage3', {})) < 55:
            st.info("📌 Teknik Destek Projesi değerlendirmesini tamamlayın")
        if 'stage4' not in st.session_state.responses or len(st.session_state.responses.get('stage4', {})) < 55:
            st.info("📌 Yapım İşleri / Altyapı Projesi değerlendirmesini tamamlayın")

def save_results_to_server():
    """Sonuçları Google Sheets'e kaydet - ESKİ FORMATTA"""
    try:
        credentials_dict = st.secrets.get("gcp_service_account", None)
        
        if not credentials_dict or not GOOGLE_SHEETS_AVAILABLE:
            return save_to_local_temp()
        
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict, scope)
        client = gspread.authorize(credentials)
        
        spreadsheet_id = st.secrets.get("spreadsheet_id", None)
        if not spreadsheet_id:
            return save_to_local_temp()
        
        sheet = client.open_by_key(spreadsheet_id).sheet1
        
        # Veri hazırla - ESKİ FORMAT
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        expert_name = st.session_state.expert_name
        expert_org = st.session_state.get('expert_org', '')
        
        # ESKİ FORMAT: {"stage2": {"a_b": "2b", ...}, "stage3": {...}, "stage4": {...}}
        json_data = json.dumps(st.session_state.responses, ensure_ascii=False)
        
        row_data = [timestamp, expert_name, expert_org, json_data]
        
        sheet.append_row(row_data)
        
        return True
        
    except Exception as e:
        print(f"Google Sheets kayıt hatası: {e}")
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
