import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client

# Cấu hình trang hiển thị tràn màn hình (wide)
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

# Hàm dịch tự động Việt -> Trung
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

# XÓA SẠCH LỀ THỪA, TỐI ƯU HIỂN THỊ TOÀN MÀN HÌNH
st.markdown("""
<style>
    .stApp {
        background-color: #fdf2f8 !important;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 0.2rem !important;
        padding-right: 0.2rem !important;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Lấy dữ liệu báo cáo từ Supabase
try:
    res = supabase.table("repair_reports").select("*").order("id", desc=True).execute()
    reports = res.data
except Exception:
    reports = []

# TẠO KHUNG BÁO CÁO FULL CHIỀU NGANG DÀNH RIÊNG CHO ĐIỆN THOẠI
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
            <td style="padding: 10px 4px; text-align: center; font-weight: bold; border-bottom: 1px solid #f472b6; font-size: 12px;">{idx}</td>
            <td style="padding: 10px 4px; text-align: center; font-weight: bold; color: #1e40af; border-bottom: 1px solid #f472b6; font-size: 13px;">{r.get('machine_name', '')}</td>
            <td style="padding: 10px 4px; text-align: center; font-size: 11px; color: #475569; border-bottom: 1px solid #f472b6;">{time_display}</td>
            <td style="padding: 10px 6px; border-bottom: 1px solid #f472b6;">
                <div style="font-weight: 600; color: #0f172a; font-size: 12px; line-height: 1.3;">{c_vi_val}</div>
                <div style="color: #db2777; font-size: 11px; font-weight: bold; margin-top: 2px;">{c_zh_val}</div>
            </td>
            <td style="padding: 10px 6px; border-bottom: 1px solid #f472b6;">
                <div style="font-weight: 600; color: #0f172a; font-size: 12px; line-height: 1.3;">{s_vi_val}</div>
                <div style="color: #db2777; font-size: 11px; font-weight: bold; margin-top: 2px;">{s_zh_val}</div>
            </td>
            <td style="padding: 10px 4px; text-align: center; font-weight: 600; color: #334155; border-bottom: 1px solid #f472b6; font-size: 11px;">{r.get('estimated_time', '')}</td>
            <td style="padding: 10px 4px; text-align: center; border-bottom: 1px solid #f472b6;">
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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #fdf2f8; }}
        
        .btn-box {{ text-align: center; padding: 8px; position: sticky; top: 0; background-color: #fdf2f8; z-index: 99; }}
        .btn-copy {{
            background-color: #be185d;
            color: white;
            border: none;
            padding: 12px 18px;
            font-size: 15px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            width: 100%;
        }}
        .btn-copy:active {{ background-color: #9d174d; }}
        
        /* KHUNG TỰ ĐỘNG CUỘN NGANG CHO ĐIỆN THOẠI */
        .outer-wrapper {{
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}
        
        #capture-target {{
            min-width: 1100px; /* Độ rộng đảm bảo hiển thị đẹp và đủ 7 cột */
            background-color: #fdf2f8;
            padding: 15px;
            box-sizing: border-box;
            border: 2px solid #be185d;
            border-radius: 10px;
        }}
        
        .title {{ text-align: center; color: #1e40af; font-size: 20px; font-weight: bold; }}
        .subtitle {{ text-align: center; color: #be185d; font-size: 14px; font-weight: bold; margin-bottom: 12px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; table-layout: fixed; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }}
        th {{ background-color: #1e40af; color: white; font-size: 12px; padding: 8px 2px; text-align: center; word-wrap: break-word; }}
        td {{ word-wrap: break-word; overflow-wrap: break-word; }}
    </style>
    </head>
    <body>
        <div class="btn-box">
            <button class="btn-copy" onclick="captureAndCopy()">📸 CHỤP & SAO CHÉP BẢNG BÁO CÁO FULL 7 CỘT</button>
        </div>

        <div class="outer-wrapper">
            <div id="capture-target">
                <div class="title">BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC</div>
                <div class="subtitle">设备维修进度汇报</div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 5%;">STT<br><small>序号</small></th>
                            <th style="width: 10%;">Máy<br><small>设备</small></th>
                            <th style="width: 14%;">Bắt Đầu<br><small>开始时间</small></th>
                            <th style="width: 26%;">Nội Dung Sửa Chữa<br><small>维修内容</small></th>
                            <th style="width: 26%;">Giải Pháp<br><small>解决方案</small></th>
                            <th style="width: 10%;">Dự Kiến<br><small>预计完成</small></th>
                            <th style="width: 9%;">Trạng Thái<br><small>状态</small></th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <script>
        function captureAndCopy() {{
            var element = document.getElementById('capture-target');
            html2canvas(element, {{ scale: 2, windowWidth: 1150 }}).then(function(canvas) {{
                canvas.toBlob(function(blob) {{
                    if (navigator.clipboard && window.ClipboardItem) {{
                        var item = new ClipboardItem({{ "image/png": blob }});
                        navigator.clipboard.write([item]).then(function() {{
                            alert("✅ Đã sao chép ảnh báo cáo ĐẦY ĐỦ 7 CỘT! Anh sang Zalo/WeChat bấm Dán (Paste) là xong nhé!");
                        }}).catch(function(err) {{
                            downloadImage(canvas);
                        }});
                    }} else {{
                        downloadImage(canvas);
                    }}
                }});
            }});
        }}

        function downloadImage(canvas) {{
            var link = document.createElement('a');
            link.download = 'Bao_Cao_Tien_Do_Full.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
            alert("📥 Ảnh báo cáo đã tải về máy! Anh mở Zalo/WeChat gửi ảnh vừa tải nhé!");
        }}
        </script>
    </body>
    </html>
    """
    components.html(export_html, height=600, scrolling=True)
else:
    st.info("Chưa có dữ liệu báo cáo nào trong cơ sở dữ liệu.")
