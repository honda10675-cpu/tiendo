<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Báo Cáo Tiến Độ Sửa Chữa Máy Móc / 设备维修进度汇报</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        :root { --primary: #0056b3; --success: #28a745; --danger: #dc3545; --warning: #ffc107; }
        body { font-family: Arial, sans-serif; margin: 15px; background: #f4f6f9; }
        h2 { text-align: center; color: #333; }
        .card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .form-group { margin-bottom: 12px; }
        label { font-weight: bold; display: block; margin-bottom: 5px; }
        input, textarea { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .btn { padding: 10px 15px; border: none; border-radius: 4px; color: white; cursor: pointer; font-weight: bold; margin-right: 5px; }
        .btn-submit { background: var(--primary); }
        .btn-download { background: #17a2b8; float: right; margin-bottom: 10px; }
        .btn-edit { background: var(--warning); color: #000; padding: 4px 8px; }
        .btn-delete { background: var(--danger); padding: 4px 8px; }
        .btn-complete { background: var(--success); padding: 4px 8px; }
        
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; vertical-align: top; }
        th { background: #e9ecef; }
        .zh-text { color: #d9534f; font-weight: 500; display: block; margin-top: 4px; }
        .completed { background-color: #d4edda !important; }
    </style>
</head>
<body>

<div class="card">
    <h2>BÁO CÁO TIẾN ĐỘ SỬA CHỮA MÁY MÓC<br><span style="color:var(--primary);">设备维修进度汇报</span></h2>
    <button class="btn btn-download" onclick="exportToImage()">📸 Tải Ảnh Báo Cáo / 下载报告图片</button>
    
    <form id="repairForm">
        <input type="hidden" id="editIndex">
        <div class="form-group">
            <label>Tên / Mã Máy (设备名称/编号):</label>
            <input type="text" id="machineName" required>
        </div>
        <div class="form-group">
            <label>Nội Dung Sửa Chữa (维修内容):</label>
            <textarea id="contentVi" rows="2" placeholder="Nhập tiếng Việt..." required></textarea>
            <textarea id="contentZh" rows="2" placeholder="Tiếng Trung (中文)..."></textarea>
        </div>
        <div class="form-group">
            <label>Giải Pháp + Quy Cách Linh Kiện (解决方案+零件规格):</label>
            <textarea id="solutionVi" rows="2" placeholder="Nhập tiếng Việt..." required></textarea>
            <textarea id="solutionZh" rows="2" placeholder="Tiếng Trung (中文)..."></textarea>
        </div>
        <div class="form-group">
            <label>Thời Gian Dự Kiến Hoàn Thành (预计完成时间):</label>
            <input type="datetime-local" id="estimatedTime" required>
        </div>
        <button type="button" class="btn btn-submit" onclick="saveData()">Lưu Báo Cáo / 保存汇报</button>
    </form>
</div>

<div id="reportTableContainer">
    <table id="reportTable">
        <thead>
            <tr>
                <th>STT<br>序号</th>
                <th>Máy & Thời Gian Bắt Đầu<br>设备与开始时间</th>
                <th>Nội Dung<br>内容</th>
                <th>Giải Pháp & Linh Kiện<br>解决方案与零件规格</th>
                <th>Dự Kiến Hoàn Thành<br>预计完成时间</th>
                <th>Thao Tác<br>操作</th>
            </tr>
        </thead>
        <tbody id="tableBody"></tbody>
    </table>
</div>

<script>
    let reports = JSON.parse(localStorage.getItem('machineReports')) || [];

    function renderTable() {
        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';
        
        reports.forEach((item, index) => {
            const tr = document.createElement('tr');
            if (item.isCompleted) tr.classList.add('completed');
            
            tr.innerHTML = `
                <td>${index + 1}</td>
                <td><b>${item.machine}</b><br><small>${item.startTime}</small></td>
                <td>${item.contentVi}<span class="zh-text">${item.contentZh || ''}</span></td>
                <td>${item.solutionVi}<span class="zh-text">${item.solutionZh || ''}</span></td>
                <td>${item.estimatedTime}</td>
                <td>
                    ${!item.isCompleted ? `<button class="btn btn-complete" onclick="completeTask(${index})">✔ Hoàn thành</button>` : '<b>✓ Đã xong</b>'}
                    <button class="btn btn-edit" onclick="editData(${index})">✏ Sửa</button>
                    <button class="btn btn-delete" onclick="deleteData(${index})">🗑 Xóa</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        localStorage.setItem('machineReports', JSON.stringify(reports));
    }

    function saveData() {
        const index = document.getElementById('editIndex').value;
        const now = new Date();
        const startTimeStr = now.toLocaleTimeString('vi-VN') + ' ' + now.toLocaleDateString('vi-VN');
        
        const data = {
            machine: document.getElementById('machineName').value,
            startTime: index === "" ? startTimeStr : reports[index].startTime,
            contentVi: document.getElementById('contentVi').value,
            contentZh: document.getElementById('contentZh').value,
            solutionVi: document.getElementById('solutionVi').value,
            solutionZh: document.getElementById('solutionZh').value,
            estimatedTime: document.getElementById('estimatedTime').value.replace("T", " "),
            isCompleted: index === "" ? false : reports[index].isCompleted
        };

        if (index === "") {
            reports.push(data);
        } else {
            reports[index] = data;
            document.getElementById('editIndex').value = "";
        }

        document.getElementById('repairForm').reset();
        renderTable();
    }

    function completeTask(index) {
        const password = prompt("Nhập mật khẩu xác nhận hoàn thành (密码):");
        if (password === "230") {
            reports[index].isCompleted = true;
            renderTable();
        } else if (password !== null) {
            alert("Mật khẩu không đúng! / 密码错误！");
        }
    }

    function deleteData(index) {
        if (confirm("Bạn có chắc muốn xóa báo cáo này? / 确定要删除吗？")) {
            reports.splice(index, 1);
            renderTable();
        }
    }

    function editData(index) {
        const item = reports[index];
        document.getElementById('editIndex').value = index;
        document.getElementById('machineName').value = item.machine;
        document.getElementById('contentVi').value = item.contentVi;
        document.getElementById('contentZh').value = item.contentZh;
        document.getElementById('solutionVi').value = item.solutionVi;
        document.getElementById('solutionZh').value = item.solutionZh;
    }

    function exportToImage() {
        const actionCols = document.querySelectorAll('#reportTable th:last-child, #reportTable td:last-child');
        actionCols.forEach(col => col.style.display = 'none');

        html2canvas(document.getElementById('reportTableContainer')).then(canvas => {
            const link = document.createElement('a');
            link.download = `Bao_Cao_Sua_Chua_${new Date().toISOString().slice(0,10)}.png`;
            link.href = canvas.toDataURL();
            link.click();
            actionCols.forEach(col => col.style.display = '');
        });
    }

    renderTable();
</script>
</body>
</html>
