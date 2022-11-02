import cv2
import numpy as np
import os
import cv2
import shutil
from glob import glob
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError


def umbral_otsu(img):
    return cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]


def corregir_giro(img):
    invertida = cv2.bitwise_not(img)
    thresh = cv2.threshold(
        invertida, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )[1]
    coords = np.column_stack(np.where(thresh > 0))
    angulo = cv2.minAreaRect(coords)[-1]
    if angulo > 45:
        angulo = 90 - angulo
    else:
        angulo = -angulo
    (h, w) = img.shape[:2]
    centro = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(centro, angulo, 1.0)
    rotada = cv2.warpAffine(
        img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return rotada


def procesar_img_3(img, enderezar=False):
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gris = umbral_otsu(gris)
    if enderezar:
        gris = corregir_giro(gris)
    return gris


def verificar_crear_dir(ubicacion_directorio):
    if not os.path.exists(ubicacion_directorio):
        os.makedirs(ubicacion_directorio)


class OCR:
    def __init__(
        self,
        preprocesamiento,
        lenguaje,
        oem,
        psm,
        dir_temporal="temp_pags/",
        enderezar=False,
    ):

        self.preprocesamiento = preprocesamiento
        self.dir_temporal = dir_temporal
        self.lenguaje = 'eng'
        self.oem = oem
        self.psm = psm
        self.enderezar = enderezar

    def imagen_a_texto(self, ubicacion_imagen):
        """
        Se encarga de leer el texto de archivos de tipo imagen, con \
        extensión 'png', 'jpg' o 'jpeg', luego de aplicar el \
        preprocesamiento definido al iniciar la clase OCR
        :param ubicacion_imagen: (string). Ruta de la imagen que se desea leer
        :return: (string). Texto del archivo tipo imagen leído con la clase OCR
        """
        # Cargar la imagen de entrada
        imagen = cv2.imread(ubicacion_imagen)
        # Se define el preprocesamiento a aplicar
        # si el número está fuera de rango, no se aplica
        # ningún preprocesmiento
        if 0 < self.preprocesamiento < 6:
            imagen = eval(
                f"procesar_img_{self.preprocesamiento}(imagen, {self.enderezar})"
            )
        # Se guarda la imagen en un archivo temporal
        nombre_archivo = "{}.png".format(os.getpid())
        cv2.imwrite(nombre_archivo, imagen)
        # Se establecen las opciones para el OCR
        config = "-l {} --psm {} --oem {}".format(
            self.lenguaje, self.psm, self.oem
        )
        # Se carga la imagen como un objeto PIL/Pillow image y se aplica el OCR
        texto = pytesseract.image_to_string(
            Image.open(nombre_archivo), config=config
        )
        # Borrar el archivo de imagen preprocesada
        os.remove(nombre_archivo)
        return str(texto)

    def pdf_a_imagen(self, ubicacion_pdf):
        """Se encarga de transformar archivos PDF a imagen
        :param ubicacion_imagen: (string). Ruta del archivo PDF
        """
        tempo_dir = self.dir_temporal + "/tempo/"
        verificar_crear_dir(self.dir_temporal)
        verificar_crear_dir(tempo_dir)
        try:
            paginas = convert_from_path(
                ubicacion_pdf, thread_count=8, output_folder=tempo_dir
            )
        except PDFInfoNotInstalledError:
            print("Poppler is not properlly installed, or it's location is not defined as a environment variable")         
            exit(1)
        # Counter to store images of each page of PDF to image
        countador_img = 0
        for pagina in paginas:
            countador_img += 1
            archivo = (
                self.dir_temporal
                + "/pagina_"
                + str(countador_img).zfill(7)
                + ".jpg"
            )
            pagina.save(archivo, "JPEG")
        # Borrar folder temporal
        shutil.rmtree(tempo_dir)

    def pdf_a_texto(self, ubicacion_pdf, borrar_folder=True):
        self.pdf_a_imagen(ubicacion_pdf)
        imagenes = sorted(glob(self.dir_temporal + "/*.jpg"))
        paginas = []
        for imagen in imagenes:
            pagina = self.imagen_a_texto(imagen)
            paginas.append(pagina)
        if borrar_folder:
            shutil.rmtree(self.dir_temporal)
        return paginas


def leer_pdf(
        ubicacion_archivo=None,
        preprocesamiento=3,
        lenguaje='eng',
        oem=2,
        psm=3,
        password=None,
        enderezar=False,
    ):
    print('I am here!')
    recog = OCR(preprocesamiento, lenguaje, oem, psm, enderezar=enderezar)
    paginas = recog.pdf_a_texto(ubicacion_archivo)
    return paginas