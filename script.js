$(document).ready(function() {
    // تعيين تاريخ الاستلام الافتراضي في مودال الطلب الجديد
    $('#newRequestModal input[name="receive_date"]').val(new Date().toISOString().slice(0,10));
    
    // حساب أيام العمل عند تغيير تاريخ الرد
    $('#responseDateInput').on('change', function() {
        let receiveDate = $('input[name="receive_date"]').val();
        let responseDate = $(this).val();
        if(receiveDate && responseDate) {
            $.get('/calculate_workdays', {start: receiveDate, end: responseDate}, function(res) {
                $('#workdaysDisplay').val(res.workdays);
            }).fail(function() { $('#workdaysDisplay').val('خطأ'); });
        } else {
            $('#workdaysDisplay').val('0');
        }
    });
    // نضيف نقطة نهاية /calculate_workdays في app.py (سأضيفها)
    
    // إرسال نموذج الطلب الجديد
    $('#newRequestForm').on('submit', function(e) {
        e.preventDefault();
        $.post('/add_request', $(this).serialize(), function(res) {
            if(res.success) {
                $('#newRequestModal').modal('hide');
                showToast('success', res.message);
                loadRequestsTable(); // تحديث الجدول
                updateSelects();     // تحديث القوائم المنسدلة (احتياطي)
            } else {
                showToast('danger', res.message);
            }
        });
    });
    
    // بحث وتصفية
    $('#applyFilterBtn').on('click', function() {
        loadRequestsTable();
    });
    
    // حذف عنصر من الجداول المرجعية
    $(document).on('click', '.delete-item', function() {
        let table = $(this).data('table');
        let id = $(this).data('id');
        if(confirm('هل أنت متأكد من الحذف؟')) {
            $.ajax({url: `/delete_item/${table}/${id}`, type: 'DELETE', success: function(res) {
                showToast('success', res.message);
                // إعادة تحميل الصفحة الإدارية أو تحديث القسم
                location.reload();
            }});
        }
    });
    
    // إضافة عنصر واحد
    $('.add-single').on('click', function() {
        let table = $(this).data('table');
        let inputId = $(this).data('input');
        let name = $('#'+inputId).val();
        if(!name) return;
        $.post(`/add_item/${table}`, {name: name}, function(res) {
            showToast(res.success ? 'success' : 'danger', res.message);
            if(res.success) location.reload();
        });
    });
    
    // إضافة عدة عناصر
    $('.add-bulk').on('click', function() {
        let table = $(this).data('table');
        let inputId = $(this).data('input');
        let items = $('#'+inputId).val();
        if(!items) return;
        $.post(`/add_multiple_items/${table}`, {items: items}, function(res) {
            showToast(res.success ? 'success' : 'danger', res.message);
            if(res.success) location.reload();
        });
    });
    
    // تحميل الإحصائيات عند فتح التبويب
    $('#statsTab').on('shown.bs.tab', function() {
        loadStatistics();
    });
    
    function loadRequestsTable() {
        let receiver = $('#filterReceiver').val();
        let department = $('#filterDepartment').val();
        let date_from = $('#filterDateFrom').val();
        let date_to = $('#filterDateTo').val();
        $.get('/filter_requests', {receiver, department, date_from, date_to}, function(data) {
            let html = '';
            if(data.length === 0) {
                html = '<div class="alert alert-info text-center">لا توجد طلبات</div>';
            } else {
                html = '<div class="table-responsive"><table class="table table-striped"><thead><tr><th>#</th><th>القسم</th><th>الخدمة</th><th>النظام</th><th>وسيلة الطلب</th><th>تاريخ الاستلام</th><th>تاريخ الرد</th><th>التفاصيل</th><th>الموظف</th><th>أيام العمل</th></tr></thead><tbody>';
                $.each(data, function(i,req) {
                    html += `<tr><td>${req.id}</td><td>${req.department}</td><td>${req.service}</td><td>${req.system}</td><td>${req.request_via}</td><td>${req.receive_date}</td><td>${req.response_date || ''}</td><td>${req.details || ''}</td><td>${req.receiver}</td><td>${req.work_days || 0}</td></tr>`;
                });
                html += '</tbody></table></div>';
            }
            $('#requestsTableContainer').html(html);
        });
    }
    
    function updateSelects() {
        $.get('/get_select_data', function(data) {
            // تحديث القوائم في المودال (اختصار)
            let deptSelect = $('select[name="department"]');
            deptSelect.empty();
            $.each(data.departments, function(i,d) { deptSelect.append(`<option value="${d.name}">${d.name}</option>`); });
            // ... وكذلك باقي القوائم
        });
    }
    
    function loadStatistics() {
        $.get('/get_statistics', function(res) {
            let labels = [], counts = [];
            $.each(res.stats, function(i,s) {
                labels.push(s.receiver);
                counts.push(s.count);
            });
            // رسم بياني باستخدام Chart.js
            let ctx = $('#statsChart')[0].getContext('2d');
            new Chart(ctx, { type: 'bar', data: { labels: labels, datasets: [{ label: 'عدد الطلبات', data: counts, backgroundColor: 'rgba(54, 162, 235, 0.5)' }] } });
            $('#statsData').html(`<div class="alert alert-info">إجمالي الطلبات: ${res.total}</div><ul>${labels.map((l,i)=>`<li>${l}: ${counts[i]}</li>`).join('')}</ul>`);
        });
    }
    
    function showToast(type, message) {
        // يمكن استخدام toasts من Bootstrap
        let toastHtml = `<div class="toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3" role="alert"><div class="d-flex"><div class="toast-body">${message}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>`;
        $('body').append(toastHtml);
        let toastEl = $('.toast').last();
        let bsToast = new bootstrap.Toast(toastEl[0], {autohide: true, delay: 3000});
        bsToast.show();
        toastEl.on('hidden.bs.toast', function() { $(this).remove(); });
    }
    
    // حساب أيام العمل عبر AJAX (نحتاج نقطة نهاية إضافية في app.py)
    $.get('/calculate_workdays', function() {}); // مجرد استدعاء
});
