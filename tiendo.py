import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="Báo Cáo Tiến Độ Sửa Chữa Máy Móc", layout="centered")

# Kết nối Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Chưa cấu hình Secrets Supabase trong Streamlit Settings!")
    st.stop()

# CSS chuẩn hóa bảng hiển thị
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    .table-title {
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        color: #334155;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        background-color: #ffffff;
    }
    .custom-table th {
        background-color: #f1f5f9;
        color: #1e293b;
        border: 1px solid #cbd5e1;
        padding: 8px 4px;
        text-align: center;
        font-weight: bold;
        line-height: 1.3;
    }
    .custom-table td {
        border: 1px solid #cbd5e1;
        padding: 8px 6px;
        text-align: center;
        vertical-align: middle;
        line-height: 1.3;
    }
    .text-zh {
        color: #d97706;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# KHUNG NHẬP BÁO CÁO (FORM)
# ---------------------------------------------------------
st.text_input("Tên / Mã Máy (设备名称/编号)", key="input_machine", placeholder="Nhập tên máy...")

st.markdown("**Nội Dung Sửa Chữa / 维修内容:**")
c_vi = st.text_area("", key="input_c_vi", placeholder="Nhập nội dung hư hỏng, sự cố...", height=80, label_visibility="collapsed")
c_zh = st.text_input("Nội dung (Tiếng Trung - 中文)", key="input_c_zh", placeholder="Tự động hoặc nhập tiếng Trung...")

st.markdown("**Giải Pháp + Quy Cách Linh Kiện / 解决方案+零件规格:**")
s_vi = st.text_area("", key="input_s_vi", placeholder="Nhập phương án và quy cách linh kiện...", height=80, label_visibility="collapsed")
s_zh = st.text_input("Giải pháp (Tiếng Trung - 中文)", key="input_s_zh", placeholder="Tự động hoặc nhập tiếng Trung...")

st.markdown("**Thời Gian Dự Kiến Hoàn Thành / 预计完成时间:**")
est_time = st.text_input("", key="input_est", placeholder="Ví dụ: 2 giờ, 17:00 ngày 03/09...", label_visibility="collapsed")

col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("Thêm Báo Cáo / 添加汇报", type="primary", use_container_width=True):
        machine = st.session_state.get("input_machine")
        if not machine or not c_vi or not s_vi or not est_time:
            st.warning("Vui lòng điền đầy đủ các thông tin!")
        else:
            data = {
                "machine_name": machine,
                "content_vi": c_vi,
                "content_zh": c_zh,
                "solution_vi": s_vi,
                "solution_zh": s_zh,
                "estimated_time": est_time,
                "status": "Đang sửa"
            }
            supabase.table("repair_reports").insert(data).execute()
            st.success("Đã thêm báo cáo thành công!")
            st.rerun()

with col_btn2:
    st.button("Tải Hình Báo Cáo / 下载图片", use_container_width=True)

# ---------------------------------------------------------
# BẢNG TIẾN ĐỘ SỬA CHỮA (XUẤT CHUẨN HTML)
# ---------------------------------------------------------
st.markdown('<div class="table-title">BẢNG TIẾN ĐỘ SỬA CHỮA / 维修进度表</div>', unsafe_allow_html=True)

try:
    res = supabase.table("repair_reports").select("*").order("id", desc=True).execute()
    reports = res.data
except Exception:
    reports = []

if not reports:
    st.info("Chưa có dữ liệu báo cáo nào.")
else:
    # Mở đầu bảng HTML
    table_html = """
    <table class="custom-table">
        <thead>
            <tr>
                <th style="width: 8%;">STT<br><span style="font-weight:normal;">序号</span></th>
                <th style="width: 12%;">Máy<br><span style="font-weight:normal;">设备</span></th>
                <th style="width: 15%;">Thời Gian Bắt Đầu<br><span style="font-weight:normal;">开始时间</span></th>
                <th style="width: 25%;">Nội Dung<br><span style="font-weight:normal;">内容</span></th>
                <th style="width: 25%;">Giải Pháp + Linh Kiện<br><span style="font-weight:normal;">解决方案+规格</span></th>
                <th style="width: 15%;">Thời Gian Dự Kiến<br><span style="font-weight:normal;">预计时间</span></th>
            </tr>
        </thead>
        <tbody>
    """
    
    rows_html = ""
    for idx, row in enumerate(reports, 1):
        created_at = row.get("created_at", "")[:16].replace("T", " ")
        c_zh_text = f'<br><span class="text-zh">{row.get("content_zh")}</span>' if row.get("content_zh") else ""
        s_zh_text = f'<br><span class="text-zh">{row.get("solution_zh")}</span>' if row.get("solution_zh") else ""
        
        rows_html += f"""
        <tr>
            <td><b>{idx}</b></td>
            <td><b>{row.get('machine_name')}</b></td>
            <td style="font-size: 11px;">{created_at}</td>
            <td style="text-align: left;">{row.get('content_vi')}{c_zh_text}</td>
            <td style="text-align: left;">{row.get('solution_vi')}{s_zh_text}</td>
            <td>{row.get('estimated_time')}</td>
        </tr>
        """
        
    # Đóng bảng HTML
    table_html += rows_html + "</tbody></table>"
    
    # Hiển thị duy nhất một lần
    st.markdown(table_html, unsafe_allow_html=True)
