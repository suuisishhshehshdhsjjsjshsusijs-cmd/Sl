from pdf_generator import generate_medical_pdf
import os

test_data = {
    'full_name_quad': 'محمد أحمد علي حسن',
    'work_place': 'شركة الاتصالات السعودية',
    'id_number': '1029384756',
    'birth_date': '1990-01-01',
    'job_title': 'مهندس برمجيات',
    'nationality': 'سعودي',
    'region': 'الرياض',
    'hospital': 'مستشفى الملك فيصل التخصصي',
    'leave_date': '2024-01-01'
}

try:
    print("جاري محاولة توليد ملف PDF تجريبي...")
    path = generate_medical_pdf(999, test_data)
    print(f"تم التوليد بنجاح في المسار: {path}")
except Exception as e:
    print(f"حدث خطأ أثناء التوليد: {e}")
