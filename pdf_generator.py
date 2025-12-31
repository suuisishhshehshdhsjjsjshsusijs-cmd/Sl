import os
from fpdf import FPDF
import qrcode
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

class MedicalPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_id = 0
        # محاولة إضافة خط يدعم العربية إذا كان موجوداً
        # ملاحظة: يجب توفير ملف الخط في مجلد fonts عند الاستضافة
        self.font_path = os.path.join(os.path.dirname(__file__), "fonts", "Amiri-Regular.ttf")
        self.font_bold_path = os.path.join(os.path.dirname(__file__), "fonts", "Amiri-Bold.ttf")
        
        if os.path.exists(self.font_path):
            self.add_font("Amiri", "", self.font_path)
            self.add_font("Amiri", "B", self.font_bold_path)
            self.arabic_font = "Amiri"
        else:
            self.arabic_font = "Helvetica" # تراجع للخط الافتراضي إذا لم يوجد الخط العربي

    def header(self):
        self.rect(5, 5, 200, 287)
        self.set_font('Helvetica', 'B', 18)
        self.cell(0, 15, 'OMAR RAJOUN PLATFORM FOR MEDICAL LEAVE', 0, 1, 'C')
        self.set_font('Helvetica', 'I', 10)
        self.cell(0, 5, 'Official Digital Medical Certificate System', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Verified Document ID: {self.doc_id} - Omar Rajoun Platform', 0, 0, 'C')

    def fix_arabic(self, text):
        if not text: return ""
        # إعادة تشكيل الحروف العربية وتعديل الاتجاه (RTL)
        reshaped_text = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped_text)
        return bidi_text

def generate_medical_pdf(request_id, data):
    # استخدام التوجيه من اليمين لليسار في fpdf2 إذا لزم الأمر
    pdf = MedicalPDF()
    pdf.doc_id = request_id
    pdf.add_page()
    
    # معلومات الشهادة
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(40, 8, 'Certificate ID:', 0, 0)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 8, str(request_id), 0, 1)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(40, 8, 'Issue Date:', 0, 0)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 8, datetime.now().strftime('%Y-%m-%d %H:%M'), 0, 1)
    
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # بيانات المريض والعمل
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 10, 'PATIENT & EMPLOYMENT DETAILS', 0, 1)
    
    # تعريف الحقول مع دعم الترجمة للعربية إذا لزم الأمر
    fields = [
        ('Full Name (Quad):', data['full_name_quad']),
        ('Work Place:', data['work_place']),
        ('ID Number:', data['id_number']),
        ('Birth Date:', data['birth_date']),
        ('Job Title:', data['job_title']),
        ('Nationality:', data['nationality']),
        ('Region:', data['region']),
        ('Hospital:', data['hospital']),
        ('Leave Date:', data['leave_date'])
    ]
    
    for label, value in fields:
        # تسمية الحقل بالإنجليزية
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(50, 9, label, 1, 0)
        
        # القيمة (قد تكون بالعربية)
        if pdf.arabic_font == "Amiri":
            pdf.set_font("Amiri", "", 12)
            processed_value = pdf.fix_arabic(value)
            # استخدام محاذاة اليمين للنصوص العربية
            pdf.cell(0, 9, processed_value, 1, 1, 'R')
        else:
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(0, 9, str(value), 1, 1)
    
    pdf.ln(15)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, 'Authorized Digital Approval', 0, 1, 'R')
    pdf.set_font('Helvetica', 'I', 10)
    pdf.cell(0, 10, 'Omar Rajoun Medical Board', 0, 1, 'R')
    
    # QR Code
    qr_data = f"Verify: https://omar-rajoun.com/v/{request_id}\nName: {data['full_name_quad']}\nID: {data['id_number']}"
    qr = qrcode.make(qr_data)
    qr_path = f"qr_{request_id}.png"
    qr.save(qr_path)
    pdf.image(qr_path, x=10, y=230, w=35)
    
    os.makedirs("generated_pdfs", exist_ok=True)
    file_path = f"generated_pdfs/medical_leave_{request_id}.pdf"
    pdf.output(file_path)
    
    if os.path.exists(qr_path):
        os.remove(qr_path)
        
    return file_path
