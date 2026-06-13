import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Cấu hình giao diện trang web
st.set_page_config(page_title="Hệ thống Dữ liệu Chứng khoán", layout="wide", page_icon="📊")

# --- 1. KHỞI TẠO BỘ NHỚ TẠM (Thay thế cho các Sheet trong Excel) ---
# Sử dụng st.session_state để giữ lại dữ liệu khi trang web tải lại
if 'db_dotbien_kl' not in st.session_state:
    st.session_state.db_dotbien_kl = pd.DataFrame(columns=['Thời Gian', 'Mã CP', 'Khối Lượng Đột Biến'])

if 'db_overwrite_new' not in st.session_state:
    # Giả lập bảng lưu trữ dữ liệu Sheet11 & Sheet15
    st.session_state.db_overwrite_new = pd.DataFrame(index=range(4, 1802))

# --- 2. LOGIC LẤY DỮ LIỆU (Thay thế cho hàm GetBangGiaTT & VNDirectCTY) ---
def fetch_stock_data(tickers):
    """
    Hàm cào dữ liệu thời gian thực.
    Trong thực tế, bạn sẽ import thư viện vnstock3 hoặc kết nối API tại đây.
    """
    current_time = datetime.now().strftime('%H:%M:%S')
    results = []
    for ticker in tickers:
        # Giả lập dữ liệu bảng giá trả về
        results.append({
            'Thời Gian': current_time,
            'Mã CP': ticker.strip().upper(),
            'Giá Đóng Cửa': 45.5,  # Ví dụ giá mẫu
            'Khối Lượng': 150000,
            'Đột Biến KL (%)': 150.5
        })
    return pd.DataFrame(results)

# --- 3. LOGIC XỬ LÝ DỮ LIỆU ĐỘT BIẾN (Thay thế cho Sub Dotbienkhoiluong) ---
def process_data_logic(new_data, mode):
    # Logic tương đương lưu vào Sheet7 (Thêm dòng mới)
    significant_data = new_data[new_data['Đột Biến KL (%)'] > 100] # Lọc đột biến
    if not significant_data.empty:
        st.session_state.db_dotbien_kl = pd.concat([st.session_state.db_dotbien_kl, significant_data], ignore_index=True)
    
    # Logic tương đương Sheet11 & Sheet15 (Ghi đè hoặc Tạo cột mới)
    col_name = f"Dữ liệu_{datetime.now().strftime('%H%M%S')}"
    if mode == "OVERWRITE" and len(st.session_state.db_overwrite_new.columns) > 0:
        last_col = st.session_state.db_overwrite_new.columns[-1]
        st.session_state.db_overwrite_new[last_col] = 45.5 # Ghi đè giá trị mới vào cột cuối
    elif mode == "NEW" or len(st.session_state.db_overwrite_new.columns) == 0:
        st.session_state.db_overwrite_new[col_name] = 45.5 # Thêm cột mới hoàn toàn

# --- 4. GIAO DIỆN CHÍNH CỦA TRANG WEB ---
st.title("📊 Hệ thống Phân tích & Tải dữ liệu Chứng khoán")
st.caption("Chuyển đổi hoàn hảo từ hệ thống Excel VBA sang nền tảng Điện toán đám mây")

# Thanh điều khiển bên trái (Sidebar)
with st.sidebar:
    st.header("⚙️ Cấu hình hệ thống")
    ticker_input = st.text_area("Nhập danh sách mã cổ phiếu (Cách nhau bằng dấu phẩy):", "FPT, HPG, TCB, VHM")
    mode_option = st.radio("Chế độ lưu trữ dữ liệu (Sheet11/15):", ("NEW", "OVERWRITE"))
    
    st.markdown("---")
    st.write("🔄 **Trạng thái tự động cập nhật:**")
    auto_update = st.toggle("Kích hoạt cập nhật tự động (Mỗi 5 giây)")

list_tickers = [x.strip() for x in ticker_input.split(",")]

# Tạo các Tab hiển thị dữ liệu trực quan giống như các Sheet Excel
tab1, tab2, tab3 = st.tabs(["⚡ Bảng giá trực tuyến", "🔥 Đột biến khối lượng (Sheet 7)", "💾 Kho dữ liệu lịch sử (Sheet 11/15)"])

# Xử lý cập nhật dữ liệu tự động hoặc bằng tay
if auto_update:
    # Vòng lặp cập nhật liên tục (Thay thế cho Application.OnTime của VBA)
    with tab1:
        st.info("🔄 Hệ thống đang tự động cập nhật dữ liệu liên tục...")
        placeholder = st.empty()
        
        while auto_update:
            df_current = fetch_stock_data(list_tickers)
            process_data_logic(df_current, mode_option)
            
            with placeholder.container():
                st.write(f"⏱️ *Cập nhật mới nhất lúc: {datetime.now().strftime('%H:%M:%S')}*")
                st.dataframe(df_current, use_container_width=True)
            
            time.sleep(5) # Tự động chạy lại sau 5 giây
else:
    # Chế độ cập nhật bằng tay (Manual) khi bấm nút (Thay thế cho btnGetData_Manual)
    with tab1:
        if st.button("🚀 Chạy tải dữ liệu (Manual)", type="primary"):
            df_current = fetch_stock_data(list_tickers)
            process_data_logic(df_current, mode_option)
            st.success("Tải dữ liệu thành công!")
            st.dataframe(df_current, use_container_width=True)

# Giao diện hiển thị Tab dữ liệu đột biến (Sheet 7)
with tab2:
    st.subheader("📋 Nhật ký mã chứng khoán đột biến khối lượng")
    st.dataframe(st.session_state.db_dotbien_kl, use_container_width=True)
    
    # Nút bấm xuất dữ liệu ra file Excel/CSV tải về máy tức thì
    if not st.session_state.db_dotbien_kl.empty:
        csv_data = st.session_state.db_dotbien_kl.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Tải dữ liệu đột biến (.CSV)", data=csv_data, file_name="dot_bien_kl.csv", mime="text/csv")

# Giao diện hiển thị Tab kho dữ liệu lịch sử (Sheet 11/15)
with tab3:
    st.subheader("🗄️ Bảng ma trận dữ liệu phân tích nâng cao")
    st.dataframe(st.session_state.db_overwrite_new, use_container_width=True)
