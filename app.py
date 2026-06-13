import streamlit as st
import pandas as pd
import time
from datetime import datetime
from vnstock import Vnstock

# 1. Giao diện tràn màn hình tối đa để hiển thị bảng điện tử nhiều cột
st.set_page_config(page_title="Bảng Giá Chứng Khoán Chi Tiết", layout="wide", page_icon="⚡")

if 'db_full_board' not in st.session_state:
    st.session_state.db_full_board = pd.DataFrame()

# --- HÀM QUÉT TOÀN BỘ BƯỚC GIÁ REAL-TIME THEO SÀN ---
def fetch_full_price_board(san_giao_dich):
    try:
        # Bước 1: Gọi nguồn dữ liệu cơ sở khởi tạo
        stock_init = Vnstock().stock(symbol='FPT', source='VCI')
        
        # Bước 2: Tự động lấy danh sách toàn bộ các mã đang niêm yết trên sàn đã chọn
        df_symbols = stock_init.listing.symbols_by_exchange()
        if df_symbols is None or df_symbols.empty:
            return None
            
        # Lọc đúng các mã thuộc sàn người dùng chọn (HOSE, HNX, UPCOM)
        df_filtered_market = df_symbols[df_symbols['exchange'] == san_giao_dich]
        list_tickers = df_filtered_market['symbol'].tolist()
        
        if not list_tickers:
            return None

        # Bước 3: Đổi sang nguồn TCBS để kéo bảng giá chi tiết bước giá giao dịch
        stock_board = Vnstock().stock(symbol='FPT', source='TCBS')
        
        # Truy vấn thông tin bước giá chi tiết (mua/bán/khớp) cho danh sách mã vừa quét
        df_raw_board = stock_board.trading.price_board(symbols=list_tickers)
        
        if df_raw_board is not None and not df_raw_board.empty:
            # Sắp xếp và ánh xạ các cột dữ liệu theo đúng chuẩn bảng điện tử thực tế
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
            
            # Lọc bớt cột thừa, giữ lại đúng cấu hình bảng điện tử
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
st.title("⚡ Bảng Điện Tử Chứng Khoán Trực Tuyến Toàn Sàn")

with st.sidebar:
    st.header("⚙️ Phân Loại Thị Trường")
    # Thay đổi tab sàn linh hoạt HOSE, HNX, UPCOM giống hệt trong ảnh bạn gửi
    selected_market = st.selectbox("Chọn Sàn Giao Dịch:", ["HOSE", "HNX", "UPCOM"])
    st.markdown("---")
    auto_refresh = st.toggle("Tự động quét liên tục (Mỗi 10 giây)")

tab1, tab2 = st.tabs(["📊 Bảng Điện Tử Real-time", "📥 Lưu File Excel"])

if auto_refresh:
    with tab1:
        st.info(f"🔄 Hệ thống đang tự động cập nhật dữ liệu bảng giá sàn {selected_market}...")
        placeholder = st.empty()
        while auto_refresh:
            df_board = fetch_full_price_board(selected_market)
            if df_board is not None:
                with placeholder.container():
                    st.write(f"⏱️ *Dữ liệu toàn sàn cập nhật lúc: {datetime.now().strftime('%H:%M:%S')} - Tổng: {len(df_board)} mã cổ phiếu*")
                    st.dataframe(df_board, use_container_width=True, height=650)
                    st.session_state.db_full_board = df_board
            time.sleep(10)
else:
    with tab1:
        if st.button(f"🚀 Tải bảng điện chi tiết sàn {selected_market}", type="primary"):
            with st.spinner("Đang xử lý và đồng bộ dữ liệu bước giá toàn sàn..."):
                df_board = fetch_full_price_board(selected_market)
                if df_board is not None:
                    st.success(f"Đã tải thành công chi tiết bước giá của {len(df_board)} mã sàn {selected_market}!")
                    st.dataframe(df_board, use_container_width=True, height=650)
                    st.session_state.db_full_board = df_board

with tab2:
    st.subheader("📥 Xuất dữ liệu bảng điện")
    if not st.session_state.db_full_board.empty:
        st.dataframe(st.session_state.db_full_board, use_container_width=True)
        csv_data = st.session_state.db_full_board.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Tải file dữ liệu bảng giá đầy đủ (.CSV)",
            data=csv_data,
            file_name=f"bang_dien_chi_tiet_{selected_market}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.write("Chưa có dữ liệu lịch sử tạm thời. Vui lòng nhấn nút tải dữ liệu ở Tab 1 trước.")
