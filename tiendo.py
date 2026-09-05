import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
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

# Hàm dịch Việt -> Trung
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

# CSS CHỦ ĐỀ XANH - TRẮNG - HỒNG DÀNH Cho DI ĐỘNG
st.markdown("""
<style>
    .stApp {
        background-color: #fdf2f8 !important;
    }
    .main-title {
        text-align: center;
        color: #1e40af;
        font-weight: 800;
        font-size: 22px;
        margin-bottom: 2px;
    }
    .sub-title {
        text-align: center;
        color: #be185d;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 15px;
    }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">设备维修进度汇报</div>', unsafe_allow_html=True)

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "show_cards" not in st.session_state:
    st.session_state.show_cards = True

edit_data = {}
if st.session_state.edit_id:
    try:
        res_edit = supabase.table("repair_reports").select("*").eq("id", st.session_state.edit_id).execute()
        if res_edit.data:
            edit_data = res_edit.data[0]
    except Exception:
        pass

# FORM NHẬP DỮ LIỆU
with st.container():
    st.markdown("**Tên Máy / 设备名称:**")
    machine = st.text_input("machine_input", value=edit_data.get("machine_name", ""), placeholder="Nhập tên máy...", label_visibility="collapsed")

    st.markdown("**Nội Dung Sửa Chữa / 维修内容:**")
    c_vi = st.text_area("c_vi_input", value=edit_data.get("content_vi", ""), placeholder="Nhập nội dung hư hỏng...", height=60, label_visibility="collapsed")

    st.markdown("**Giải Pháp + Linh Kiện / 解决方案+零件:**")
    s_vi = st.text_area("s_vi_input", value=edit_data.get("solution_vi", edit_data.get("solution", "")), placeholder="Nhập phương án...", height=60, label_visibility="collapsed")

    st.markdown("**Thời Gian Dự Kiến / 预计完成时间:**")
    est_time = st.text_input("est_input", value=edit_data.get("estimated_time", ""), placeholder="Ví dụ: 17:00 ngày 08/09...", label_visibility="collapsed")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        btn_label = "Thêm Báo Cáo / 添加" if not st.session_state.edit_id else "Cập Nhật / 更新"
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
        btn_view_text = "📱 Bật Khung Dạng Thẻ Dễ Chụp" if st.session_state.show_cards else "📊 Bật Dạng Bảng Báo Cáo"
        if st.button(btn_view_text, use_container_width=True):
            st.session_state.show_cards = not st.session_state.show_cards
            st.rerun()

# Lấy danh sách báo cáo
try:
    res = supabase.table("repair_reports").select("*").order("id", desc=True).execute()
    reports = res.data
except Exception:
    reports = []

# HIỂN THỊ DẠNG THẺ CHUẨN ĐIỆN THOẠI (DỄ CHỤP MÀN HÌNH GỬI ZALO / WECHAT)
if st.session_state.show_cards and reports:
    cards_html = ""
    for idx, r in enumerate(reports, 1):
        is_done = r.get("status") == "Hoàn thành"
        time_display = convert_utc_to_vn(r.get("created_at", ""))
        
        c_vi_val = r.get("content_vi", "")
        c_zh_val = r.get("content_zh") if r.get("content_zh") else translate_to_zh(c_vi_val)
        
        s_vi_val = r.get("solution_vi") if r.get("solution_vi") else r.get("solution", "")
        s_zh_val = r.get("solution_zh") if r.get("solution_zh") else translate_to_zh(s_vi_val)
        
        st_badge_bg = "#dcfce7" if is_done else "#fef3c7"
        st_color = "#15803d" if is_done else "#b45309"
        st_text = "🟢 Hoàn thành / 已完成" if is_done else "🟡 Đang sửa / 维修中"

        cards_html += f"""
        <div style="background-color: #ffffff; border: 2px solid #be185d; border-radius: 12px; padding: 12px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f472b6; padding-bottom: 8px; margin-bottom: 10px;">
                <span style="font-size: 18px; font-weight: bold; color: #1e40af;">#{idx}. {r.get('machine_name', '')}</span>
                <span style="background-color: {st_badge_bg}; color: {st_color}; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold;">{st_text}</span>
            </div>
            
            <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">
                🕒 Bắt đầu / 开始时间: <strong style="color: #334155;">{time_display}</strong>
            </div>

            <div style="margin-bottom: 8px; background-color: #f8fafc; padding: 8px; border-radius: 6px; border-left: 4px solid #1e40af;">
                <div style="font-size: 12px; font-weight: bold; color: #475569;">Nội Dung Sửa / 维修内容:</div>
                <div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-top: 2px;">{c_vi_val}</div>
                <div style="font-size: 13px; font-weight: bold; color: #be185d; margin-top: 2px;">{c_zh_val}</div>
            </div>

            <div style="margin-bottom: 8px; background-color: #f8fafc; padding: 8px; border-radius: 6px; border-left: 4px solid #be185d;">
                <div style="font-size: 12px; font-weight: bold; color: #475569;">Giải Pháp / 解决方案:</div>
                <div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-top: 2px;">{s_vi_val}</div>
                <div style="font-size: 13px; font-weight: bold; color: #be185d; margin-top: 2px;">{s_zh_val}</div>
            </div>

            <div style="font-size: 12px; font-weight: bold; color: #1e40af; text-align: right; margin-top: 6px;">
                ⏱ Dự kiến / 预计完成: {r.get('estimated_time', '')}
            </div>
        </div>
        """

    card_container_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #fdf2f8; }}
        .wrapper {{ padding: 4px; }}
    </style>
    </head>
    <body>
        <div class="wrapper">
            {cards_html}
        </div>
    </body>
    </html>
    """
    
    # Tính chiều cao động
    calc_height = len(reports) * 230 + 30
    components.html(card_container_html, height=calc_height, scrolling=False)
    st.divider()

# DANH SÁCH BẢNG / THAO TÁC QUẢN LÝ
st.markdown("**DANH SÁCH & QUẢN LÝ / 列表与管理:**")

if not reports:
    st.info("Chưa có dữ liệu báo cáo nào.")
else:
    # Bảng rút gọn hoặc chọn theo thẻ để thao tác
    report_options = {f"STT {i} - {r.get('machine_name')}": r.get('id') for i, r in enumerate(reports, 1)}
    selected_option = st.selectbox("Chọn máy cần chỉnh sửa / xóa / cập nhật:", list(report_options.keys()))
    selected_id = report_options[selected_option]

    selected_row = next((r for r in reports if r.get('id') == selected_id), None)
    is_selected_done = selected_row.get("status") == "Hoàn thành" if selected_row else False

    c_act1, c_act2, c_act3 = st.columns(3)
    with c_act1:
        if st.button("✏️ Sửa / 编辑", use_container_width=True):
            st.session_state.edit_id = selected_id
            st.rerun()

    with c_act2:
        check_label = "⬜ Chưa xong" if is_selected_done else "✅ Hoàn thành"
        if st.button(check_label, use_container_width=True):
            new_status = "Đang sửa" if is_selected_done else "Hoàn thành"
            supabase.table("repair_reports").update({"status": new_status}).eq("id", selected_id).execute()
            st.rerun()

    with c_act3:
        if st.button("🗑️ Xóa / 删除", use_container_width=True):
            st.session_state["confirm_del_id"] = selected_id

    if st.session_state.get("confirm_del_id") == selected_id:
        pwd = st.text_input("Mật khẩu xóa (230):", type="password", key="del_pwd_input")
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if st.button("OK Xóa", type="primary", use_container_width=True):
                if pwd == "230":
                    supabase.table("repair_reports").delete().eq("id", selected_id).execute()
                    st.session_state.pop("confirm_del_id", None)
                    st.success("Đã xóa!")
                    st.rerun()
                else:
                    st.error("Sai MK!")
        with c_p2:
            if st.button("Hủy", use_container_width=True):
                st.session_state.pop("confirm_del_id", None)
                st.rerun()
