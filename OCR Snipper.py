import sys
import pytesseract
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QRubberBand
from PyQt5.QtCore import Qt, QRect, QSize, QBuffer
from PyQt5.QtGui import QPixmap
import pyperclip
from PIL import Image, ImageOps, ImageEnhance
from io import BytesIO


# Configure Tesseract path (adjust this based on your installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class SnippingTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.start_pos = None
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)

    def initUI(self):
        self.setWindowTitle('OCR Snipper')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen = QApplication.primaryScreen()
        self.screenshot = screen.grabWindow(QApplication.desktop().winId())
        self.setGeometry(self.screenshot.rect())
        label = QLabel(self)
        label.setPixmap(self.screenshot)
        label.setGeometry(self.screenshot.rect())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Capture the start position of the drag
            self.start_pos = event.pos()
            self.rubber_band.setGeometry(QRect(self.start_pos, QSize()))
            self.rubber_band.show()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            # Update the rubber band geometry as the mouse moves
            self.rubber_band.setGeometry(QRect(self.start_pos, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubber_band.hide()
            rect = self.rubber_band.geometry()
            self.extract_text_from_snip(rect)
            self.screenshot = None
            self.close()

    def preprocess_image(self, pil_image):
        # Convert to grayscale
        pil_image = ImageOps.grayscale(pil_image)
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(2.0)
        # Apply binary thresholding
        pil_image = pil_image.point(lambda x: 0 if x < 128 else 255, '1')
        return pil_image

    def extract_text_from_snip(self, rect):
        cropped_image = self.screenshot.copy(rect)
        # Convert QPixmap to QByteArray
        q_buffer = QBuffer()
        q_buffer.open(QBuffer.ReadWrite)
        cropped_image.save(q_buffer, "PNG")
        byte_array = q_buffer.data()
        q_buffer.close()

        # Convert QByteArray to Pillow Image
        pil_image = Image.open(BytesIO(byte_array))
        pil_image = self.preprocess_image(pil_image)

        # Configure Tesseract for faster recognition
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(pil_image, config=custom_config)
        pyperclip.copy(text)
        print("Text copied to clipboard:\n", text)

        # Release memory
        del pil_image
        del cropped_image
        del q_buffer


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = SnippingTool()
    tool.showFullScreen()
    sys.exit(app.exec_())
