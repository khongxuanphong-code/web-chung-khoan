import streamlit as st
import pandas as pd
import time
from datetime import datetime
from vnstock import Vnstock

# 1. Cấu hình giao diện trang web tràn màn hình rộng để hiển thị bảng điện tử
st.set_page_config(page_title="Bảng Giá Chứng Khoán Chi Tiết", layout="wide", page_icon="⚡")

if 'db_full_board' not in st.session_state:
    st.session_state.db_full_board = pd.DataFrame()

# --- HÀM QUÉT BƯỚC GIÁ REAL-TIME THEO DANH SÁCH MÃ CHỌN LỌC ---
def fetch_custom_price_board(ticker_list):
    try:
        # Khởi tạo nguồn dữ liệu từ Vietcap (VCI) cực kỳ ổn định
        stock = Vnstock().stock(symbol='FPT', source='VCI')
        
        # Gọi hàm lấy bảng giá chi tiết cho danh sách mã cụ thể (Giải pháp tránh RetryError)
        df_raw_board = stock.trading.price_board(symbols=ticker_list)
        
        if df_raw_board is not None and not df_raw_board.empty:
            # Sắp xếp các cột chuẩn bảng điện tử thực tế: Mã CK, TC, Trần, Sàn, Giá mua, Khớp lệnh, Giá bán
            columns_mapping = {
                'symbol': 'Mã CK',
                're': 'TC',
                'ce': 'Trần',
                'fl': 'Sàn',
                'total_volume': 'Tổng KL',
                'bid_price_3': 'Giá Mua 3', 'bid_volume_3': 'KL Mua 3',
                'bid_price_2': 'Giá Mua 2', 'bid_volume_2': 'KL Mua 2',
                'bid_price_1': 'Giá Mua 1', 'bid_volume_1': 'KL Mua 1',
                'match_price': 'Giá Khớp', 'match_volume': 'KL Khớp', 'match_change': '+/-',
                'ask_price_1': 'Giá Bán 1', 'ask_volume_1': 'KL Bán 1',
                'ask_price_2': 'Giá Bán 2', 'ask_volume_2': 'KL Bán 2',
                'ask_price_3': 'Giá Bán 3', 'ask_volume_3': 'KL Bán 3',
                'high': 'Cao', 'low': 'Thấp'
            }
            
            available_cols = [col for col in columns_mapping.keys() if col in df_raw_board.columns]
            df_final = df_raw_board[available_cols].copy()
            df_final.rename(columns={col: columns_mapping[col] for col in available_cols}, inplace=True)
            
            # Chèn thêm cột thời gian cập nhật vào đầu bảng
            df_final.insert(0, 'Thời Gian', datetime.now().strftime('%H:%M:%S'))
            return df_final
        else:
            return None
    except Exception as e:
        st.error(f"Lỗi hệ thống khi tải bảng giá: {e}")
        return None

# --- GIAO DIỆN CHÍNH CỦA TRANG WEB ---
st.title("⚡ Bảng Điện Tử Chứng Khoán Trực Tuyến")

with st.sidebar:
    st.header("⚙️ Danh Mục Theo Dõi")
    # Cho phép người dùng tự điền các mã muốn xem, mặc định sẵn danh sách các mã lớn để hiển thị luôn
    user_tickers = st.text_area(
        "Nhập các mã cổ phiếu bạn muốn theo dõi (Cách nhau bởi dấu phẩy):",
        value="FPT, HPG, TCB, VHM, SSI, VND, VNM, MSN, VIC, VRE, STB, MBB"
    )
    
    # Chuyển đổi chuỗi nhập thành danh sách List Python
    list_tickers = [ticker.strip().upper() for ticker in user_tickers.split(",") if ticker.strip()]
    
    st.markdown("---")
    auto_refresh = st.toggle("Tự động làm mới bảng giá (Mỗi 10 giây)")

tab1, tab2 = st.tabs(["📊 Bảng Điện Tử Real-time", "📥 Lưu File Excel"])

if auto_refresh:
    with tab1:
        st.info("🔄 Hệ thống đang tự động cập nhật bảng giá liên tục...")
        placeholder = st.empty()
        while auto_refresh:
            if list_tickers:
                df_board = fetch_custom_price_board(list_tickers)
                if df_board is not None:
                    with placeholder.container():
                        st.write(f"⏱️ *Dữ liệu cập nhật lúc: {datetime.now().strftime('%H:%M:%S')} - Đang theo dõi: {len(df_board)} mã*")
                        st.dataframe(df_board, use_container_width=True, height=500)
                        st.session_state.db_full_board = df_board
            else:
                st.warning("Vui lòng nhập ít nhất 1 mã cổ phiếu vào thanh bên trái.")
            time.sleep(10)
else:
    with tab1:
        if st.button("🚀 Tải bảng điện chi tiết", type="primary"):
            if list_tickers:
                with st.spinner("Đang đồng bộ dữ liệu bước giá từ hệ thống..."):
                    df_board = fetch_custom_price_board(list_tickers)
                    if df_board is not None:
                        st.success(f"Đã tải thành công chi tiết bước giá của danh mục theo dõi!")
                        st.dataframe(df_board, use_container_width=True, height=500)
                        st.session_state.db_full_board = df_board
            else:
                st.warning("Vui lòng nhập ít nhất 1 mã cổ phiếu vào thanh bên trái.")

with tab2:
    st.subheader("📥 Xuất dữ liệu bảng điện")
    if not st.session_state.db_full_board.empty:
        st.dataframe(st.session_state.db_full_board, use_container_width=True)
        csv_data = st.session_state.db_full_board.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Tải file dữ liệu danh mục theo dõi (.CSV)",
            data=csv_data,
            file_name=f"danh_muc_theo_doi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.write("Chưa có dữ liệu lịch sử tạm thời. Vui lòng nhấn nút tải dữ liệu ở Tab 1 trước.")
