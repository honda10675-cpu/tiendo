import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Báo Cáo Sửa Chữa Máy Móc", layout="wide")

# Kết nối Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Chưa cấu hình Secrets Supabase trong Streamlit Settings!")
    st.stop()

st.title("BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC")
st.subheader("设备维修进度汇报")

# Form nhập báo cáo
with st.expander("➕ Thêm báo cáo mới / 新建汇报", expanded=True):
    with st.form("repair_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            machine = st.text_input("Tên / Mã Máy (设备名称/编号)*")
            c_vi = st.text_area("Nội Dung Sửa Chữa (Tiếng Việt)*")
            c_zh = st.text_area("Nội Dung Sửa Chữa (Tiếng Trung - 中文)")
        with col2:
            est_time = st.text_input("Thời Gian Dự Kiến Hoàn Thành (预计完成时间)*")
            s_vi = st.text_area("Giải Pháp + Quy Cách Linh Kiện (Tiếng Việt)*")
            s_zh = st.text_area("Giải Pháp + Quy Cách Linh Kiện (Tiếng Trung - 中文)")

        submitted = st.form_submit_button("Lưu Báo Cáo / 保存汇报", use_container_width=True)
        if submitted:
            if not machine or not c_vi or not s_vi or not est_time:
                st.warning("Vui lòng điền đầy đủ các thông tin có dấu *")
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
                st.success("Đã lưu báo cáo thành công!")
                st.rerun()

# Hiển thị danh sách báo cáo
st.write("---")
st.subheader("📋 Danh Sách Báo Cáo Tiến Độ / 进度汇报列表")

res = supabase.table("repair_reports").select("*").order("id", desc=True).execute()
reports = res.data

if not reports:
    st.info("Chưa có dữ liệu báo cáo nào.")
else:
    for row in reports:
        is_done = row.get("status") == "Hoàn thành"
        bg_color = "#d4edda" if is_done else "#ffffff"
        border_color = "#28a745" if is_done else "#cccccc"
        status_text = "✓ ĐÃ HOÀN THÀNH / 已完成" if is_done else "⏳ ĐANG SỬA CHỮA / 维修中"

        st.markdown(f"""
        <div style="background-color: {bg_color}; border: 2px solid {border_color}; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
            <div style="display:flex; justify-content:space-between;">
                <h3 style="margin:0; color:#0056b3;">🔧 Máy: {row['machine_name']}</h3>
                <span style="font-weight:bold; color: {'green' if is_done else 'red'};">{status_text}</span>
            </div>
            <small>⏱ Thời gian bắt đầu báo: {row['created_at'][:16].replace('T', ' ')}</small>
            <hr style="margin:8px 0;">
            <p style="margin:5px 0;"><b>1. Nội dung sửa chữa / 维修内容:</b><br>
            {row['content_vi']}<br>
            <span style="color:#d9534f; font-weight:500;">{row.get('content_zh') or ''}</span></p>
            
            <p style="margin:5px 0;"><b>2. Giải pháp + Quy cách linh kiện / 解决方案+零件规格:</b><br>
            {row['solution_vi']}<br>
            <span style="color:#d9534f; font-weight:500;">{row.get('solution_zh') or ''}</span></p>
            
            <p style="margin:5px 0;"><b>3. Dự kiến hoàn thành / 预计完成时间:</b> {row['estimated_time']}</p>
        </div>
        """, unsafe_allow_html=True)

        col_act1, col_act2 = st.columns([2, 1])
        with col_act1:
            if not is_done:
                pwd = st.text_input("Mật khẩu xác nhận (230):", type="password", key=f"pwd_{row['id']}")
                if st.button("✔ Tích hoàn thành", key=f"done_{row['id']}"):
                    if pwd == "230":
                        supabase.table("repair_reports").update({"status": "Hoàn thành"}).eq("id", row["id"]).execute()
                        st.success("Đã chuyển trạng thái hoàn thành!")
                        st.rerun()
                    else:
                        st.error("Mật khẩu không đúng!")
        with col_act2:
            if st.button("🗑 Xóa báo cáo", key=f"del_{row['id']}"):
                supabase.table("repair_reports").delete().eq("id", row["id"]).execute()
                st.rerun()
