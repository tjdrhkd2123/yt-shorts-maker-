from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, ColorClip, VideoFileClip
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
import re
import textwrap
import platform

def resize_image_for_shorts(img_path, target_size=(1080, 1920)):
    """
    이미지를 유튜브 쇼츠 크기에 맞게 조정합니다 (크롭 없이 여백을 검은색으로 패딩).
    """
    try:
        img = Image.open(img_path)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
            
        # 가로 세로 비율 유지하며 리사이즈 (썸네일 방식으로 맞춤)
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # 검은색 배경 생성
        background = Image.new('RGB', target_size, (0, 0, 0))
        
        # 중앙 배치
        offset = (
            (target_size[0] - img.width) // 2,
            (target_size[1] - img.height) // 2
        )
        background.paste(img, offset)
        
        new_path = img_path + "_padded.jpg"
        background.save(new_path)
        return new_path
    except Exception as e:
        print(f"Error resizing image {img_path}: {e}")
        return img_path

def parse_vtt(vtt_path):
    """
    VTT 파일에서 타임스탬프와 텍스트를 추출합니다.
    """
    subs = []
    if not vtt_path or not os.path.exists(vtt_path):
        return subs
        
    def time_to_seconds(t_str):
        # 00:00:01.000 또는 00:00:01,000 형식 파싱
        t_str = t_str.replace(',', '.')
        parts = t_str.strip().split(':')
        s = float(parts[-1])
        m = int(parts[-2])
        h = int(parts[-3]) if len(parts) > 2 else 0
        return h * 3600 + m * 60 + s

    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        start_time = None
        end_time = None
        text_lines = []
        
        for line in lines:
            line = line.strip()
            if '-->' in line:
                if start_time is not None and text_lines:
                    # 이전 자막 저장
                    subs.append((start_time, end_time, " ".join(text_lines)))
                    text_lines = []
                    
                times = line.split('-->')
                start_time = time_to_seconds(times[0])
                end_time = time_to_seconds(times[1])
            elif line and not line.startswith('WEBVTT') and not line.isdigit():
                text_lines.append(line)
                
        # 마지막 자막 저장
        if start_time is not None and text_lines:
            subs.append((start_time, end_time, " ".join(text_lines)))
    except Exception as e:
        print(f"Error parsing VTT: {e}")
        
    return subs

def hex_to_rgba(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return (255, 255, 255, 255)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)

def create_subtitle_clip(text, duration, target_size=(1080, 1920), font_style="맑은 고딕", font_size=60, font_color="#FFFFFF", use_bg_box=True):
    """
    PIL을 이용하여 투명 배경에 자막을 그리고 클립으로 만듭니다. (ImageMagick 오류 우회)
    """
    img = Image.new('RGBA', target_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font_map = {
        "맑은 고딕": "malgun.ttf",
        "굴림": "gulim.ttc",
        "바탕": "batang.ttc"
    }
    font_file = font_map.get(font_style, "malgun.ttf")
    
    if platform.system() == "Windows":
        font_path = f"C:\\Windows\\Fonts\\{font_file}"
    else:
        # 클라우드 배포용 리눅스 환경 (packages.txt에서 fonts-nanum 설치 시 경로)
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        try:
            # 실패 시 로컬 또는 다른 기본 폰트 재시도
            font = ImageFont.truetype("NanumGothic.ttf", font_size)
        except:
            font = ImageFont.load_default()
            
    # 텍스트 줄바꿈 처리 (한 줄이 너무 길어 화면 밖으로 잘리는 현상 방지)
    # 글자 크기에 따라 한 줄에 들어갈 글자 수를 조절
    chars_per_line = int(1080 / (font_size * 0.9)) # 대략적인 글자 수 계산
    wrapped_text = "\n".join(textwrap.wrap(text, width=chars_per_line))
    
    # 텍스트 크기 계산
    try:
        bbox = draw.textbbox((0,0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width, text_height = draw.textsize(wrapped_text, font=font)
        
    # 하단 중앙 배치
    x = (target_size[0] - text_width) / 2
    y = target_size[1] - text_height - 300
    
    # 배경 박스 그리기 (겹침 방지 및 가독성 향상)
    if use_bg_box:
        padding_x = 40
        padding_y = 20
        box_bbox = [x - padding_x, y - padding_y, x + text_width + padding_x, y + text_height + padding_y]
        try:
            # Pillow 최신 버전 지원 시 둥근 사각형
            draw.rounded_rectangle(box_bbox, radius=15, fill=(0, 0, 0, 180))
        except:
            draw.rectangle(box_bbox, fill=(0, 0, 0, 180))
            
    # 텍스트 윤곽선 (잘 보이게 검정색 테두리)
    outline_color = (0, 0, 0, 255)
    for adj in range(-3, 4):
        for adj2 in range(-3, 4):
            draw.text((x+adj, y+adj2), wrapped_text, font=font, fill=outline_color, align="center")
            
    # 텍스트 채우기 (사용자 지정 색상)
    fill_color = hex_to_rgba(font_color)
    draw.text((x, y), wrapped_text, font=font, fill=fill_color, align="center")
    
    import time
    temp_path = f"temp_assets/temp_subtitle_{hash(text)}_{time.time()}.png"
    img.save(temp_path)
    
    clip = ImageClip(temp_path).with_duration(duration)
    return clip, temp_path

def create_video(image_paths, audio_path, vtt_path=None, output_path="final_shorts.mp4", font_style="맑은 고딕", font_size=60, font_color="#FFFFFF", use_bg_box=True):
    """
    이미지들과 오디오, 자막을 결합하여 영상을 생성합니다.
    """
    temp_files = []
    try:
        # 오디오 로드
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        
        if not image_paths:
            print("No images found to create video.")
            return None
            
        # 각 이미지가 보여질 시간 계산
        duration_per_image = total_duration / len(image_paths)
        
        image_clips = []
        for media_path in image_paths:
            ext = media_path.lower().split('.')[-1]
            if ext in ['mp4', 'mov', 'avi']:
                try:
                    clip = VideoFileClip(media_path).without_audio()
                    # 썸네일 방식 리사이즈 (가로세로 비율 유지)
                    ratio = min(1080 / clip.w, 1920 / clip.h)
                    clip = clip.resized((int(clip.w * ratio), int(clip.h * ratio)))
                    
                    if clip.duration > duration_per_image:
                        clip = clip.subclipped(0, duration_per_image)
                        
                    bg_clip = ColorClip(size=(1080, 1920), color=(0,0,0)).with_duration(duration_per_image)
                    clip = CompositeVideoClip([bg_clip, clip.with_position("center")]).with_duration(duration_per_image)
                    image_clips.append(clip)
                except Exception as ve:
                    print(f"Error processing video {media_path}: {ve}")
            else:
                resized_path = resize_image_for_shorts(media_path)
                temp_files.append(resized_path)
                clip = ImageClip(resized_path).with_duration(duration_per_image)
                image_clips.append(clip)
            
        # 기본 영상 (이미지 슬라이드쇼)
        base_video = concatenate_videoclips(image_clips, method="compose")
        
        # 자막 클립 생성
        subs = parse_vtt(vtt_path)
        subtitle_clips = []
        
        for start, end, text in subs:
            duration = end - start
            if duration <= 0: continue
            
            # VTT 텍스트 전처리 (태그 제거 등)
            text = re.sub(r'<[^>]+>', '', text)
            
            sub_clip, t_path = create_subtitle_clip(text, duration, target_size=(1080, 1920), font_style=font_style, font_size=font_size, font_color=font_color, use_bg_box=use_bg_box)
            temp_files.append(t_path)
            
            sub_clip = sub_clip.with_start(start).with_position(("center", "center"))
            subtitle_clips.append(sub_clip)
            
        # 기본 영상 위에 자막 합성
        if subtitle_clips:
            final_video = CompositeVideoClip([base_video] + subtitle_clips)
        else:
            final_video = base_video
            
        # 오디오 설정 및 길이 맞춤
        final_video = final_video.with_audio(audio_clip)
        final_video = final_video.with_duration(total_duration)
        
        final_video.write_videofile(
            output_path, 
            fps=15, # 렌더링 속도 향상을 위해 24 -> 15프레임으로 하향
            preset="ultrafast", # 렌더링 속도 최적화
            codec="libx264", 
            audio_codec="aac",
            threads=4
        )
        
        # 사용된 임시 파일 정리
        for f in temp_files:
            try: os.remove(f)
            except: pass
            
        return output_path
        
    except Exception as e:
        print(f"Error creating video: {e}")
        return None
