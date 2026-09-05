import io
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
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

# Hàm tạo ảnh PNG trực tiếp bằng Pillow (Không gây lỗi máy chủ)
def create_table_image(reports_data):
    width = 1200
    row_height = 65
    header_height = 80
    padding_top = 70
    
    total_height = padding_top + header_height + max(1, len(reports_data)) * row_height + 40
    img = Image.new('RGB', (width, total_height), color='#ffffff')
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_header = ImageFont.truetype("arial.ttf", 13)
        font_body = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        font_title = font_header = font_body = ImageFont.load_default()

    # Tiêu đề
    draw.text((width // 2, 25), "BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC / 设备维修进度汇报", fill="#1e40af", font=font_title, anchor="mm")

    # Kích thước cột
    cols = [
        ("STT\n序号", 60),
        ("Máy\n设备", 100),
        ("Thời Gian Bắt Đầu\n开始时间", 160),
        ("Nội Dung Sửa Chữa\n维修内容", 330),
        ("Giải Pháp\n解决方案", 330),
        ("Dự Kiến\n预计完成", 120),
        ("Trạng Thái\n状态", 100)
    ]

    # Vẽ Header
    x_curr = 20
    y_curr = padding_top
    draw.rectangle([x_curr, y_curr, width - 20, y_curr + header_height], fill="#1e40af")

    for title, col_w in cols:
        draw.text((x_curr + col_w // 2, y_curr + header_height // 2), title, fill="#ffffff", font=font_header, anchor="mm", align="center")
        draw.rectangle([x_curr, y_curr, x_curr + col_w, y_curr + header_height], outline="#ffffff", width=1)
        x_curr += col_w

    # Vẽ Dữ Liệu
    y_curr += header_height
    for idx, r in enumerate(reports_data, 1):
        x_curr = 20
        is_done = r.get("status") == "Hoàn thành"
        bg_color = "#f8fafc" if idx % 2 == 0 else "#ffffff"
        draw.rectangle([x_curr, y_curr, width - 20, y_curr + row_height], fill=bg_color)

        c_vi_val = r.get("content_vi", "")
        c_zh_val = r.get("content_zh") if r.get("content_zh") else translate_to_zh(c_vi_val)
        full_c = f"{c_vi_val}\n({c_zh_val})" if c_zh_val else c_vi_val

        s_vi_val = r.get("solution_vi") if r.get("solution_vi") else r.get("solution", "")
        s_zh_val = r.get("solution_zh") if r.get("solution_zh") else translate_to_zh(s_vi_val)
        full_s = f"{s_vi_val}\n({s_zh_val})" if s_zh_val else s_vi_val

        st_text = "Đã xong\n已完成" if is_done else "Đang sửa\n维修中"

        row_vals = [
            str(idx),
            r.get("machine_name", ""),
            convert_utc_to_vn(r.get("created_at", "")),
            full_c,
            full_s,
            r.get("estimated_time", ""),
            st_text
        ]

        for i, (val, (title, col_w)) in enumerate(zip(row_vals, cols)):
            text_color = "#15803d" if i == 6 and is_done else ("#b45309" if i == 6 else "#0f172a")
            align_anchor = "lm" if i in [3, 4] else "mm"
            text_x = x_curr + 10 if i in [3, 4] else x_curr + col_w // 2

            draw.text((text_x, y_curr + row_height // 2), val, fill=text_color, font=font_body, anchor=align_anchor)
            draw.rectangle([x_curr, y_curr, x_curr + col_w, y_curr + row_height], outline="#cbd5e1", width=1)
            x_curr += col_w

        y_curr += row_height

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

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
        font-size: 20px;
        margin-bottom: 2px;
    }
    .sub-title {
        text-align: center;
        color: #475569;
        font-size: 13px;
        margin-bottom: 15px;
    }
    .table-header {
        text-align: center;
        font-weight: bold;
        font-size: 16px;
        color: #334155;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    .block-container {
        padding-top: 1.5rem !important;
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

    # Lấy dữ liệu báo cáo
    try:
        res = supabase.table("repair_reports").select("*").order("id", desc=True).execute()
        reports = res.data
    except Exception:
        reports = []

    # NÚT TẢI DẠNG HÌNH ẢNH PNG
    with col_b2:
        if reports:
            img_bytes = create_table_image(reports)
            st.download_button(
                label="Tải ảnh bảng tiến độ sửa chữa",
                data=img_bytes,
                file_name=f"Bao_Cao_Tien_Do_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                mime="image/png",
                use_container_width=True
            )
        else:
            st.button("Tải ảnh bảng tiến độ sửa chữa", disabled=True, use_container_width=True)

# BẢNG TIẾN ĐỘ TƯƠNG THÍCH ĐIỆN THOẠI
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
