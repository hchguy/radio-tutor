import streamlit as st
import pandas as pd
from database import init_db, add_user, authenticate_user, get_user, get_pending_users, update_user_status, delete_user
from ai_tutor import analyze_image
import os
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="방사선사 국가시험 AI 튜터", page_icon="🩺", layout="wide")

# CSS 스타일 적용 (청색 & 화이트 톤)
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #004a99;
        color: white;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    h1, h2, h3 {
        color: #004a99;
    }
    .status-pending {
        color: orange;
        font-weight: bold;
    }
    .status-active {
        color: green;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False

# DB 초기화
init_db()

# 관리자 정보
ADMIN_ID = "2018015"
ADMIN_PW = "745840"

def login_page():
    st.title("🩺 방사선사 AI 튜터 로그인")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("사용자 로그인")
        student_id = st.text_input("학번", key="login_id")
        password = st.text_input("비밀번호", type="password", key="login_pw")
        
        if st.button("로그인"):
            # 관리자 체크
            if student_id == ADMIN_ID and password == ADMIN_PW:
                st.session_state.logged_in = True
                st.session_state.admin_mode = True
                st.session_state.user_info = {"name": "관리자", "student_id": ADMIN_ID}
                st.rerun()
            
            # 일반 사용자 체크
            user = authenticate_user(student_id, password)
            if user:
                status = user[5]
                if status == 'Pending':
                    st.warning("⚠️ 관리자의 승인이 필요합니다.")
                elif status == 'Active':
                    st.session_state.logged_in = True
                    st.session_state.admin_mode = False
                    st.session_state.user_info = {"student_id": user[0], "name": user[1], "email": user[2]}
                    st.rerun()
                else:
                    st.error("❌ 계정이 비활성화되었거나 거절되었습니다.")
            else:
                st.error("❌ 정보 불일치: 학번 또는 비밀번호를 확인하세요.")

    with col2:
        st.subheader("회원가입")
        new_id = st.text_input("학번 (ID)", key="reg_id")
        new_name = st.text_input("이름", key="reg_name")
        new_email = st.text_input("이메일", key="reg_email")
        new_phone = st.text_input("전화번호", key="reg_phone")
        new_pw = st.text_input("비밀번호", type="password", key="reg_pw")
        
        if st.button("회원가입 신청"):
            if new_id and new_name and new_email and new_phone and new_pw:
                if add_user(new_id, new_name, new_email, new_phone, new_pw):
                    st.success("✅ 회원가입 신청 완료! 관리자 승인 후 이용 가능합니다.")
                else:
                    st.error("❌ 이미 존재하는 학번입니다.")
            else:
                st.warning("⚠️ 모든 필드를 입력해주세요.")

def admin_dashboard():
    st.title("🛡️ 관리자 대시보드")
    st.subheader("승인 대기 회원 목록")
    
    pending_users = get_pending_users()
    if not pending_users:
        st.info("현재 승인 대기 중인 회원이 없습니다.")
    else:
        df = pd.DataFrame(pending_users, columns=["학번", "이름", "이메일", "전화번호", "상태"])
        st.table(df)
        
        for user in pending_users:
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"**{user[1]}** ({user[0]})")
            if col2.button(f"승인", key=f"approve_{user[0]}"):
                update_user_status(user[0], 'Active')
                st.success(f"{user[1]} 학생의 계정이 승인되었습니다.")
                st.rerun()
            if col3.button(f"거절", key=f"reject_{user[0]}"):
                update_user_status(user[0], 'Rejected')
                st.error(f"{user[1]} 학생의 계정이 거절되었습니다.")
                st.rerun()

def main_ai_tutor():
    st.title("🧠 AI 방사선 영상 분석 (AI Tutor)")
    st.write(f"반갑습니다, **{st.session_state.user_info['name']}** 학생! 분석할 영상을 업로드해주세요.")
    
    # API 키 설정: Streamlit Secrets 또는 사이드바 입력
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Streamlit Cloud 설정에서 GEMINI_API_KEY를 등록하면 편리합니다.")
    
    uploaded_file = st.file_uploader("방사선 영상 업로드 (JPG, PNG)", type=["jpg", "jpeg", "png"])
    camera_photo = st.camera_input("또는 카메라로 촬영")
    
    target_image = uploaded_file if uploaded_file else camera_photo
    
    if target_image:
        st.image(target_image, caption="업로드된 영상", use_container_width=True)
        
        if st.button("황 교수님께 분석 요청하기"):
            if not api_key:
                st.error("⚠️ AI 분석을 위해 Gemini API Key가 필요합니다.")
            else:
                with st.spinner("황 교수님이 영상을 분석 중입니다..."):
                    try:
                        # 임시 파일 저장
                        temp_path = "temp_image.png"
                        with open(temp_path, "wb") as f:
                            f.write(target_image.getbuffer())
                        
                        analysis_result = analyze_image(temp_path, api_key)
                        
                        st.markdown("---")
                        st.subheader("👨‍🏫 황 교수님의 분석 결과")
                        st.markdown(analysis_result)
                        
                        # 임시 파일 삭제
                        os.remove(temp_path)
                    except Exception as e:
                        st.error(f"분석 중 오류가 발생했습니다: {e}")

# 사이드바 구성
if st.session_state.logged_in:
    st.sidebar.title("메뉴")
    if st.session_state.admin_mode:
        st.sidebar.info("로그인 상태: 관리자")
        if st.sidebar.button("관리자 대시보드"):
            st.session_state.page = "admin"
    else:
        st.sidebar.info(f"로그인 상태: {st.session_state.user_info['name']} 학생")
        if st.sidebar.button("AI 분석 홈"):
            st.session_state.page = "home"
    
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.session_state.admin_mode = False
        st.rerun()

# 페이지 라우팅
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.admin_mode:
        admin_dashboard()
    else:
        main_ai_tutor()
