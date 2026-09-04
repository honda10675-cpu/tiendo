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

# CSS ÉP GIAO DIỆN HÀNG NGANG CHUẨN ĐIỆN THOẠI (KHÔNG LỘ MÃ HTML)
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
        font-size: 12px;
        font-weight: 500;
        display: block;
        margin-top: 3px;
    }

    /* Bắt buộc Streamlit columns không bị bẻ dòng trên điện thoại */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        min-width: 750px !important;
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

# BẢNG TIẾN ĐỘ SỬA CHỮA (XUẤT RA DẠNG NGUYÊN BẢN CỦA STREAMLIT)
st.markdown('<div class="table-header">BẢNG TIẾN ĐỘ SỬA CHỮA / 维修进度表</div>', unsafe_allow_html=True)

try:
    res = supabase.table("repair_reports").select("*").order("id", desc=True).execute()
    reports = res.data
except Exception:
    reports = []

if not reports:
    st.info("Chưa có dữ liệu báo cáo nào.")
else:
    # Tiêu đề bảng
    h_col1, h_col2, h_col3, h_col4, h_col5, h_col6, h_col7 = st.columns([0.6, 1.2, 1.5, 2.5, 2.5, 1.5, 1.8])
    with h_col1: st.markdown("**STT<br><span style='font-size:11px;'>序号</span>**", unsafe_allow_html=True)
    with h_col2: st.markdown("**Máy<br><span style='font-size:11px;'>设备</span>**", unsafe_allow_html=True)
    with h_col3: st.markdown("**Thời Gian Bắt Đầu<br><span style='font-size:11px;'>开始时间</span>**", unsafe_allow_html=True)
    with h_col4: st.markdown("**Nội Dung<br><span style='font-size:11px;'>内容</span>**", unsafe_allow_html=True)
    with h_col5: st.markdown("**Giải Pháp + Linh Kiện<br><span style='font-size:11px;'>解决方案+规格</span>**", unsafe_allow_html=True)
    with h_col6: st.markdown("**Thời Gian Dự Kiến<br><span style='font-size:11px;'>预计时间</span>**", unsafe_allow_html=True)
    with h_col7: st.markdown("**Thao Tác<br><span style='font-size:11px;'>操作</span>**", unsafe_allow_html=True)

    st.divider()

    # Dữ liệu bảng
    for idx, row in enumerate(reports, 1):
        row_id = row.get("id")
        is_done = row.get("status") == "Hoàn thành"
        time_display = convert_utc_to_vn(row.get("created_at", ""))

        c_vi_val = row.get("content_vi", "")
        c_zh_val = row.get("content_zh") if row.get("content_zh") else translate_to_zh(c_vi_val)

        s_vi_val = row.get("solution_vi") if row.get("solution_vi") else row.get("solution", "")
        s_zh_val = row.get("solution_zh") if row.get("solution_zh") else translate_to_zh(s_vi_val)

        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.6, 1.2, 1.5, 2.5, 2.5, 1.5, 1.8])

        with c1: st.write(f"**{idx}**")
        with c2: st.write(f"**{row.get('machine_name')}**")
        with c3: st.caption(time_display)
        
        with c4:
            st.write(c_vi_val)
            if c_zh_val:
                st.markdown(f'<span class="text-zh">{c_zh_val}</span>', unsafe_allow_html=True)
                
        with c5:
            st.write(s_vi_val if s_vi_val else "")
            if s_zh_val:
                st.markdown(f'<span class="text-zh">{s_zh_val}</span>', unsafe_allow_html=True)
                
        with c6:
            st.write(row.get("estimated_time"))
            if is_done:
                st.markdown("🟢 **Đã xong / 已完成**")

        with c7:
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
