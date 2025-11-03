import cv2
import numpy as np
import pytesseract
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.uix.popup import Popup
from kivy.uix.label import Label
import os

# 🔧 (solo necesario en PC Windows)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class CamaraCartas(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.image = Image()
        self.add_widget(self.image)
        self.boton = Button(
            text="📸 Tomar foto y contar cartas CERTIFICADAS",
            size_hint=(1, 0.2)
        )
        self.boton.bind(on_press=self.tomar_foto)
        self.add_widget(self.boton)
        self.cam = cv2.VideoCapture(0)

        # 📂 Carpeta accesible en Android
        self.directorio_resultados = "/storage/emulated/0/CartasCertificadas"
        if not os.path.exists(self.directorio_resultados):
            try:
                os.makedirs(self.directorio_resultados)
                print(f"📁 Carpeta creada: {self.directorio_resultados}")
            except Exception as e:
                print(f"⚠️ No se pudo crear la carpeta: {e}")

    def tomar_foto(self, instance):
        ret, frame = self.cam.read()
        if not ret:
            self.mostrar_popup("Error", "❌ No se pudo acceder a la cámara.")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 120, 255, cv2.THRESH_BINARY_INV)
        contornos, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        posibles_cartas = [c for c in contornos if cv2.contourArea(c) > 1000]
        certificadas = 0

        for c in posibles_cartas:
            x, y, w, h = cv2.boundingRect(c)
            roi = frame[y:y+h, x:x+w]
            texto = pytesseract.image_to_string(roi, lang='spa').upper()

            if "CERTIFICADO" in texto:
                certificadas += 1
                color = (0, 255, 0)
                label = "CERTIFICADO"
            else:
                color = (0, 0, 255)
                label = "NO"

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        total = len(posibles_cartas)
        self.guardar_registro(total, certificadas)

        # 🪟 Mostrar resultado en popup
        mensaje = f"📬 Detectadas: {total}\n📦 Certificadas: {certificadas}"
        self.mostrar_popup("Resultado", mensaje)

        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(
            size=(frame.shape[1], frame.shape[0]), colorfmt="bgr")
        texture.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")
        self.image.texture = texture

    def guardar_registro(self, total, certificadas):
        """Guarda los resultados en una carpeta visible del móvil."""
        fecha = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        linea = f"{fecha} Detectadas: {total} sobres, {certificadas} certificados.\n"

        archivo = os.path.join(self.directorio_resultados, "resultados.txt")
        try:
            with open(archivo, "a", encoding="utf-8") as f:
                f.write(linea)
            print(f"📝 Resultado guardado en: {archivo}")
        except Exception as e:
            print(f"⚠️ Error al guardar el resultado: {e}")

    def mostrar_popup(self, titulo, mensaje):
        """Muestra una ventana emergente en pantalla."""
        popup = Popup(
            title=titulo,
            content=Label(text=mensaje, font_size='20sp'),
            size_hint=(0.8, 0.4)
        )
        popup.open()


class ContarCartasApp(App):
    def build(self):
        return CamaraCartas()


if __name__ == "__main__":
    ContarCartasApp().run()
