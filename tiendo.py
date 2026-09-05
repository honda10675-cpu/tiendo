import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client

st.set_page_config(page_title="BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC", layout="wide")

def convert_utc_to_vn(dt_str):
    if not dt_str:
        tz_vn = timezone(timedelta(hours=7))
        return datetime.now(tz_vn).strftime("%Y-%m-%d %H:%M")
    try:
        clean_str = dt_str.replace("T", " ")[:19]
        dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
        dt_vn = dt + timedelta(hours=7)
        return dt_vn.strftime("%d/%m %H:%M")
    except Exception:
        return dt_str[:16] if len(dt_str) >= 16 else dt_str

def translate_to_zh(text):
    if not text or not str(text).strip():
        return ""
    text_clean = str(text).strip()
    try:
        url_gt = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=vi&tl=zh-CN&dt=t&q={urllib.parse.quote(text_clean)}"
        req = urllib.request.Request(url_gt, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=3)
        data = json.loads(res.read().decode('utf-8'))
        translated = "".join([item[0] for item in data[0] if item[0]])
        if translated:
            return translated
    except Exception:
        pass
    return ""

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Chưa cấu hình Secrets SUPABASE_URL và SUPABASE_KEY!")
    st.stop()

st.markdown("""
<style>
    .stApp { background-color: #fdf2f8 !important; }
    .block-container {
        padding-top: 0.1rem !important;
        padding-bottom: 0.1rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

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
        
        st_text_vi = "🟢Đã xong" if is_done else "🟡Đang sửa"
        st_text_zh = "已完成" if is_done else "维修中"
        st_color = "#15803d" if is_done else "#b45309"

        rows_html += f"""
        <tr style="background-color: {bg_cls};">
            <td style="padding: 6px 2px; text-align: center; font-weight: bold; border-bottom: 1px solid #f472b6; font-size: 11px;">{idx}</td>
            <td style="padding: 6px 2px; text-align: center; font-weight: bold; color: #1e40af; border-bottom: 1px solid #f472b6; font-size: 11px;">{r.get('machine_name', '')}</td>
            <td style="padding: 6px 2px; text-align: center; font-size: 10px; color: #475569; border-bottom: 1px solid #f472b6;">{time_display}</td>
            <td style="padding: 6px 4px; border-bottom: 1px solid #f472b6;">
                <div style="font-weight: 600; color: #0f172a; font-size: 11px; line-height: 1.2;">{c_vi_val}</div>
                <div style="color: #db2777; font-size: 10px; font-weight: bold; margin-top: 1px;">{c_zh_val}</div>
            </td>
            <td style="padding: 6px 4px; border-bottom: 1px solid #f472b6;">
                <div style="font-weight: 600; color: #0f172a; font-size: 11px; line-height: 1.2;">{s_vi_val}</div>
                <div style="color: #db2777; font-size: 10px; font-weight: bold; margin-top: 1px;">{s_zh_val}</div>
            </td>
            <td style="padding: 6px 2px; text-align: center; font-weight: 600; color: #334155; border-bottom: 1px solid #f472b6; font-size: 10px;">{r.get('estimated_time', '')}</td>
            <td style="padding: 6px 2px; text-align: center; border-bottom: 1px solid #f472b6;">
                <div style="font-weight: bold; color: {st_color}; font-size: 10px;">{st_text_vi}</div>
                <div style="font-weight: bold; color: {st_color}; font-size: 9px;">{st_text_zh}</div>
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
        body {{ margin: 0; padding: 4px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #fdf2f8; }}
        
        .btn-box {{ text-align: center; margin-bottom: 6px; }}
        .btn-download {{
            background-color: #be185d;
            color: white;
            border: none;
            padding: 10px 12px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 6px;
            cursor: pointer;
            width: 100%;
        }}
        .btn-download:active {{ background-color: #9d174d; }}
        
        #capture-target {{
            width: 100%;
            background-color: #fdf2f8;
            padding: 8px 4px;
            border: 2px solid #be185d;
            border-radius: 8px;
        }}
        
        .title {{ text-align: center; color: #1e40af; font-size: 16px; font-weight: bold; }}
        .subtitle {{ text-align: center; color: #be185d; font-size: 12px; font-weight: bold; margin-bottom: 8px; }}
        
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 6px; overflow: hidden; table-layout: fixed; }}
        th {{ background-color: #1e40af; color: white; font-size: 11px; padding: 6px 1px; text-align: center; word-break: break-word; }}
        td {{ word-break: break-word; overflow-wrap: break-word; }}
    </style>
    </head>
    <body>
        <div class="btn-box">
            <button class="btn-download" onclick="downloadImage()">📸 TẢI ÁNH BÁO CÁO TOÀN MÀN HÌNH</button>
        </div>

        <div id="capture-target">
            <div class="title">BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC</div>
            <div class="subtitle">设备维修进度汇报</div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 7%;">STT<br><small>序号</small></th>
                        <th style="width: 12%;">Máy<br><small>设备</small></th>
                        <th style="width: 15%;">Bắt Đầu<br><small>开始</small></th>
                        <th style="width: 25%;">Nội Dung<br><small>内容</small></th>
                        <th style="width: 23%;">Giải Pháp<br><small>方案</small></th>
                        <th style="width: 10%;">Dự Kiến<br><small>预计</small></th>
                        <th style="width: 8%;">Trạng Thái<br><small>状态</small></th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>

        <script>
        function downloadImage() {{
            var element = document.getElementById('capture-target');
            html2canvas(element, {{ scale: 3 }}).then(function(canvas) {{
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
    components.html(export_html, height=700, scrolling=True)
else:
    st.info("Chưa có dữ liệu báo cáo nào.")
