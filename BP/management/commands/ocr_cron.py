from django.core.management.base import BaseCommand
from BP.models import Doc, ocr_Page
from BP.ocr_utils import *

# http://127.0.0.1:8000/BP/inbox/50/43/

def apply_OCR():
    status_filter = ['Done', 'Error']
    document = Doc.objects.order_by('created').exclude(ocr_status__in=status_filter).first()
    if document != None:
        try:
            if document.ocr_status == 'Pending':
                print('I am starting')
                document.ocr_status = 'Processing'
                document.ocr_tries += 1
                document.save()
                print('Now going Inside leet pdf')
                print(f'Document: {str(document)} - {document.ocr_status} - {document.ocr_tries} - {document.upload.path}')
                print('Now going!!')
                text = leer_pdf(document.upload.path)
                for idx, page_text in enumerate(text):
                    page_text_clean = ' '.join(page_text.splitlines())
                    page_text_clean = ' '.join(page_text_clean.split())
                    page = ocr_Page(page_number=idx+1, text=page_text_clean, document=document)
                    page.save()

                document.ocr_status = 'Done'
                document.save()
                apply_OCR()

            elif document.ocr_status == 'Processing':
                # validates how many tries should occur before labeling the file with an error, 24 * 5 min = 120 min = 2 hours. 
                # In this case if the proccessing of a file lasts more than 2 hours it will be labeled as an Error and it will be ignored.
                # if document.ocr_tries == 24:
                if document.ocr_tries == 5:
                    document.ocr_status = 'Error'
                else:
                    document.ocr_tries += 1
                
                document.save()

        except Exception as e:
            print(f'Error: {e}')

class Command(BaseCommand):
    def handle(self, *args, **options):
        apply_OCR()