import streamlit as st
import pandas as pd
import time
from datetime import datetime
# Import thư viện lấy dữ liệu chứng khoán Việt Nam thật
from vnstock3 import Vnstock

# Cấu hình giao diện trang web
st.set_page_config(page_title="Hệ thống Dữ liệu Chứng khoán", layout="wide", page_icon="📊")

# Khởi tạo bộ nhớ tạm để lưu lịch sử quét dữ liệu
if 'db_dotbien_kl' not in st.session_state:
    st.session_state.db_dotbien_kl = pd.DataFrame()

# --- HÀM LẤY DỮ LIỆU THẬT TỪ VNSTOCK ---
def fetch_realtime_data():
    try:
        # Khởi tạo vnstock lấy nguồn dữ liệu từ bảng giá trực tuyến TCBS hoặc SSI
        stock = Vnstock()
        
        # Lấy bảng giá toàn bộ thị trường (real-time)
        # Hàm này trả về toàn bộ các mã đang giao dịch trên sàn kèm khối lượng, mức giá
        df_all = stock.stock_trading.price_board(symbols="")
        
        if df_all is not None and not df_all.empty:
            # Lọc và đổi tên cột cho dễ nhìn (tùy thuộc vào cấu trúc trả về của vnstock3)
            # Thông thường gồm: Mã CP, Giá khớp, Khối lượng khớp, % Thay đổi
            df_clean = df_all[['symbol', 'price', 'volume', 'pc_change']].copy()
            df_clean.columns = ['Mã CP', 'Giá Hiện Tại', 'Khối Lượng Khớp', 'Tăng/Giảm (%)']
            df_clean['Thời Gian'] = datetime.now().strftime('%H:%M:%S')
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
tab1, tab2 = st.tabs(["⚡ Bảng giá toàn sàn Real-time", "🔥 Nhật ký lưu trữ"])

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
                    
                    # Lưu lại lịch sử vào bộ nhớ tạm
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

# Tab xuất dữ liệu ra file Excel/CSV để bạn sử dụng
with tab2:
    st.subheader("💾 Tải dữ liệu dạng bảng về máy tính")
    if not st.session_state.db_dotbien_kl.empty:
        st.dataframe(st.session_state.db_dotbien_kl, use_container_width=True)
        
        # Nút bấm xuất file Excel/CSV tải về máy giống hệt nút bấm trong VBA cũ
        csv_data = st.session_state.db_dotbien_kl.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Tải toàn bộ dữ liệu này về file Excel (.CSV)",
            data=csv_data,
            file_name=f"du_lieu_toan_san_{datetime.now().strftime('%Y%M%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.write("Chưa có dữ liệu lịch sử. Vui lòng bấm quét dữ liệu ở Tab 1 trước.")
