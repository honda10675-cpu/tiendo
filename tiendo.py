import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC", layout="wide")

# Kết nối Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Chưa cấu hình Secrets SUPABASE_URL và SUPABASE_KEY trong Streamlit Settings!")
    st.stop()

# Tùy chỉnh CSS giao diện chuẩn theo ảnh
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1e40af;
        font-weight: bold;
        font-size: 26px;
        margin-bottom: 5px;
    }
    .sub-title {
        text-align: center;
        color: #475569;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .table-header {
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        color: #334155;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    .completed-row {
        background-color: #dcfce7 !important;
        color: #15803d !important;
    }
    .text-zh {
        color: #d97706;
        font-size: 12px;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

# Tiêu đề ứng dụng
st.markdown('<div class="main-title">BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">设备维修进度汇报</div>', unsafe_allow_html=True)

# Quản lý trạng thái sửa dữ liệu
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# Lấy thông tin bản ghi đang sửa (nếu có)
edit_data = {}
if st.session_state.edit_id:
    try:
        res_edit = supabase.table("repair_reports").select("*").eq("id", st.session_state.edit_id).execute()
        if res_edit.data:
            edit_data = res_edit.data[0]
    except Exception:
        pass

# ---------------------------------------------------------
# FORM NHẬP / SỬA BÁO CÁO
# ---------------------------------------------------------
with st.container():
    st.markdown("**Tên Máy / 设备名称:**")
    machine = st.text_input("machine_input", value=edit_data.get("machine_name", ""), placeholder="Nhập tên máy...", label_visibility="collapsed")

    st.markdown("**Nội Dung Sửa Chữa / 维修内容:**")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        c_vi = st.text_area("c_vi_input", value=edit_data.get("content_vi", ""), placeholder="Nhập nội dung hư hỏng, sự cố (Tiếng Việt)...", height=70, label_visibility="collapsed")
    with col_c2:
        c_zh = st.text_area("c_zh_input", value=edit_data.get("content_zh", ""), placeholder="Nhập nội dung (Tiếng Trung - 中文)...", height=70, label_visibility="collapsed")

    st.markdown("**Giải Pháp + Quy Cách Linh Kiện / 解决方案+零件规格:**")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        s_vi = st.text_area("s_vi_input", value=edit_data.get("solution_vi", ""), placeholder="Nhập phương án và quy cách linh kiện (Tiếng Việt)...", height=70, label_visibility="collapsed")
    with col_s2:
        s_zh = st.text_area("s_zh_input", value=edit_data.get("solution_zh", ""), placeholder="Nhập giải pháp (Tiếng Trung - 中文)...", height=70, label_visibility="collapsed")

    st.markdown("**Thời Gian Dự Kiến Hoàn Thành / 预计完成时间:**")
    est_time = st.text_input("est_input", value=edit_data.get("estimated_time", ""), placeholder="Ví dụ: 2 giờ, 17:00 ngày 03/09...", label_visibility="collapsed")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        btn_label = "Cập Nhật Báo Cáo / 更新汇报" if st.session_state.edit_id else "Thêm Báo Cáo / 添加汇报"
        if st.button(btn_label, type="primary", use_container_width=True):
            if not machine or not c_vi or not s_vi or not est_time:
                st.warning("Vui lòng điền đầy đủ các thông tin bắt buộc!")
            else:
                payload = {
                    "machine_name": machine,
                    "content_vi": c_vi,
                    "content_zh": c_zh,
                    "solution_vi": s_vi,
                    "solution_zh": s_zh,
                    "estimated_time": est_time
                }
                if st.session_state.edit_id:
                    supabase.table("repair_reports").update(payload).eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None
                    st.success("Đã cập nhật báo cáo thành công!")
                else:
                    payload["status"] = "Đang sửa"
                    supabase.table("repair_reports").insert(payload).execute()
                    st.success("Đã thêm báo cáo mới thành công!")
                st.rerun()

    with col_b2:
        st.button("Tải Hình Báo Cáo / 下载图片", use_container_width=True)

# ---------------------------------------------------------
# BẢNG TIẾN ĐỘ SỬA CHỮA + CỘT THAO TÁC / 操作
# ---------------------------------------------------------
st.markdown('<div class="table-header">BẢNG TIẾN ĐỘ SỬA CHỮA / 维修进度表</div>', unsafe_allow_html=True)

try:
    res = supabase.table("repair_reports").select("*").order("id", desc=True).execute()
    reports = res.data
except Exception:
    reports = []

if not reports:
    st.info("Chưa có dữ liệu báo cáo nào.")
else:
    # Header Bảng
    h_col1, h_col2, h_col3, h_col4, h_col5, h_col6, h_col7 = st.columns([0.6, 1.2, 1.5, 2.5, 2.5, 1.5, 2.2])
    with h_col1: st.markdown("**STT<br><span style='font-size:11px;'>序号</span>**", unsafe_allow_html=True)
    with h_col2: st.markdown("**Máy<br><span style='font-size:11px;'>设备</span>**", unsafe_allow_html=True)
    with h_col3: st.markdown("**Bắt Đầu<br><span style='font-size:11px;'>开始时间</span>**", unsafe_allow_html=True)
    with h_col4: st.markdown("**Nội Dung<br><span style='font-size:11px;'>内容</span>**", unsafe_allow_html=True)
    with h_col5: st.markdown("**Giải Pháp + Linh Kiện<br><span style='font-size:11px;'>解决方案+规格</span>**", unsafe_allow_html=True)
    with h_col6: st.markdown("**Dự Kiến<br><span style='font-size:11px;'>预计时间</span>**", unsafe_allow_html=True)
    with h_col7: st.markdown("**Thao Tác<br><span style='font-size:11px;'>操作</span>**", unsafe_allow_html=True)

    st.divider()

    for idx, row in enumerate(reports, 1):
        row_id = row.get("id")
        is_done = row.get("status") == "Hoàn thành"
        created_at = row.get("created_at", "")[:16].replace("T", " ")
        
        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.6, 1.2, 1.5, 2.5, 2.5, 1.5, 2.2])
        
        with c1: st.write(f"**{idx}**")
        with c2: st.write(f"**{row.get('machine_name')}**")
        with c3: st.caption(created_at)
        with c4:
            st.write(row.get("content_vi"))
            if row.get("content_zh"): st.markdown(f'<span class="text-zh">{row.get("content_zh")}</span>', unsafe_allow_html=True)
        with c5:
            st.write(row.get("solution_vi"))
            if row.get("solution_zh"): st.markdown(f'<span class="text-zh">{row.get("solution_zh")}</span>', unsafe_allow_html=True)
        with c6:
            st.write(row.get("estimated_time"))
            if is_done:
                st.markdown("🟢 **Đã xong / 已完成**")

        # Cột Thao tác (Sửa, Tích Hoàn Thành, Xóa mật khẩu 230)
        with c7:
            act_col1, act_col2, act_col3 = st.columns(3)
            
            # 1. Nút Sửa
            with act_col1:
                if st.button("✏️", key=f"edit_{row_id}", help="Sửa / 修改"):
                    st.session_state.edit_id = row_id
                    st.rerun()

            # 2. Nút Tích Hoàn Thành / Bôi Xanh
            with act_col2:
                check_icon = "✅" if is_done else "⬜"
                if st.button(check_icon, key=f"done_{row_id}", help="Đánh dấu hoàn thành / 完成"):
                    new_status = "Đang sửa" if is_done else "Hoàn thành"
                    supabase.table("repair_reports").update({"status": new_status}).eq("id", row_id).execute()
                    st.rerun()

            # 3. Nút Xóa (Yêu cầu Mật Khẩu 230)
            with act_col3:
                if st.button("🗑️", key=f"del_{row_id}", help="Xóa / 删除"):
                    st.session_state[f"confirm_del_{row_id}"] = True

            # Khung nhập mật khẩu xác nhận xóa
            if st.session_state.get(f"confirm_del_{row_id}"):
                pwd = st.text_input("Nhập MK (230):", type="password", key=f"pwd_{row_id}")
                col_pass1, col_pass2 = st.columns(2)
                with col_pass1:
                    if st.button("OK", key=f"ok_del_{row_id}"):
                        if pwd == "230":
                            supabase.table("repair_reports").delete().eq("id", row_id).execute()
                            st.session_state.pop(f"confirm_del_{row_id}", None)
                            st.success("Đã xóa báo cáo!")
                            st.rerun()
                        else:
                            st.error("Mật khẩu sai!")
                with col_pass2:
                    if st.button("Hủy", key=f"cancel_del_{row_id}"):
                        st.session_state.pop(f"confirm_del_{row_id}", None)
                        st.rerun()
        st.divider()
