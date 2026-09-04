# Cấu trúc bảng HTML đầy đủ thẻ mở table và thead
    html_code = """
    <table class="custom-table">
        <thead>
            <tr>
                <th style="width: 8%;">STT<br><span style="font-weight:normal;">序号</span></th>
                <th style="width: 12%;">Máy<br><span style="font-weight:normal;">设备</span></th>
                <th style="width: 15%;">Thời Gian Bắt Đầu<br><span style="font-weight:normal;">开始时间</span></th>
                <th style="width: 25%;">Nội Dung<br><span style="font-weight:normal;">内容</span></th>
                <th style="width: 25%;">Giải Pháp + Linh Kiện<br><span style="font-weight:normal;">解决方案+规格</span></th>
                <th style="width: 15%;">Thời Gian Dự Kiến<br><span style="font-weight:normal;">预计时间</span></th>
            </tr>
        </thead>
        <tbody>
    """
    
    for idx, row in enumerate(reports, 1):
        created_at = row.get("created_at", "")[:16].replace("T", " ")
        c_zh_text = f'<br><span class="text-zh">{row.get("content_zh")}</span>' if row.get("content_zh") else ""
        s_zh_text = f'<br><span class="text-zh">{row.get("solution_zh")}</span>' if row.get("solution_zh") else ""
        
        html_code += f"""
        <tr>
            <td><b>{idx}</b></td>
            <td><b>{row.get('machine_name')}</b></td>
            <td style="font-size: 11px;">{created_at}</td>
            <td style="text-align: left;">{row.get('content_vi')}{c_zh_text}</td>
            <td style="text-align: left;">{row.get('solution_vi')}{s_zh_text}</td>
            <td>{row.get('estimated_time')}</td>
        </tr>
        """
        
    html_code += "</tbody></table>"
    st.markdown(html_code, unsafe_allow_html=True)
