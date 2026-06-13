import streamlit as st
import pandas as pd
import time
from datetime import datetime
from vnstock import Vnstock

# 1. Cấu hình giao diện trang web dạng tràn màn hình để hiển thị bảng giá rộng
st.set_page_config(page_title="Bảng Giá Chứng Khoán Trực Tuyến", layout="wide", page_icon="📈")

if 'db_price_board' not in st.session_state:
    st.session_state.db_price_board = pd.DataFrame()

# --- HÀM LẤY BẢNG GIÁ REAL-TIME CHI TIẾT ---
def fetch_price_board(san_giao_dich):
    try:
        # Khởi tạo đối tượng lấy dữ liệu từ nguồn bảng giá TCBS hoặc SSI
        stock = Vnstock().stock(symbol='FPT', source='TCBS')
        
        # Gọi hàm lấy toàn bộ bảng giá của một sàn (HOSE, HNX, hoặc UPCOM)
        # Hàm này trả về chi tiết giá Khớp lệnh, Mua, Bán, Trần, Sàn, TC...
        df = stock.trading.price_board(market=san_giao_dich)
        
        if df is not None and not df.empty:
            # Chỉ định chọn và sắp xếp các cột theo thứ tự giống bảng giá thực tế
            # Lưu ý: Tên cột có thể thay đổi nhẹ tùy theo phiên bản, dưới đây là các cột tiêu chuẩn:
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
            
            # Lọc các cột tồn tại trong dữ liệu trả về để tránh lỗi
            available_cols = [col for col in columns_mapping.keys() if col in df.columns]
            df_filtered = df[available_cols].copy()
            df_filtered.rename(columns={col: columns_mapping[col] for col in available_cols}, inplace=True)
            
            df_filtered['Cập Nhật'] = datetime.now().strftime('%H:%M:%S')
            return df_filtered
        else:
            return None
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu bảng giá: {e}")
        return None

# --- GIAO DIỆN WEB ---
st.title("⚡ Hệ Thống Bảng Giá Chứng Khoán Trực Tuyến")

with st.sidebar:
    st.header("⚙️ Tùy chọn Sàn")
    # Cho phép bạn chọn xem bảng giá của từng sàn giống như các tab HOSE, HNX trên ảnh
    selected_market = st.selectbox("Chọn sàn giao dịch:", ["HOSE", "HNX", "UPCOM"])
    st.markdown("---")
    auto_update = st.toggle("Tự động làm mới bảng giá (10 giây)")

tab1, tab2 = st.tabs(["📊 Bảng Giá Trực Tuyến", "📥 Xuất Dữ Liệu Excel"])

if auto_update:
    with tab1:
        st.info(f"🔄 Đang tự động cập nhật bảng giá sàn {selected_market} liên tục...")
        placeholder = st.empty()
        while auto_update:
            df_board = fetch_price_board(selected_market)
            if df_board is not None:
                with placeholder.container():
                    st.write(f"⏱️ *Dữ liệu cập nhật lúc: {datetime.now().strftime('%H:%M:%S')} - Tổng số: {len(df_board)} mã*")
                    st.dataframe(df_board, use_container_width=True, height=600)
                    st.session_state.db_price_board = df_board
            time.sleep(10)
else:
    with tab1:
        if st.button(f"🚀 Tải bảng giá sàn {selected_market}", type="primary"):
            with st.spinner("Đang kết nối đến bảng giá trực tuyến..."):
                df_board = fetch_price_board(selected_market)
                if df_board is not None:
                    st.success(f"Đã tải xong bảng giá sàn {selected_market}!")
                    st.dataframe(df_board, use_container_width=True, height=600)
                    st.session_state.db_price_board = df_board

with tab2:
    st.subheader("📥 Tải bảng giá hiện tại về máy tính")
    if not st.session_state.db_price_board.empty:
        st.dataframe(st.session_state.db_price_board, use_container_width=True)
        csv_data = st.session_state.db_price_board.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Xuất bảng giá này ra file Excel (.CSV)",
            data=csv_data,
            file_name=f"bang_gia_{selected_market}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.write("Chưa có dữ liệu lưu trữ tạm thời. Hãy bấm nút tải ở Tab 1 trước.")
