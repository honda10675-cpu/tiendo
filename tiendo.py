import streamlit as st
from datetime import datetime, timedelta
import urllib.parse
import urllib.request
import json
from supabase import create_client, Client

# Cấu hình trang
st.set_page_config(page_title="BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC", layout="wide")

# Hàm làm tròn giờ thực tế đến 30 phút gần nhất (VD: 17:42 -> 17:30 hoặc 18:00)
def get_rounded_time():
    now = datetime.now()
    minute = now.minute
    if minute < 15:
        now = now.replace(minute=0, second=0, microsecond=0)
    elif minute < 45:
        now = now.replace(minute=30, second=0, microsecond=0)
    else:
        now = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return now.strftime("%Y-%m-%d %H:%M")

# Hàm dịch tự động Việt -> Trung chuẩn xác
def translate_to_zh(text):
    if not text:
        return ""
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=vi&tl=zh-CN&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        
        translated = ""
        for item in data[0]:
            if item[0]:
                translated += item[0]
        return translated
    except Exception:
        return ""

# Kết nối Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Chưa cấu hình Secrets SUPABASE_URL và SUPABASE_KEY trong Streamlit Settings!")
    st.stop()

# CSS định dạng kiểu dáng chuẩn
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
    .text-zh {
        color: #d97706;
        font-size: 13px;
        font-weight: 500;
        display: block;
        margin-top: 3px;
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

# ---------------------------------------------------------
# KHUNG NHẬP BÁO CÁO
# ---------------------------------------------------------
with st.container():
    st.markdown("**Tên Máy / 设备名称:**")
    machine = st.text_input("machine_input", value=edit_data.get("machine_name", ""), placeholder="Nhập tên máy...", label_visibility="collapsed")

    st.markdown("**Thời Gian Bắt Đầu (Tự động làm tròn 30p) / 开始时间:**")
    start_time_val = edit_data.get("start_time") if edit_data.get("start_time") else get_rounded_time()
    start_time = st.text_input("start_time_input", value=start_time_val, label_visibility="collapsed")

    st.markdown("**Nội Dung Sửa Chữa & Giải Pháp / 维修内容与解决方案:**")
    c_vi = st.text_area("c_vi_input", value=edit_data.get("content_vi", ""), placeholder="Nhập nội dung hư hỏng và phương án sửa chữa...", height=90, label_visibility="collapsed")

    st.markdown("**Thời Gian Dự Kiến Hoàn Thành / 预计完成时间:**")
    est_time = st.text_input("est_input", value=edit_data.get("estimated_time", ""), placeholder="Ví dụ: 17:00 ngày 06/09/2026...", label_visibility="collapsed")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        btn_label = "Cập Nhật Báo Cáo / 更新汇报" if st.session_state.edit_id else "Thêm Báo Cáo / 添加汇报"
        if st.button(btn_label, type="primary", use_container_width=True):
            if not machine or not c_vi or not est_time:
                st.warning("Vui lòng nhập đủ thông tin Máy, Nội dung và Thời gian dự kiến!")
            else:
                # Tự động dịch sang Tiếng Trung
                c_zh = translate_to_zh(c_vi)

                payload = {
                    "machine_name": machine,
                    "start_time": start_time,
                    "content_vi": c_vi,
                    "content_zh": c_zh,
                    "solution_vi": "",
                    "solution_zh": "",
                    "estimated_time": est_time
                }

                if st.session_state.edit_id:
                    supabase.table("repair_reports").update(payload).eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None
                    st.success("Đã cập nhật báo cáo!")
                else:
                    payload["status"] = "Đang sửa"
                    supabase.table("repair_reports").insert(payload).execute()
                    st.success("Đã thêm báo cáo mới!")
                st.rerun()

    with col_b2:
        st.button("Tải Hình Báo Cáo / 下载图片", use_container_width=True)

# ---------------------------------------------------------
# BẢNG TIẾN ĐỘ SỬA CHỮA
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
    h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns([0.6, 1.2, 1.8, 3.8, 1.8, 1.8])
    with h_col1: st.markdown("**STT<br><span style='font-size:11px;'>序号</span>**", unsafe_allow_html=True)
    with h_col2: st.markdown("**Máy<br><span style='font-size:11px;'>设备</span>**", unsafe_allow_html=True)
    with h_col3: st.markdown("**Bắt Đầu<br><span style='font-size:11px;'>开始时间</span>**", unsafe_allow_html=True)
    with h_col4: st.markdown("**Nội Dung & Giải Pháp<br><span style='font-size:11px;'>内容与解决方案</span>**", unsafe_allow_html=True)
    with h_col5: st.markdown("**Dự Kiến<br><span style='font-size:11px;'>预计时间</span>**", unsafe_allow_html=True)
    with h_col6: st.markdown("**Thao Tác<br><span style='font-size:11px;'>操作</span>**", unsafe_allow_html=True)

    st.divider()

    for idx, row in enumerate(reports, 1):
        row_id = row.get("id")
        is_done = row.get("status") == "Hoàn thành"
        
        # Ưu tiên lấy start_time đã làm tròn 30p
        time_display = row.get("start_time") if row.get("start_time") else row.get("created_at", "")[:16].replace("T", " ")

        # Tự động dịch bổ sung nếu bản ghi cũ chưa có Tiếng Trung
        content_vi = row.get("content_vi", "")
        content_zh = row.get("content_zh", "")
        if content_vi and not content_zh:
            content_zh = translate_to_zh(content_vi)

        c1, c2, c3, c4, c5, c6 = st.columns([0.6, 1.2, 1.8, 3.8, 1.8, 1.8])

        with c1: st.write(f"**{idx}**")
        with c2: st.write(f"**{row.get('machine_name')}**")
        with c3: st.caption(time_display)
        with c4:
            st.write(content_vi)
            if content_zh:
                st.markdown(f'<span class="text-zh">{content_zh}</span>', unsafe_allow_html=True)
        with c5:
            st.write(row.get("estimated_time"))
            if is_done:
                st.markdown("🟢 **Đã xong / 已完成**")

        with c6:
            act_col1, act_col2, act_col3 = st.columns(3)
            
            with act_col1:
                if st.button("✏️", key=f"edit_{row_id}", help="Sửa"):
                    st.session_state.edit_id = row_id
                    st.rerun()

            with act_col2:
                check_icon = "✅" if is_done else "⬜"
                if st.button(check_icon, key=f"done_{row_id}", help="Tích hoàn thành"):
                    new_status = "Đang sửa" if is_done else "Hoàn thành"
                    supabase.table("repair_reports").update({"status": new_status}).eq("id", row_id).execute()
                    st.rerun()

            with act_col3:
                if st.button("🗑️", key=f"del_{row_id}", help="Xóa"):
                    st.session_state[f"confirm_del_{row_id}"] = True

            if st.session_state.get(f"confirm_del_{row_id}"):
                pwd = st.text_input("Mật khẩu (230):", type="password", key=f"pwd_{row_id}")
                col_pass1, col_pass2 = st.columns(2)
                with col_pass1:
                    if st.button("OK", key=f"ok_del_{row_id}"):
                        if pwd == "230":
                            supabase.table("repair_reports").delete().eq("id", row_id).execute()
                            st.session_state.pop(f"confirm_del_{row_id}", None)
                            st.success("Đã xóa!")
                            st.rerun()
                        else:
                            st.error("Sai MK!")
                with col_pass2:
                    if st.button("Hủy", key=f"cancel_del_{row_id}"):
                        st.session_state.pop(f"confirm_del_{row_id}", None)
                        st.rerun()
        st.divider()
