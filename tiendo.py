import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
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
    
    # MyMemory API
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

    # Google Translate API
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

# CSS giao diện
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1e40af;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 2px;
    }
    .sub-title {
        text-align: center;
        color: #be185d;
        font-size: 13px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .table-header {
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        color: #334155;
        margin-top: 20px;
        margin-bottom: 10px;
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

# BẢNG TIẾN ĐỘ SỬA CHỮA
st.markdown('<div class="table-header">BẢNG TIẾN ĐỘ SỬA CHỮA / 维修进度表</div>', unsafe_allow_html=True)

try:
    res = supabase.table("repair_reports").select("*").order("id", desc=True).execute()
    reports = res.data
except Exception:
    reports = []

if reports:
    rows_html = ""
    for idx, r in enumerate(reports, 1):
        is_done = r.get("status") == "Hoàn thành"
        bg_cls = "#ffffff" if idx % 2 == 1 else "#fdf2f8"
        time_display = convert_utc_to_vn(r.get("created_at", ""))
        
        c_vi_val = r.get("content_vi", "")
        c_zh_val = r.get("content_zh") if r.get("content_zh") else translate_to_zh(c_vi_val)
        
        s_vi_val = r.get("solution_vi") if r.get("solution_vi") else r.get("solution", "")
        s_zh_val = r.get("solution_zh") if r.get("solution_zh") else translate_to_zh(s_vi_val)
        
        st_text_vi = "🟢 Đã xong" if is_done else "🟡 Đang sửa"
        st_text_zh = "已完成" if is_done else "维修中"
        st_color = "#15803d" if is_done else "#b45309"

        rows_html += f"""
        <tr style="background-color: {bg_cls};">
            <td style="padding: 8px 4px; text-align: center; font-weight: bold; border-bottom: 1px solid #cbd5e1; font-size: 12px;">{idx}</td>
            <td style="padding: 8px 4px; text-align: center; font-weight: bold; color: #1e40af; border-bottom: 1px solid #cbd5e1; font-size: 13px;">{r.get('machine_name', '')}</td>
            <td style="padding: 8px 4px; text-align: center; font-size: 11px; color: #475569; border-bottom: 1px solid #cbd5e1;">{time_display}</td>
            <td style="padding: 8px 6px; border-bottom: 1px solid #cbd5e1;">
                <div style="font-weight: 600; color: #0f172a; font-size: 12px; line-height: 1.3;">{c_vi_val}</div>
                <div style="color: #d97706; font-size: 11px; font-weight: bold; margin-top: 2px;">{c_zh_val}</div>
            </td>
            <td style="padding: 8px 6px; border-bottom: 1px solid #cbd5e1;">
                <div style="font-weight: 600; color: #0f172a; font-size: 12px; line-height: 1.3;">{s_vi_val}</div>
                <div style="color: #d97706; font-size: 11px; font-weight: bold; margin-top: 2px;">{s_zh_val}</div>
            </td>
            <td style="padding: 8px 4px; text-align: center; font-weight: 600; color: #334155; border-bottom: 1px solid #cbd5e1; font-size: 11px;">{r.get('estimated_time', '')}</td>
            <td style="padding: 8px 4px; text-align: center; border-bottom: 1px solid #cbd5e1;">
                <div style="font-weight: bold; color: {st_color}; font-size: 11px;">{st_text_vi}</div>
                <div style="font-weight: bold; color: {st_color}; font-size: 10px;">{st_text_zh}</div>
            </td>
        </tr>
        """

    export_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: transparent; }}
        
        .btn-box {{ text-align: center; margin-bottom: 8px; }}
        .btn-download {{
            background-color: #be185d;
            color: white;
            border: none;
            padding: 12px 16px;
            font-size: 15px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
        }}
        .btn-download:active {{ background-color: #9d174d; }}
        
        .table-wrapper {{ width: 100%; overflow-x: auto; }}
        
        #capture-target {{
            min-width: 850px;
            background-color: #ffffff;
            padding: 12px;
            border: 2px solid #1e40af;
            border-radius: 8px;
        }}
        
        .title {{ text-align: center; color: #1e40af; font-size: 18px; font-weight: bold; }}
        .subtitle {{ text-align: center; color: #be185d; font-size: 12px; font-weight: bold; margin-bottom: 10px; }}
        
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 4px; overflow: hidden; table-layout: fixed; }}
        th {{ background-color: #1e40af; color: white; font-size: 12px; padding: 8px 2px; text-align: center; }}
        td {{ word-break: break-word; overflow-wrap: break-word; }}
    </style>
    </head>
    <body>
        <div class="btn-box">
            <button class="btn-download" onclick="downloadImage()">📸 TẢI ÁNH BÁO CÁO TOÀN MÀN HÌNH</button>
        </div>

        <div class="table-wrapper">
            <div id="capture-target">
                <div class="title">BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC</div>
                <div class="subtitle">设备维修进度汇报</div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 6%;">STT<br><small>序号</small></th>
                            <th style="width: 12%;">Máy<br><small>设备</small></th>
                            <th style="width: 15%;">Bắt Đầu<br><small>开始时间</small></th>
                            <th style="width: 27%;">Nội Dung<br><small>维修内容</small></th>
                            <th style="width: 25%;">Giải Pháp<br><small>解决方案</small></th>
                            <th style="width: 10%;">Dự Kiến<br><small>预计完成</small></th>
                            <th style="width: 10%;">Trạng Thái<br><small>状态</small></th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <script>
        function downloadImage() {{
            var element = document.getElementById('capture-target');
            html2canvas(element, {{ scale: 2 }}).then(function(canvas) {{
                var link = document.createElement('a');
                link.download = 'Bao_Cao_Tien_Do.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            }});
        }}
        </script>
    </body>
    </html>
    """
    
    dynamic_height = max(450, len(reports) * 80 + 130)
    components.html(export_html, height=dynamic_height, scrolling=True)

# PHẦN QUẢN LÝ THAO TÁC (ĐÃ CHỌN MÁY & HÀNG NGANG)
st.markdown('<div class="table-header">QUẢN LÝ THAO TÁC / 操作管理</div>', unsafe_allow_html=True)

if not reports:
    st.info("Chưa có dữ liệu báo cáo nào.")
else:
    # 1. Chọn máy muốn thao tác
    machine_options = {f"#{i+1} - {r.get('machine_name', '')} ({r.get('status', 'Đang sửa')})": r for i, r in enumerate(reports)}
    selected_machine_label = st.selectbox("Chọn máy muốn thao tác / 选择要操作的设备:", list(machine_options.keys()))
    
    selected_row = machine_options[selected_machine_label]
    row_id = selected_row.get("id")
    is_done = selected_row.get("status") == "Hoàn thành"

    # 2. Hiển thị 3 nút thao tác trên 1 HÀNG NGANG
    c_btn1, c_btn2, c_btn3 = st.columns(3)

    with c_btn1:
        if st.button("✏️ Sửa Báo Cáo", use_container_width=True, key=f"edit_sel_{row_id}"):
            st.session_state.edit_id = row_id
            st.rerun()

    with c_btn2:
        check_text = "✅ Đã Hoàn Thành" if is_done else "⬜ Đánh Dấu Xong"
        if st.button(check_text, use_container_width=True, key=f"done_sel_{row_id}"):
            new_status = "Đang sửa" if is_done else "Hoàn thành"
            supabase.table("repair_reports").update({"status": new_status}).eq("id", row_id).execute()
            st.rerun()

    with c_btn3:
        if st.button("🗑️ Xóa Báo Cáo", use_container_width=True, key=f"del_sel_{row_id}"):
            st.session_state[f"confirm_del_{row_id}"] = True

    # Xác nhận xóa mật khẩu 230
    if st.session_state.get(f"confirm_del_{row_id}"):
        pwd = st.text_input("Nhập mật khẩu xóa (230):", type="password", key=f"pwd_{row_id}")
        col_pass1, col_pass2 = st.columns(2)
        with col_pass1:
            if st.button("Xác Nhận Xóa", key=f"ok_del_{row_id}", type="primary", use_container_width=True):
                if pwd == "230":
                    supabase.table("repair_reports").delete().eq("id", row_id).execute()
                    st.session_state.pop(f"confirm_del_{row_id}", None)
                    st.success("Đã xóa báo cáo thành công!")
                    st.rerun()
                else:
                    st.error("Sai mật khẩu!")
        with col_pass2:
            if st.button("Hủy Bỏ", key=f"cancel_del_{row_id}", use_container_width=True):
                st.session_state.pop(f"confirm_del_{row_id}", None)
                st.rerun()
