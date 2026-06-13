import streamlit as st
import pandas as pd
import time
from datetime import datetime
# Cú pháp import mới theo tài liệu vnstock3
from vnstock import Vnstock

# Cấu hình giao diện trang web
st.set_page_config(page_title="Hệ thống Dữ liệu Chứng khoán", layout="wide", page_icon="📊")

# Khởi tạo bộ nhớ tạm để lưu lịch sử quét dữ liệu
if 'db_dotbien_kl' not in st.session_state:
    st.session_state.db_dotbien_kl = pd.DataFrame()

# --- HÀM LẤY DỮ LIỆU THẬT SỬ DỤNG CÚ PHÁP VNSTOCK3 CẬP NHẬT ---
def fetch_realtime_data():
    try:
        # Khởi tạo đối tượng theo chuẩn mới nhất của thư viện vnstock3
        # Để trống symbol để mặc định quét danh sách bảng giá tổng hợp
        stock = Vnstock().stock(symbol='FPT', source='VCI')
        
        # Gọi hàm lấy dữ liệu danh sách niêm yết (Toàn bộ mã trên sàn)
        df_all = stock.listing.all_symbols()
        
        if df_all is not None and not df_all.empty:
            # Tạo bảng hiển thị đầy đủ và làm sạch dữ liệu
            df_clean = df_all.copy()
            df_clean['Thời Gian Cập Nhật'] = datetime.now().strftime('%H:%M:%S')
            return df_clean
        else:
            return None
    except Exception as e:
        st.error(f"Lỗi kết nối nguồn dữ liệu: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Hệ thống Phân tích & Tải dữ liệu Toàn sàn Chứng khoán")

# Thanh điều khiển bên trái
with st.sidebar:
    st.header("⚙️ Cấu hình hệ thống")
    st.write("Hệ thống đang tự động cấu hình quét toàn bộ mã trên sàn (HOSE, HNX, UPCOM).")
    st.markdown("---")
    auto_update = st.toggle("Kích hoạt tự động quét liên tục (Mỗi 10 giây)")

# Các Tab hiển thị
tab1, tab2 = st.tabs(["⚡ Bảng giá toàn sàn Real-time", "💾 Nhật ký lưu trữ & Xuất file"])

if auto_update:
    with tab1:
        st.info("🔄 Hệ thống đang tự động quét toàn bộ thị trường...")
        placeholder = st.empty()
        
        while auto_update:
            df_real = fetch_realtime_data()
            if df_real is not None:
                with placeholder.container():
                    st.write(f"⏱️ *Cập nhật toàn sàn lúc: {datetime.now().strftime('%H:%M:%S')} - Tổng số mã: {len(df_real)}*")
                    st.dataframe(df_real, use_container_width=True, height=500)
                    st.session_state.db_dotbien_kl = df_real
            time.sleep(10)
else:
    with tab1:
        if st.button("🚀 Bấm để quét toàn bộ mã trên sàn", type="primary"):
            with st.spinner("Đang tải dữ liệu toàn sàn..."):
                df_real = fetch_realtime_data()
                if df_real is not None:
                    st.success(f"Tải thành công dữ liệu của {len(df_real)} mã chứng khoán!")
                    st.dataframe(df_real, use_container_width=True, height=500)
                    st.session_state.db_dotbien_kl = df_real

# Tab xuất dữ liệu ra file
with tab2:
    st.subheader("💾 Tải dữ liệu toàn bộ mã về máy tính")
    if not st.session_state.db_dotbien_kl.empty:
        st.dataframe(st.session_state.db_dotbien_kl, use_container_width=True)
        
        csv_data = st.session_state.db_dotbien_kl.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Tải toàn bộ danh sách mã về file Excel (.CSV)",
            data=csv_data,
            file_name=f"danh_sach_toan_san_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.write("Chưa có dữ liệu. Vui lòng bấm quét dữ liệu ở Tab 1 trước.")
