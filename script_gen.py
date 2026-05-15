import requests
import json

def generate_script(title, text_content, api_key=""):
    """
    제품 제목과 텍스트를 바탕으로 유튜브 쇼츠용 대본을 생성합니다.
    api_key가 제공되면 Gemini API를 사용하고, 없으면 기본 템플릿을 사용합니다.
    """
    if not api_key:
        # 무료/기본 템플릿 제공
        desc = text_content[:200] if text_content else "정말 놀라운 디자인과 실용성을 겸비한 아이템입니다."
        script = f"여러분 안녕하세요! 오늘 소개할 대박 제품은 바로 '{title[:50]}' 입니다. "
        script += "요즘 가장 핫한 필수템이라고 할 수 있는데요! "
        script += f"주요 특징을 살펴보면, {desc}... "
        script += "화면의 이미지를 통해 퀄리티와 디테일을 직접 확인해 보세요! "
        script += "실제로 사용해보면 그 편리함에 깜짝 놀라실 거예요. "
        script += "놓치면 정말 후회할 이 제품, 더 늦기 전에 지금 바로 확인해보시고 득템하세요! "
        script += "오늘 영상이 도움되셨다면 구독과 좋아요 부탁드립니다!"
        return script
    
    # Gemini API 호출 (REST API 방식)
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        prompt = f"""
        당신은 유튜브 쇼츠 대본 작성 전문가입니다.
        다음 제품 정보를 바탕으로 50초~60초 분량(약 300~400자 내외)의 유튜브 쇼츠용 대본을 작성해주세요.
        사람이 자연스럽게 말하는 톤(해요체 등)으로 작성하고, 시청자의 호기심과 구매 욕구를 강하게 유발하세요. 제품의 특징을 콕 집어 설명해주세요.
        이모지나 특수문자는 TTS 음성 변환에 방해될 수 있으니 절대 사용하지 마세요.
        오직 대본 텍스트만 출력하세요.
        
        제품 제목: {title}
        제품 설명 요약: {text_content[:1500]}
        """
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        generated_text = result['candidates'][0]['content']['parts'][0]['text']
        
        return generated_text.strip()
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return f"안녕하세요! 오늘 소개해 드릴 제품은 {title[:50]} 입니다. 정말 놀라운 제품이죠. 꼭 확인해보세요!"
