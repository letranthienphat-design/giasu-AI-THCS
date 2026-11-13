import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import os
import time

# 1. CẤU HÌNH TRANG WEB
st.set_page_config(
    page_title="Gia Sư AI Gợi Mở - THCS",
    page_icon="🎓",
    layout="wide"
)

# 2. KHỞI TẠO BỘ NHỚ TẠM (SESSION STATE)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0

DAILY_LIMIT = 50  # Hạn mức miễn phí mỗi ngày

# 3. LẤY API KEY (Ưu tiên lấy từ Streamlit Secrets)
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

# 4. GIAO DIỆN THANH BÊN TRÁI (SIDEBAR)
with st.sidebar:
    st.header("🎓 Gia Sư AI THCS")
    st.caption("Phương pháp Socratic: Gợi mở tư duy, không giải hộ bài tập.")
    
    if not api_key:
        api_key = st.text_input("🔑 Nhập Gemini API Key:", type="password")
    
    st.divider()
    
    mon_hoc = st.selectbox(
        "📚 Chọn môn học:",
        ["Toán học", "Tin học (Python/Scratch)", "Vật lý", "Hóa học", "Ngữ văn", "Tiếng Anh"]
    )
    
    che_do = st.selectbox(
        "🎯 Chế độ hỗ trợ:",
        [
            "Gợi ý từng bước (Không đưa đáp án)",
            "Kiểm tra lỗi sai bài làm của em",
            "Giải thích lý thuyết dễ hiểu"
        ]
    )
    
    st.divider()
    
    st.markdown("**👤 Chế độ Khách (Dùng thử)**")
    st.progress(min(st.session_state.usage_count / DAILY_LIMIT, 1.0))
    st.caption(f"Đã dùng: **{st.session_state.usage_count} / {DAILY_LIMIT}** lượt hôm nay")
    
    if st.button("🗑️ Xóa cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 5. GIAO DIỆN CHÍNH (MAIN SCREEN)
st.title("⚡ Gia Sư AI - Đồng Hành Tư Duy")
st.info(f"📌 Đang học môn: **{mon_hoc}** | Chế độ: **{che_do}** | Mô hình: `Gemini AI`")

if st.session_state.usage_count >= DAILY_LIMIT:
    st.warning(f"⚠️ Bạn đã hết {DAILY_LIMIT} lượt hỏi miễn phí trong ngày! Vui lòng quay lại vào ngày mai.")

uploaded_file = st.file_uploader("📸 Chụp ảnh đề bài hoặc bài làm của em (nếu có):", type=["png", "jpg", "jpeg"])
image_data = None
if uploaded_file is not None:
    image_data = Image.open(uploaded_file)
    st.image(image_data, caption="Ảnh bài tập đã tải lên", width=300)

st.divider()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. XỬ LÝ KHI NGƯỜI DÙNG NHẬP CÂU HỎI
prompt = st.chat_input("Nhập đề bài hoặc phần em đang bí vào đây...")

if prompt:
    if not api_key:
        st.error("Vui lòng nhập Gemini API Key ở thanh bên trái (hoặc cài đặt trong Streamlit Secrets) để bắt đầu!")
        st.stop()
        
    if st.session_state.usage_count >= DAILY_LIMIT:
        st.error("Bạn đã đạt giới hạn lượt dùng miễn phí hôm nay!")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    system_instruction = f"""
    Bạn là một gia sư AI thân thiện, kiên nhẫn dành riêng cho học sinh THCS (lớp 6 đến lớp 9) tại Việt Nam.
    Môn học hiện tại: {mon_hoc}.
    Chế độ hỗ trợ: {che_do}.

    QUY TẮC BẮT BUỘC PHẢI TUÂN THỦ:
    1. Nếu ở chế độ "Gợi ý từng bước (Không đưa đáp án)": TUYỆT ĐỐI KHÔNG giải trọn vẹn bài tập hay tiết lộ đáp án cuối cùng ngay từ đầu. Hãy chia bài toán/vấn đề thành các bước nhỏ. Mỗi lần trả lời chỉ nhắc lại kiến thức/công thức nền tảng cho bước tiếp theo và đặt 1 câu hỏi gợi mở để học sinh tự tính toán hoặc tự viết code.
    2. Nếu học sinh nài nỉ xin đáp án, hãy từ chối khéo léo, động viên và đưa ra một ví dụ tương tự đơn giản hơn để học sinh tự áp dụng.
    3. Nếu ở chế độ "Kiểm tra lỗi sai bài làm của em": Chỉ ra chính xác dòng/bước nào đang bị sai, giải thích vì sao sai và gợi ý cách sửa, không làm thay toàn bộ.
    4. Trình bày rõ ràng, ngắn gọn, dùng ngôn ngữ gần gũi với học sinh cấp 2. Sử dụng công thức toán học chuẩn LaTeX ($...$) nếu cần.
    """

    with st.chat_message("assistant"):
        with st.spinner("Gia sư đang phân tích đề bài..."):
            try:
                client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(timeout=20000)
                )
                
                # Tự động lấy danh sách các mô hình Gemini hợp lệ từ chính API Key của bạn
                available_models = []
                for m in client.models.list():
                    name = m.name.replace("models/", "")
                    if "gemini" in name and "flash" in name and "embedding" not in name and "tts" not in name and "image" not in name:
                        available_models.append(name)
                
                # Ưu tiên bản mới nhất trước, nếu không tìm thấy thì dùng danh sách mặc định
                available_models.sort(reverse=True)
                if not available_models:
                    available_models = ["gemini-2.5-flash", "gemini-2.0-flash"]

                contents = []
                for m in st.session_state.messages[:-1]:
                    role_gemini = "user" if m["role"] == "user" else "model"
                    contents.append(types.Content(role=role_gemini, parts=[types.Part.from_text(text=m["content"])]))
                
                current_parts = [types.Part.from_text(text=prompt)]
                if image_data is not None:
                    current_parts.append(image_data)
                contents.append(types.Content(role="user", parts=current_parts))

                response = None
                last_error = None

                # Thử lần lượt các mô hình thực tế có trong tài khoản
                for current_model in available_models[:3]:
                    try:
                        response = client.models.generate_content(
                            model=current_model,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.4,
                            )
                        )
                        if response and response.text:
                            break
                    except Exception as err:
                        last_error = err
                        time.sleep(2)
                        continue

                if response is None or not response.text:
                    raise last_error
                
                reply_text = response.text
                st.markdown(reply_text)
                
                st.session_state.messages.append({"role": "assistant", "content": reply_text})
                st.session_state.usage_count += 1
                
            except Exception as e:
                st.error(f"Có lỗi xảy ra khi kết nối AI: {e}")
