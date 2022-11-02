# from urllib.request import Request, urlopen
import io
from PyPDF2 import PdfFileWriter, PdfFileReader
from fpdf import FPDF
import tempfile
from django.core.files import File

def createWaterMark(X=5, Y=5, Font='Helvetica', Size=12, LineSpacing=6, Text=[None, None, None, None, None, None]):
    pdf = FPDF(format='Letter')
    pdf.add_page()
    
    # https://pyfpdf.readthedocs.io/en/latest/reference/add_font/index.html
    # https://www.1001freefonts.com/
    
    pdf.set_font(Font, size=Size)    
    pdf.set_text_color(0,0,0)

    if Text[0] is not None:
        pdf.text(x=X, y=(Y+LineSpacing*0), txt=Text[0])
    
    if (Text[1] is not None) and (Text[2] is not None):
        pdf.text(x=X, y=(Y+LineSpacing*1), txt=f"{Text[1]}, {Text[2]}")
    elif (Text[1] is None) and (Text[2] is not None):
        pdf.text(x=X, y=(Y+LineSpacing*1), txt=f"{Text[2]}")
    elif (Text[1] is not None) and (Text[2] is None):
        pdf.text(x=X, y=(Y+LineSpacing*1), txt=f"{Text[1]}")

    if (Text[3] is not None) and (Text[4] is not None) and (Text[5] is not None):
        pdf.text(x=X, y=(Y+LineSpacing*2), txt=f"{Text[3]}, {Text[4]}, {Text[5]}")    
    elif (Text[3] is None) and (Text[4] is not None) and (Text[5] is not None):
        pdf.text(x=X, y=(Y+LineSpacing*2), txt=f"{Text[4]}, {Text[5]}")
    elif (Text[3] is not None) and (Text[4] is None) and (Text[5] is not None):
        pdf.text(x=X, y=(Y+LineSpacing*2), txt=f"{Text[3]}, {Text[5]}")
    elif (Text[3] is not None) and (Text[4] is not None) and (Text[5] is None):
        pdf.text(x=X, y=(Y+LineSpacing*2), txt=f"{Text[3]}, {Text[4]}")
    elif (Text[3] is not None) and (Text[4] is None) and (Text[5] is None):
        pdf.text(x=X, y=(Y+LineSpacing*2), txt=f"{Text[3]}")
    elif (Text[3] is None) and (Text[4] is not None) and (Text[5] is None):
        pdf.text(x=X, y=(Y+LineSpacing*2), txt=f"{Text[4]}")
    elif (Text[3] is None) and (Text[4] is None) and (Text[5] is not None):
        pdf.text(x=X, y=(Y+LineSpacing*2), txt=f"{Text[5]}")

    return pdf.output(dest='S')


def create_stamped_file(X=5, Y=5, Font='Helvetica', Size=12, target_page=1, file_path=None, LineSpacing=6, Text=[None, None, None, None, None, None], instance=None, HIPAA_file=False):
    
    # remote_file = urlopen(Request(file_path)).read()
    # input = PdfFileReader(io.BytesIO(remote_file))
    output = PdfFileWriter()

    if HIPAA_file:
        print(Text)
        try:
            with instance.upload.open() as data_file:
                input = PdfFileReader(data_file)            
                memory_watermark = createWaterMark(X, Y, Font, Size, LineSpacing, Text)
                watermark = PdfFileReader(io.BytesIO(memory_watermark))

                for page in range(0,input.getNumPages()):
                    current_page = input.getPage(page)
                    if page == target_page - 1:
                        current_page.mergePage(watermark.getPage(0))

                    output.addPage(current_page)

                temp_file = tempfile.NamedTemporaryFile(delete=True)
                output.write(temp_file)
                temp_file.flush()

                instance_upload_name = instance.upload.name.split("/")[1].split(".pdf")[0]
                instance.upload.save(f'{instance_upload_name}___stamped.pdf', File(temp_file))
                temp_file.close()
        except Exception as e:
            print(e)

    else:
        try:
            with instance.template.open() as data_file:
                input = PdfFileReader(data_file)            
                memory_watermark = createWaterMark(X, Y, Font, Size, LineSpacing, Text)
                watermark = PdfFileReader(io.BytesIO(memory_watermark))

                for page in range(0,input.getNumPages()):
                    current_page = input.getPage(page)
                    if page == target_page - 1:
                        current_page.mergePage(watermark.getPage(0))

                    output.addPage(current_page)

                temp_file = tempfile.NamedTemporaryFile(delete=True)
                output.write(temp_file)
                temp_file.flush()

                instance_template_name = instance.template.name.split("/")[1].split(".pdf")[0]
                instance.template_stamped.save(f'{instance_template_name}_stamped.pdf', File(temp_file))
                temp_file.close()
        except Exception as e:
            print(e)