import os
import glob
from pdf2image import convert_from_path
from PyPDF2 import PdfFileWriter, PdfFileReader


def convert_pdf_first_page_to_image(pdf_input_file, image_output_file):
    dpi = 200
    pages = convert_from_path(pdf_input_file, dpi)
    first_page = pages[0]
    first_page.save(image_output_file, 'JPEG')

def convert_pdfs_to_image(pdfs_path):
    filtered_path = glob.glob(pdfs_path + '*.pdf')
    for pdf in filtered_path:
        image = os.path.splitext(pdf)[0] + '.jpg'
        convert_pdf_first_page_to_image(pdf, image)
        print(image)

def rename_contestations(dir):
    for filename in os.listdir(dir):
        src = dir + filename
        dst = dir + filename[25:33] + ".pdf"
        os.rename(src, dst) 

def keep_pdf_first_page(dir):
    filtered_path = glob.glob(dir + '*.pdf')
    for pdf in filtered_path:
        with open(pdf, "rb") as inputStream:
            inputpdf = PdfFileReader(inputStream)
            output = PdfFileWriter()
            output.addPage(inputpdf.getPage(0))
            new_name = pdf + ".first.pdf"
            with open(new_name, "wb") as outputStream:
                output.write(outputStream)
        os.remove(pdf)
        os.rename(new_name, pdf) 

dir = 'C:/pdfs/'
keep_pdf_first_page(dir)
rename_contestations(dir)
convert_pdfs_to_image(dir)