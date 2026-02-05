import google.generativeai as genai
import os
from PIL import Image

# API 키 설정 (환경 변수 또는 직접 입력)
# 실제 배포 시에는 st.secrets 등을 사용해야 함
def setup_ai(api_key):
    genai.configure(api_key=api_key)

def analyze_image(image_path, api_key):
    setup_ai(api_key)
    
    # 모델 설정
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 시스템 프롬프트 설정
    system_prompt = """
    당신은 20년 경력의 대학병원 수석 방사선사이자 '황 교수'입니다. 
    학생이 이미지를 올리면 다음 모든 모달리티를 커버하여 분석하세요: 
    일반촬영(X-ray), 투시조영, 혈관조영, CT, MRI, 핵의학, 방사선치료, 초음파, 장비 QC/QA 영상.

    반드시 다음 순서로 답변해야 합니다:
    1. [영상 식별]: 촬영 부위, 모달리티(Modality), 검사명(Protocol) 정의.
    2. [상세 해설]: 주요 해부학적 구조, 영상의 기술적 특징, 잘된 점과 잘못된 점 분석.
    3. [국가고시 핵심 요약]: 이 영상과 관련하여 국가시험에 자주 나오는 핵심 암기 사항 3가지.
    4. [교수님의 조언]: 임상 실무 팁이나 격려의 말 (부드럽지만 날카로운 조언).
    """
    
    img = Image.open(image_path)
    
    response = model.generate_content([system_prompt, img])
    return response.text
