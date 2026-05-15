import streamlit as st
import asyncio
import os
import shutil
from scraper import fetch_page_data, download_images
from script_gen import generate_script
from tts_gen import generate_tts
from video_maker import create_video

st.set_page_config(page_title="유튜브 쇼츠 자동 생성기", page_icon="🎥", layout="centered")

st.title("🎥 유튜브 쇼츠 자동 생성기")
st.markdown("쿠팡, 네이버 스마트스토어 등 쇼핑몰의 보안 정책(봇 차단)이 강력하여 자동 수집이 막히는 경우가 많습니다. **막힐 경우 '수동 업로드' 탭을 이용해 주세요!**")

api_key = st.text_input("🔑 Gemini API Key (선택사항, 입력시 더 자연스러운 대본 생성):", type="password", help="무료 API 키 발급: Google AI Studio")

tab1, tab2 = st.tabs(["🔗 링크로 자동 생성", "📁 수동 업로드 (차단 대비)"])

def process_pipeline(title, text_content, image_paths, status, font_style="맑은 고딕", font_size=60, font_color="#FFFFFF", use_bg_box=True):
    try:
        # 2. 대본 생성
        st.write("2️⃣ 대본(스크립트) 생성 중...")
        script = generate_script(title, text_content, api_key)
        st.info(f"생성된 대본: {script}")
        
        # 3. 음성 생성 (TTS)
        st.write("3️⃣ 음성(TTS) 생성 중...")
        audio_path = os.path.join("temp_assets", "audio.mp3")
        generated_audio, vtt_path = generate_tts(script, audio_path)
        
        if not generated_audio:
            st.error("음성 생성에 실패했습니다.")
            status.update(label="생성 실패", state="error", expanded=True)
            st.stop()
        st.write("✅ 음성 파일 생성 완료.")
        
        # 4. 영상 생성
        st.write("4️⃣ 영상 합성 및 렌더링 중...")
        output_video_path = "final_shorts.mp4"
        
        if os.path.exists(output_video_path):
            os.remove(output_video_path)
            
        video_result = create_video(image_paths, generated_audio, vtt_path, output_video_path, font_style, font_size, font_color, use_bg_box)
        
        if video_result and os.path.exists(video_result):
            status.update(label="🎉 영상 생성 완료!", state="complete", expanded=False)
            st.success("쇼츠 영상이 성공적으로 만들어졌습니다!")
            
            with open(video_result, "rb") as file:
                video_bytes = file.read()
            st.video(video_bytes)
            
            st.download_button(
                label="⬇️ 영상 다운로드",
                data=video_bytes,
                file_name="youtube_shorts.mp4",
                mime="video/mp4"
            )
        else:
            st.error("영상 렌더링에 실패했습니다.")
            status.update(label="생성 실패", state="error", expanded=True)
            
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        status.update(label="생성 실패", state="error", expanded=True)


with tab1:
    st.markdown("웹페이지 URL을 입력하여 자동으로 데이터와 이미지를 수집합니다. (일부 사이트 차단 가능성 있음)")
    url = st.text_input("제품 링크 (URL):", placeholder="https://www.coupang.com/vp/products/...")
    
    if st.button("자동 수집으로 쇼츠 만들기", type="primary"):
        if not url:
            st.error("URL을 입력해주세요!")
        else:
            with st.status("🚀 영상 생성 중... (최대 1~2분 소요)", expanded=True) as status:
                temp_dir = "temp_assets"
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                os.makedirs(temp_dir, exist_ok=True)
                
                st.write("1️⃣ 웹페이지 분석 및 이미지 수집 중...")
                data = asyncio.run(fetch_page_data(url))
                
                if not data['images']:
                    st.error("이미지를 찾을 수 없습니다. 보안 정책에 의해 접근이 차단되었거나 지원하지 않는 링크일 수 있습니다. 상단의 '수동 업로드' 탭을 이용해 주세요.")
                    status.update(label="수집 차단됨", state="error", expanded=True)
                    st.stop()
                    
                st.write(f"✅ 제목: {data['title'][:30]}...")
                
                image_paths = download_images(data['images'], temp_dir)
                if not image_paths:
                    st.error("이미지 다운로드에 실패했습니다. (0장)")
                    status.update(label="생성 실패", state="error", expanded=True)
                    st.stop()
                    
                st.write(f"✅ 이미지 {len(image_paths)}장 다운로드 완료.")
                process_pipeline(data['title'], data['text_content'], image_paths, status, font_style, font_size, font_color, use_bg_box)

with tab2:
    st.markdown("자동 수집이 막히는 사이트의 경우, 이미지를 직접 다운받아 이곳에 올려주시면 똑같이 대본과 음성을 입혀 영상을 제작해 드립니다.")
    manual_title = st.text_input("제품 이름 (제목):", placeholder="예: 초경량 무선 청소기")
    manual_desc = st.text_area("제품 특징 설명 (대본에 반영됩니다):", placeholder="가볍고 흡입력이 강력하며, 배터리가 오래갑니다.")
    uploaded_files = st.file_uploader("제품 이미지 또는 영상 업로드 (여러 개 가능)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'webp', 'mp4', 'mov', 'avi'])
    
    st.markdown("### 🎨 자막 설정 및 미리보기")
    col1, col2, col3 = st.columns(3)
    with col1:
        font_style = st.selectbox("폰트 종류", ["맑은 고딕", "굴림", "바탕"])
    with col2:
        font_size = st.slider("자막 크기", 40, 100, 60, step=5)
    with col3:
        font_color = st.color_picker("자막 색상", "#FFFFFF")
        
    use_bg_box = st.checkbox("자막 배경 박스 사용 (이미지 겹침 방지 및 가독성 향상)", value=True)
        
    font_family_map = {
        "맑은 고딕": "'Malgun Gothic', '맑은 고딕', sans-serif",
        "굴림": "'Gulim', '굴림', sans-serif",
        "바탕": "'Batang', '바탕', serif"
    }
    css_font = font_family_map.get(font_style, "sans-serif")
    
    bg_style = "background-color: rgba(0, 0, 0, 0.7); padding: 15px 30px; border-radius: 15px;" if use_bg_box else ""
    
    preview_html = f"""
<div style="background-color: #2b2b2b; background-image: linear-gradient(45deg, #1f1f1f 25%, transparent 25%, transparent 75%, #1f1f1f 75%, #1f1f1f), linear-gradient(45deg, #1f1f1f 25%, transparent 25%, transparent 75%, #1f1f1f 75%, #1f1f1f); background-size: 20px 20px; background-position: 0 0, 10px 10px; height: 180px; display: flex; align-items: flex-end; justify-content: center; padding-bottom: 20px; border-radius: 10px; border: 2px dashed #666; margin-bottom: 20px;">
    <div style="{bg_style} font-family: {css_font}; font-size: {font_size * 0.7}px; color: {font_color}; text-align: center; font-weight: bold; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000; line-height: 1.4;">
        적용된 폰트, 크기, 색상입니다!<br>긴 문장은 자동으로 줄바꿈됩니다.
    </div>
</div>
    """
    st.markdown("#### 👀 자막 미리보기 화면")
    st.markdown(preview_html, unsafe_allow_html=True)
    
    if st.button("수동 입력 정보로 쇼츠 만들기", type="primary"):
        if not manual_title or not uploaded_files:
            st.error("제품 이름과 미디어(이미지/영상)를 최소 1개 이상 업로드해주세요!")
        else:
            with st.status("🚀 영상 생성 중... (최대 1~2분 소요)", expanded=True) as status:
                temp_dir = "temp_assets"
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                os.makedirs(temp_dir, exist_ok=True)
                
                st.write("1️⃣ 업로드된 이미지 처리 중...")
                image_paths = []
                for i, file in enumerate(uploaded_files):
                    file_path = os.path.join(temp_dir, f"manual_{i}_{file.name}")
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    image_paths.append(file_path)
                st.write(f"✅ 이미지 {len(image_paths)}장 준비 완료.")
                
                process_pipeline(manual_title, manual_desc, image_paths, status, font_style, font_size, font_color, use_bg_box)
