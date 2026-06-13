import streamlit as st
import pandas as pd
import time
from datetime import datetime
from vnstock import Vnstock

# 1. Cấu hình giao diện trang web tràn màn hình rộng để hiển thị bảng điện tử
st.set_page_config(page_title="Bảng Giá Chứng Khoán Chi Tiết", layout="wide", page_icon="⚡")

if 'db_full_board' not in st.session_state:
    st.session_state.db_full_board = pd.DataFrame()

# --- HÀM QUÉT TOÀN BỘ BƯỚC GIÁ REAL-TIME SỬ DỤNG HỆ THỐNG ĐỊNH TUYẾN MỚI ---
def fetch_full_price_board(san_giao_dich):
    try:
        # Sử dụng giao diện hợp nhất Unified UI của Vnstock v4
        # Hệ thống tự động chọn nguồn API tốt nhất đang hoạt động (KBS hoặc VCI) để kéo dữ liệu
        stock_api = Vnstock()
        
        # 1. Lấy danh sách toàn bộ mã chứng khoán theo sàn người dùng chọn
        df_symbols = stock_api.listing.symbols_by_exchange()
        if df_symbols is None or df_symbols.empty:
            return None
            
        df_filtered_market = df_symbols[df_symbols['exchange'] == san_giao_dich]
        list_tickers = df_filtered_market['symbol'].tolist()
        
        if not list_tickers:
            return None

        # 2. Truy xuất bảng giá bước giá (Price board) trực tiếp bằng phương thức Unified
        df_raw_board = stock_api.market.price_board(symbols=list_tickers)
        
        if df_raw_board is not None and not df_raw_board.empty:
            # Sắp xếp các cột chuẩn bảng điện tử thực tế: TC, Trần, Sàn, Giá mua, Khớp lệnh, Giá bán
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
            with st.spinner("Đang xử lý và đồng bộ dữ liệu bước giá toàn sàn tự động..."):
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
