import base64
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

# CSS GIAO DIỆN CHỦ ĐỀ XANH - TRẮNG - HỒNG
st.markdown("""
<style>
    /* Nền tổng thể màu hồng phấn dịu */
    .stApp {
        background-color: #fdf2f8 !important;
    }
    .main-title {
        text-align: center;
        color: #1e40af;
        font-weight: bold;
        font-size: 22px;
        margin-bottom: 2px;
    }
    .sub-title {
        text-align: center;
        color: #be185d;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 15px;
    }
    .table-header {
        text-align: center;
        font-weight: bold;
        font-size: 16px;
        color: #1e40af;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
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
    c_vi = st.text_area("c_vi_input", value=edit_data.get("content_vi", ""), placeholder="Nhập nội dung hư hỏng...", height=60, label_visibility="collapsed")

    st.markdown("**Giải Pháp + Quy Cách Linh Kiện / 解决方案+零件规格:**")
    s_vi = st.text_area("s_vi_input", value=edit_data.get("solution_vi", edit_data.get("solution", "")), placeholder="Nhập phương án...", height=60, label_visibility="collapsed")

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

    # Lấy dữ liệu báo cáo từ Supabase
    try:
        res = supabase.table("repair_reports").select("*").order("id", desc=True).execute()
        reports = res.data
    except Exception:
        reports = []

    # NÚT XUẤT ÁNH CHUẨN ĐẸP TỰ ĐỘNG CHỐNG LỖI FONT
    with col_b2:
        if reports:
            # Tạo HTML Bảng đẹp chuẩn Xanh - Trắng - Hồng
            rows_html = ""
            for idx, r in enumerate(reports, 1):
                is_done = r.get("status") == "Hoàn thành"
                bg_cls = "#ffffff" if idx % 2 == 1 else "#fdf2f8"
                time_display = convert_utc_to_vn(r.get("created_at", ""))
                
                c_vi_val = r.get("content_vi", "")
                c_zh_val = r.get("content_zh") if r.get("content_zh") else translate_to_zh(c_vi_val)
                c_html = f"<div>{c_vi_val}</div><div style='color:#db2777; font-size:12px;'>{c_zh_val}</div>" if c_zh_val else c_vi_val

                s_vi_val = r.get("solution_vi") if r.get("solution_vi") else r.get("solution", "")
                s_zh_val = r.get("solution_zh") if r.get("solution_zh") else translate_to_zh(s_vi_val)
                s_html = f"<div>{s_vi_val}</div><div style='color:#db2777; font-size:12px;'>{s_zh_val}</div>" if s_zh_val else s_vi_val

                st_html = "<b style='color:#16a34a;'>🟢 Đã xong<br><small>已完成</small></b>" if is_done else "<b style='color:#d97706;'>🟡 Đang sửa<br><small>维修中</small></b>"

                rows_html += f"""
                <tr style="background-color: {bg_cls}; text-align: center;">
                    <td style="padding: 8px; border: 1px solid #fbcfe8;"><b>{idx}</b></td>
                    <td style="padding: 8px; border: 1px solid #fbcfe8; font-weight: bold; color: #1e40af;">{r.get('machine_name', '')}</td>
                    <td style="padding: 8px; border: 1px solid #fbcfe8; font-size: 11px; color: #475569;">{time_display}</td>
                    <td style="padding: 8px; border: 1px solid #fbcfe8; text-align: left;">{c_html}</td>
                    <td style="padding: 8px; border: 1px solid #fbcfe8; text-align: left;">{s_html}</td>
                    <td style="padding: 8px; border: 1px solid #fbcfe8;">{r.get('estimated_time', '')}</td>
                    <td style="padding: 8px; border: 1px solid #fbcfe8;">{st_html}</td>
                </tr>
                """

            html_report = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #fdf2f8; margin: 0; padding: 15px; }}
                .card {{ background: white; border-radius: 8px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
                .title {{ text-align: center; color: #1e40af; font-size: 20px; font-weight: bold; margin-bottom: 2px; }}
                .subtitle {{ text-align: center; color: #be185d; font-size: 13px; margin-bottom: 15px; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
                th {{ background-color: #1e40af; color: white; padding: 10px; border: 1px solid #1e3a8a; text-align: center; }}
            </style>
            </head>
            <body>
                <div class="card">
                    <div class="title">BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC</div>
                    <div class="subtitle">设备维修进度汇报</div>
                    <table>
                        <thead>
                            <tr>
                                <th style="width:5%;">STT<br><small>序号</small></th>
                                <th style="width:10%;">Máy<br><small>设备</small></th>
                                <th style="width:15%;">Thời Gian Bắt Đầu<br><small>开始时间</small></th>
                                <th style="width:28%;">Nội Dung Sửa Chữa<br><small>维修内容</small></th>
                                <th style="width:28%;">Giải Pháp<br><small>解决方案</small></th>
                                <th style="width:14%;">Dự Kiến<br><small>预计完成</small></th>
                                <th style="width:10%;">Trạng Thái<br><small>状态</small></th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
            </body>
            </html>
            """
            
            # Xuất dạng HTML xem/lưu trực tiếp chuẩn sắc nét
            b64_html = base64.b64encode(html_report.encode('utf-8')).decode('utf-8')
            href = f'<a href="data:text/html;base64,{b64_html}" download="Bao_Cao_Tien_Do_{datetime.now().strftime("%Y%m%d_%H%M")}.html" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#be185d; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">Tải ảnh bảng tiến độ sửa chữa</button></a>'
            st.markdown(href, unsafe_allow_html=True)

        else:
            st.button("Tải ảnh bảng tiến độ sửa chữa", disabled=True, use_container_width=True)

# BẢNG TIẾN ĐỘ HIỂN THỊ TRÊN MAN HÌNH APP
st.markdown('<div class="table-header">BẢNG TIẾN ĐỘ SỬA CHỮA / 维修进度表</div>', unsafe_allow_html=True)

if not reports:
    st.info("Chưa có dữ liệu báo cáo nào.")
else:
    table_data = []
    for idx, row in enumerate(reports, 1):
        is_done = row.get("status") == "Hoàn thành"
        time_display = convert_utc_to_vn(row.get("created_at", ""))

        c_vi_val = row.get("content_vi", "")
        c_zh_val = row.get("content_zh") if row.get("content_zh") else translate_to_zh(c_vi_val)
        full_content = f"{c_vi_val}\n({c_zh_val})" if c_zh_val else c_vi_val

        s_vi_val = row.get("solution_vi") if row.get("solution_vi") else row.get("solution", "")
        s_zh_val = row.get("solution_zh") if row.get("solution_zh") else translate_to_zh(s_vi_val)
        full_solution = f"{s_vi_val}\n({s_zh_val})" if s_zh_val else s_vi_val

        status_str = "🟢 Đã xong / 已完成" if is_done else "🟡 Đang sửa / 维修中"

        table_data.append({
            "STT / 序号": idx,
            "Máy / 设备": row.get("machine_name", ""),
            "Thời Gian Bắt Đầu / 开始时间": time_display,
            "Nội Dung Sửa Chữa / 维修内容": full_content,
            "Giải Pháp / 解决方案": full_solution,
            "Dự Kiến / 预计完成": row.get("estimated_time", ""),
            "Trạng Thái / 状态": status_str
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True, height=300)

    # KHUNG QUẢN LÝ BẢN GHI
    st.markdown("**Quản lý bản ghi / 操作:**")
    report_options = {f"STT {i} - {r.get('machine_name')}": r.get('id') for i, r in enumerate(reports, 1)}
    selected_option = st.selectbox("Chọn máy thao tác:", list(report_options.keys()))
    selected_id = report_options[selected_option]

    selected_row = next((r for r in reports if r.get('id') == selected_id), None)
    is_selected_done = selected_row.get("status") == "Hoàn thành" if selected_row else False

    c_act1, c_act2, c_act3 = st.columns(3)
    with c_act1:
        if st.button("✏️ Sửa", use_container_width=True):
            st.session_state.edit_id = selected_id
            st.rerun()

    with c_act2:
        check_label = "⬜ Chưa xong" if is_selected_done else "✅ Hoàn thành"
        if st.button(check_label, use_container_width=True):
            new_status = "Đang sửa" if is_selected_done else "Hoàn thành"
            supabase.table("repair_reports").update({"status": new_status}).eq("id", selected_id).execute()
            st.rerun()

    with c_act3:
        if st.button("🗑️ Xóa", use_container_width=True):
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
