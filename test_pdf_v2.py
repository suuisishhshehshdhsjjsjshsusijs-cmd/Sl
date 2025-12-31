from fpdf import FPDF

def test_arabic_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    try:
        text = "محمد أحمد علي حسن"
        print(f"محاولة كتابة نص عربي: {text}")
        pdf.cell(0, 10, text, 1, 1, 'C')
        pdf.output("test_arabic.pdf")
        print("تم توليد الملف بنجاح (تقنياً).")
    except Exception as e:
        print(f"حدث خطأ: {e}")

if __name__ == "__main__":
    test_arabic_pdf()
