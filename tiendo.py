import base64
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
        return dt_vn.strftime("%Y-%m-%d %H:%M")
    except Exception:
        try:
            clean_str = dt_str.replace("T", " ")[:16]
            dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M")
            dt_vn = dt + timedelta(hours=7)
            return dt_vn.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return dt_str[:16] if len(dt_str) >= 16 else dt_str

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
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        padding-left: 0.1rem !important;
        padding-right: 0.1rem !important;
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
        
        st_text_vi = "🟢 Đã xong" if is_done else "🟡 Đang sửa"
        st_text_zh = "已完成" if is_done else "维修中"
        st_color = "#15803d" if is_done else "#b45309"

        rows_html += f"""
        <tr style="background-color: {bg_cls};">
            <td style="padding: 10px 4px; text-align: center; font-weight: bold; border-bottom: 1px solid #f472b6; font-size: 13px;">{idx}</td>
            <td style="padding: 10px 4px; text-align: center; font-weight: bold; color: #1e40af; border-bottom: 1px solid #f472b6; font-size: 14px;">{r.get('machine_name', '')}</td>
            <td style="padding: 10px 4px; text-align: center; font-size: 12px; color: #475569; border-bottom: 1px solid #f472b6;">{time_display}</td>
            <td style="padding: 10px 6px; border-bottom: 1px solid #f472b6;">
                <div style="font-weight: 600; color: #0f172a; font-size: 13px; line-height: 1.3;">{c_vi_val}</div>
                <div style="color: #db2777; font-size: 12px; font-weight: bold; margin-top: 2px;">{c_zh_val}</div>
            </td>
            <td style="padding: 10px 6px; border-bottom: 1px solid #f472b6;">
                <div style="font-weight: 600; color: #0f172a; font-size: 13px; line-height: 1.3;">{s_vi_val}</div>
                <div style="color: #db2777; font-size: 12px; font-weight: bold; margin-top: 2px;">{s_zh_val}</div>
            </td>
            <td style="padding: 10px 4px; text-align: center; font-weight: 600; color: #334155; border-bottom: 1px solid #f472b6; font-size: 12px;">{r.get('estimated_time', '')}</td>
            <td style="padding: 10px 4px; text-align: center; border-bottom: 1px solid #f472b6;">
                <div style="font-weight: bold; color: {st_color}; font-size: 12px;">{st_text_vi}</div>
                <div style="font-weight: bold; color: {st_color}; font-size: 11px;">{st_text_zh}</div>
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
        
        .btn-box {{ text-align: center; padding: 5px; position: sticky; top: 0; background-color: #fdf2f8; z-index: 99; }}
        .btn-download {{
            background-color: #be185d;
            color: white;
            border: none;
            padding: 12px 18px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            width: 100%;
        }}
        .btn-download:active {{ background-color: #9d174d; }}
        
        .outer-wrapper {{ width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }}
        
        #capture-target {{
            min-width: 1200px;
            background-color: #fdf2f8;
            padding: 15px;
            box-sizing: border-box;
            border: 2px solid #be185d;
            border-radius: 10px;
        }}
        
        .title {{ text-align: center; color: #1e40af; font-size: 22px; font-weight: bold; }}
        .subtitle {{ text-align: center; color: #be185d; font-size: 15px; font-weight: bold; margin-bottom: 12px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; table-layout: fixed; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }}
        th {{ background-color: #1e40af; color: white; font-size: 13px; padding: 8px 2px; text-align: center; word-wrap: break-word; }}
        td {{ word-wrap: break-word; overflow-wrap: break-word; }}
    </style>
    </head>
    <body>
        <div class="btn-box">
            <button class="btn-download" onclick="downloadImage()">📥 TẢI ẢNH BÁO CÁO VỀ MÁY (GỬI ZALO/WECHAT)</button>
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
        function downloadImage() {{
            var element = document.getElementById('capture-target');
            html2canvas(element, {{ scale: 2, windowWidth: 1250 }}).then(function(canvas) {{
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
    components.html(export_html, height=650, scrolling=True)
else:
    st.info("Chưa có dữ liệu báo cáo nào trong cơ sở dữ liệu.")
