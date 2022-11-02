# django_pdfOCR

## New requirements

    opencv-python==4.6.0.66
    pytesseract==0.3.7
    pdf2image==1.16.0


opencv-python, pytesseract and pdf2image are used to transform the PDF file into images and then apply OCR.

I have not tested the heroku scheduler properly. The function that should run is called "apply_OCR" and it is defined in BP/management/commands/ocr_cron.py

    ** Keep in mind I'm using recursion when the OCR finish succesfully

I created a view to test the OCR manually (this view can be deleted) (it might take some time while it process all the documents, you should be able to see some prints in the console)

    http://127.0.0.1:8000/BP/apply_ocr_manual_trigger/

The uploaded files can have for status: 

    Pending (Default)
    Processing
    Done
    Error

after N attempts (this can be set in line 34 of ocr_cron.py file) the document status will be set as 'Error', and it will be ignored in the future calls of the OCR function.

---
## Install poppler and tesseract

You'll nedd to install poppler and tesseract, you can follow this [instructions for windows](https://ucd--dnp-github-io.translate.goog/ConTexto/versiones/master/instalacion/instalacion_popple_teseract_windows.html?_x_tr_sl=es&_x_tr_tl=en&_x_tr_hl=es&_x_tr_pto=wapp#instalacion-poppler-tesseract-windows)

Download the file 'eng.traineddata' from [GitHub](https://github.com/tesseract-ocr/tessdata/blob/main/eng.traineddata) and update the english corpus of tesseract to get better results.


