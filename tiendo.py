import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
import streamlit as st
from supabase import Client, create_client

st.set_page_config(page_title="BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC", layout="wide")

# Chuyển đổi thời gian UTC từ Supabase sang múi giờ Việt Nam (+7)
def convert_utc_to_vn(dt_str):
    if not dt_str:
        tz_vn = timezone(timedelta(hours=7))
        return datetime.now(tz_vn).strftime("%Y-%m-%d %H:%M")
    try:
        clean_str = dt_str.replace("T", " ")[:19]
        dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
        dt_vn = dt + timedelta(hours=7)
        return dt_vn.strftime("%Y-%m-%d %H:%M")
    except Exception:
        try:
            clean_str = dt_str.replace("T", " ")[:16]
            dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M")
            dt_vn = dt + timedelta(hours=7)
            return dt_vn.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return dt_str[:16] if len(dt_str) >= 16 else dt_str

# Hàm dịch đa tầng Việt -> Trung
def translate_to_zh(text):
    if not text or not str(text).strip():
        return ""
    text_clean = str(text).strip()
    
    try:
        url_mm = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text_clean)}&langpair=vi|zh-CN"
        req = urllib.request.Request(url_mm, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=4)
        data = json.loads(res.read().decode('utf-8'))
        translated = data.get("responseData", {}).get("translatedText", "")
        if translated and translated.lower() != text_clean.lower():
            return translated
    except Exception:
        pass

    try:
        url_gt = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=vi&tl=zh-CN&dt=t&q={urllib.parse.quote(text_clean)}"
        req = urllib.request.Request(url_gt, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        res = urllib.request.urlopen(req, timeout=4)
        data = json.loads(res.read().decode('utf-8'))
        translated = "".join([item[0] for item in data[0] if item[0]])
        if translated:
            return translated
    except Exception:
        pass

    return ""

# Kết nối Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Chưa cấu hình Secrets SUPABASE_URL và SUPABASE_KEY!")
    st.stop()

# CSS giao diện chuẩn Table hàng ngang cho Điện thoại
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1e40af;
        font-weight: bold;
        font-size: 22px;
        margin-bottom: 5px;
    }
    .sub-title {
        text-align: center;
        color: #475569;
        font-size: 13px;
        margin-bottom: 20px;
    }
    
    /* Ép bảng hiển thị dạng cuộn ngang trên điện thoại */
    .table-container {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin-top: 15px;
    }
    .custom-table {
        width: 100%;
        min-width: 800px; /* Đảm bảo luôn giữ kích thước hàng ngang */
        border-collapse: collapse;
        background-color: #ffffff;
    }
    .custom-table th {
        background-color: #f1f5f9;
        color: #1e293b;
        font-weight: bold;
        text-align: center;
        padding: 10px 8px;
        border-bottom: 2px solid #cbd5e1;
        font-size: 13px;
    }
    .custom-table td {
        padding: 10px 8px;
        border-bottom: 1px solid #e2e8f0;
        vertical-align: middle;
        font-size: 13px;
    }
    .text-zh {
        color: #d97706;
        font-size: 12px;
        font-weight: 500;
        display: block;
        margin-top: 3px;
    }
    .status-done {
        color: #15803d;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">设备维修进度汇报</div>', unsafe_allow_html=True)

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

edit_data = {}
if st.session_state.edit_id:
    try:
        res_edit = supabase.table("repair_reports").select("*").eq("id", st.session_state.edit_id).execute()
        if res_edit.data:
            edit_data = res_edit.data[0]
    except Exception:
        pass

# FORM NHẬP BÁO CÁO
with st.container():
    st.markdown("**Tên Máy / 设备名称:**")
    machine = st.text_input("machine_input", value=edit_data.get("machine_name", ""), placeholder="Nhập tên máy...", label_visibility="collapsed")

    st.markdown("**Nội Dung Sửa Chữa / 维修内容:**")
    c_vi = st.text_area("c_vi_input", value=edit_data.get("content_vi", ""), placeholder="Nhập nội dung hư hỏng...", height=70, label_visibility="collapsed")

    st.markdown("**Giải Pháp + Quy Cách Linh Kiện / 解决方案+零件规格:**")
    s_vi = st.text_area("s_vi_input", value=edit_data.get("solution_vi", edit_data.get("solution", "")), placeholder="Nhập phương án...", height=70, label_visibility="collapsed")

    st.markdown("**Thời Gian Dự Kiến Hoàn Thành / 预计完成时间:**")
    est_time = st.text_input("est_input", value=edit_data.get("estimated_time", ""), placeholder="Ví dụ: 2 giờ, 17:00 ngày 03/09...", label_visibility="collapsed")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        btn_label = "Thêm Báo Cáo / 添加汇报" if not st.session_state.edit_id else "Cập Nhật Báo Cáo / 更新汇报"
        if st.button(btn_label, type="primary", use_container_width=True):
            if not machine or not c_vi or not est_time:
                st.warning("Vui lòng điền đầy đủ thông tin!")
            else:
                c_zh = translate_to_zh(c_vi)
                s_zh = translate_to_zh(s_vi) if s_vi else ""

                payload_full = {
                    "machine_name": machine,
                    "content_vi": c_vi,
                    "content_zh": c_zh,
                    "solution_vi": s_vi,
                    "solution_zh": s_zh,
                    "estimated_time": est_time
                }

                payload_legacy = {
                    "machine_name": machine,
                    "content_vi": c_vi,
                    "content_zh": c_zh,
                    "solution": s_vi,
                    "estimated_time": est_time
                }

                saved = False
                try:
                    if st.session_state.edit_id:
                        supabase.table("repair_reports").update(payload_full).eq("id", st.session_state.edit_id).execute()
                    else:
                        payload_full["status"] = "Đang sửa"
                        supabase.table("repair_reports").insert(payload_full).execute()
                    saved = True
                except Exception:
                    pass

                if not saved:
                    try:
                        if st.session_state.edit_id:
                            supabase.table("repair_reports").update(payload_legacy).eq("id", st.session_state.edit_id).execute()
                        else:
                            payload_legacy["status"] = "Đang sửa"
                            supabase.table("repair_reports").insert(payload_legacy).execute()
                        saved = True
                    except Exception as e:
                        st.error(f"Lỗi Supabase: {e}")
                        st.stop()

                st.session_state.edit_id = None
                st.success("Lưu báo cáo thành công!")
                st.rerun()

    with col_b2:
        st.button("Tải Báo Cáo / 下载图片", use_container_width=True)

# BẢNG TIẾN ĐỘ SỬA CHỮA HÀNG NGANG CHUẨN ĐIỆN THOẠI
st.markdown("<h4 style='text-align: center; margin-top: 20px;'>BẢNG TIẾN ĐỘ SỬA CHỮA / 维修进度表</h4>", unsafe_allow_html=True)

try:
    res = supabase.table("repair_reports").select("*").order("id", desc=True).execute()
    reports = res.data
except Exception:
    reports = []

if not reports:
    st.info("Chưa có dữ liệu báo cáo nào.")
else:
    # Render bảng HTML cuộn ngang cố định
    html_table = """
    <div class="table-container">
        <table class="custom-table">
            <thead>
                <tr>
                    <th style="width: 5%;">STT<br><small>序号</small></th>
                    <th style="width: 10%;">Máy<br><small>设备</small></th>
                    <th style="width: 15%;">Thời Gian Bắt Đầu<br><small>开始时间</small></th>
                    <th style="width: 25%;">Nội Dung<br><small>内容</small></th>
                    <th style="width: 25%;">Giải Pháp + Linh Kiện<br><small>解决方案+规格</small></th>
                    <th style="width: 12%;">Thời Gian Dự Kiến<br><small>预计时间</small></th>
                    <th style="width: 8%;">Trạng Thái<br><small>状态</small></th>
                </tr>
            </thead>
            <tbody>
    """

    for idx, row in enumerate(reports, 1):
        is_done = row.get("status") == "Hoàn thành"
        time_display = convert_utc_to_vn(row.get("created_at", ""))

        c_vi_val = row.get("content_vi", "")
        c_zh_val = row.get("content_zh") if row.get("content_zh") else translate_to_zh(c_vi_val)

        s_vi_val = row.get("solution_vi") if row.get("solution_vi") else row.get("solution", "")
        s_zh_val = row.get("solution_zh") if row.get("solution_zh") else translate_to_zh(s_vi_val)

        status_html = '<span class="status-done">🟢 Đã xong<br><small>已完成</small></span>' if is_done else '🟡 Đang sửa<br><small>维修中</small>'

        html_table += f"""
            <tr>
                <td style="text-align: center;"><b>{idx}</b></td>
                <td style="text-align: center;"><b>{row.get('machine_name', '')}</b></td>
                <td style="text-align: center; color: #64748b; font-size: 11px;">{time_display}</td>
                <td>{c_vi_val}<span class="text-zh">{c_zh_val}</span></td>
                <td>{s_vi_val}<span class="text-zh">{s_zh_val}</span></td>
                <td style="text-align: center;">{row.get('estimated_time', '')}</td>
                <td style="text-align: center;">{status_html}</td>
            </tr>
        """

    html_table += """
            </tbody>
        </table>
    </div>
    """
    st.markdown(html_table, unsafe_allow_html=True)

    # Khung thao tác sửa / xóa / hoàn thành gọn gàng bên dưới
    st.divider()
    st.markdown("**Quản lý bản ghi / 操作:**")
    
    col_sel, col_act1, col_act2, col_act3 = st.columns([3, 1, 1, 1])
    with col_sel:
        report_options = {f"STT {i} - {r.get('machine_name')}": r.get('id') for i, r in enumerate(reports, 1)}
        selected_option = st.selectbox("Chọn máy thao tác:", list(report_options.keys()), label_visibility="collapsed")
        selected_id = report_options[selected_option]

    # Tìm thông tin bản ghi được chọn
    selected_row = next((r for r in reports if r.get('id') == selected_id), None)
    is_selected_done = selected_row.get("status") == "Hoàn thành" if selected_row else False

    with col_act1:
        if st.button("✏️ Sửa", use_container_width=True):
            st.session_state.edit_id = selected_id
            st.rerun()

    with col_act2:
        check_label = "⬜ Chưa xong" if is_selected_done else "✅ Hoàn thành"
        if st.button(check_label, use_container_width=True):
            new_status = "Đang sửa" if is_selected_done else "Hoàn thành"
            supabase.table("repair_reports").update({"status": new_status}).eq("id", selected_id).execute()
            st.rerun()

    with col_act3:
        if st.button("🗑️ Xóa", use_container_width=True):
            st.session_state["confirm_del_id"] = selected_id

    if st.session_state.get("confirm_del_id") == selected_id:
        pwd = st.text_input("Mật khẩu (230):", type="password", key="del_pwd_input")
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if st.button("Xác nhận xóa", type="primary", use_container_width=True):
                if pwd == "230":
                    supabase.table("repair_reports").delete().eq("id", selected_id).execute()
                    st.session_state.pop("confirm_del_id", None)
                    st.success("Đã xóa!")
                    st.rerun()
                else:
                    st.error("Mật khẩu sai!")
        with c_p2:
            if st.button("Hủy", use_container_width=True):
                st.session_state.pop("confirm_del_id", None)
                st.rerun()
