import streamlit as st
import pandas as pd
from database import init_db, add_user, authenticate_user, get_user, get_pending_users, update_user_status, delete_user, set_setting, get_setting, get_active_users
from ai_tutor import analyze_image
import os
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="방사선사 국가시험 AI 튜터", page_icon="🩺", layout="wide")

# CSS 스타일 적용 (카메라 안내 메시지 제거 포함)
st.markdown("""
    <style>
    /* 기존 스타일 */
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004a99; color: white; }
    h1, h2, h3 { color: #004a99; }
    
    /* 카메라 권한 안내 메시지 숨기기 */
    [data-testid="stCameraInputPermission"] {
        display: none !important;
    }
    
    /* 카메라 설명 텍스트 숨기기 (선택사항) */
    .st-emotion-cache-1v0z8nx {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False

init_db()

ADMIN_ID = "2018015"
ADMIN_PW = "745840"

# 로그아웃 함수
def logout():
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.session_state.admin_mode = False
    st.rerun()

# 사이드바
if st.session_state.logged_in:
    st.sidebar.title("메뉴")
    st.sidebar.info(f"로그인: {st.session_state.user_info['name']}")
    if st.sidebar.button("로그아웃"):
        logout()

# 메인 로직
if not st.session_state.logged_in:
    st.title("🩺 방사선사 AI 튜터 로그인")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("로그인")
        sid = st.text_input("학번")
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if sid == ADMIN_ID and pw == ADMIN_PW:
                st.session_state.logged_in, st.session_state.admin_mode = True, True
                st.session_state.user_info = {"name": "관리자"}
                st.rerun()
            user = authenticate_user(sid, pw)
            if user:
                if user[5] == 'Active':
                    st.session_state.logged_in, st.session_state.user_info = True, {"name": user[1], "id": user[0]}
                    st.rerun()
                else: st.warning("관리자 승인이 필요합니다.")
            else: st.error("정보 불일치")
    with col2:
        st.subheader("회원가입")
        nid, nname, nmail, nphone, npw = st.text_input("학번(ID)"), st.text_input("이름"), st.text_input("이메일"), st.text_input("전화번호"), st.text_input("비번", type="password")
        if st.button("가입 신청"):
            if add_user(nid, nname, nmail, nphone, npw): st.success("신청 완료!")
            else: st.error("이미 존재하는 학번입니다.")

elif st.session_state.admin_mode:
    st.title("🛡️ 관리자 대시보드")
    # 탭을 3개로 늘립니다.
    tab1, tab2, tab3 = st.tabs(["승인 대기 회원", "승인 완료 회원", "시스템 설정 (API)"])
    
    with tab1:
        st.subheader("승인 대기 중인 회원")
        pending = get_pending_users()
        if not pending: st.info("대기 회원 없음")
        else:
            for u in pending:
                c1, c2, c3 = st.columns([2,1,1])
                c1.write(f"👤 {u[1]} ({u[0]})")
                if c2.button("승인", key=f"a_{u[0]}"): update_user_status(u[0], 'Active'); st.rerun()
                if c3.button("거절", key=f"r_{u[0]}"): update_user_status(u[0], 'Rejected'); st.rerun()
                
    with tab2:
        st.subheader("현재 활동 중인 회원")
        # 새로 만든 get_active_users 함수를 사용합니다.
        active = get_active_users() 
        if not active: st.info("승인된 회원 없음")
        else:
            for u in active:
                c1, c2 = st.columns([3,1])
                c1.write(f"✅ {u[1]} ({u[0]}) | {u[2]}")
                # 비활성화 버튼 클릭 시 상태를 다시 'Pending'으로 바꿉니다.
                if c2.button("비활성화", key=f"d_{u[0]}"): 
                    update_user_status(u[0], 'Pending')
                    st.success(f"{u[1]} 학생이 비활성화되었습니다.")
                    st.rerun()
                    
    with tab3:
        st.subheader("공용 API 설정")
        curr = get_setting("GEMINI_API_KEY")
        new_key = st.text_input("Gemini API Key", value=curr if curr else "", type="password")
        if st.button("저장"):
            set_setting("GEMINI_API_KEY", new_key)
            st.success("저장 완료!")


else:
    st.title("🧠 AI 방사선 영상 분석")
    api_key = get_setting("GEMINI_API_KEY")
    if api_key: st.success("공용 AI 모드 활성화")
    else: api_key = st.sidebar.text_input("개인 API Key", type="password")
    
    img_file = st.file_uploader("영상 업로드", type=["jpg", "png"])
    cam_file = st.camera_input("카메라 촬영")
    target = img_file if img_file else cam_file
    if target:
        st.image(target)
        if st.button("황 교수님 분석 요청"):
            if not api_key: st.error("API Key 필요")
            else:
                with st.spinner("분석 중..."):
                    with open("temp.png", "wb") as f: f.write(target.getbuffer())
                    res = analyze_image("temp.png", api_key)
                    st.subheader("분석 결과"); st.markdown(res)
                    os.remove("temp.png")
