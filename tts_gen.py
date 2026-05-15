import subprocess
import os

def generate_tts(text, output_path="output_audio.mp3"):
    """
    edge-tts를 사용하여 텍스트를 음성으로 변환합니다.
    """
    # 한국어 음성 화자 (여성: ko-KR-SunHiNeural, 남성: ko-KR-InJoonNeural)
    voice = "ko-KR-SunHiNeural"
    
    vtt_path = output_path.replace(".mp3", ".vtt")
    
    try:
        # edge-tts CLI 명령어 실행
        command = [
            "edge-tts",
            "--text", text,
            "--voice", voice,
            "--write-media", output_path,
            "--write-subtitles", vtt_path
        ]
        
        subprocess.run(command, check=True)
        print(f"TTS generated successfully: {output_path}, Subtitles: {vtt_path}")
        return output_path, vtt_path
        
    except Exception as e:
        print(f"Error generating TTS: {e}")
        return None, None
