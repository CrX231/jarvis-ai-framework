import os
import docx
import xlsxwriter
from pptx import Presentation

class CreativeSkill:
    def __init__(self):
        self.output_folder = "documentos_generados"
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def _ask_gemini_deep(self, prompt, brain):
        """Petición especial a Gemini para contenido extenso y estructurado."""
        try:
            response = brain.client.models.generate_content(
                model=brain.model_id,
                contents=prompt
            )
            return response.text.replace("*", "")
        except Exception as e:
            return f"Error de IA: {e}"

    def create_word(self, topic, brain):
        print(f"[Creative] Redactando monografía sobre: {topic}")
        prompt = f"Escribe una monografía extensa y profesional sobre '{topic}'. Estructura con 'H1: Título' y 'H2: Subtítulo'. No uses markdown."
        contenido = self._ask_gemini_deep(prompt, brain)
        
        doc = docx.Document()
        
        # Corrección aplicada: usamos add_heading con level=0 para el título principal
        doc.add_heading(topic.upper(), level=0)
        
        for linea in contenido.split('\n'):
            linea = linea.strip()
            if linea.startswith("H1:"):
                doc.add_heading(linea.replace("H1:", ""), level=1)
            elif linea.startswith("H2:"):
                doc.add_heading(linea.replace("H2:", ""), level=2)
            elif linea:
                doc.add_paragraph(linea)
        
        filename = f"Monografia_{topic.replace(' ', '_')[:20]}.docx"
        path = os.path.join(self.output_folder, filename)
        doc.save(path)
        
        # Abre el archivo automáticamente en Windows
        os.startfile(path)
        
        return f"Documento Word creado y abierto con éxito: {filename}"

    def create_excel(self, topic, brain):
        print(f"[Creative] Generando hoja de cálculo sobre: {topic}")
        prompt = f"Genera una lista de datos para un Excel sobre '{topic}'. Devuelve los datos en formato CSV (separados por comas), máximo 10 filas. Solo los datos, nada de texto extra."
        datos_raw = self._ask_gemini_deep(prompt, brain)
        
        filename = f"Excel_{topic.replace(' ', '_')[:20]}.xlsx"
        path = os.path.join(self.output_folder, filename)
        
        workbook = xlsxwriter.Workbook(path)
        worksheet = workbook.add_worksheet()
        
        bold = workbook.add_format({'bold': True, 'bg_color': '#D4AF37', 'font_color': 'white'})
        
        for r, linea in enumerate(datos_raw.split('\n')):
            if not linea.strip(): continue
            columnas = linea.split(',')
            for c, valor in enumerate(columnas):
                if r == 0:
                    worksheet.write(r, c, valor.strip(), bold)
                else:
                    worksheet.write(r, c, valor.strip())
        
        workbook.close()
        
        # Abre el archivo automáticamente en Windows
        os.startfile(path)
        
        return f"Hoja de Excel creada y abierta con éxito: {filename}"

    def create_pptx(self, topic, brain):
        print(f"[Creative] Diseñando presentación sobre: {topic}")
        prompt = f"Genera el esquema para una presentación de 5 diapositivas sobre '{topic}'. Para cada diapositiva escribe 'T: Titulo' y luego 'C: Contenido'. No uses markdown."
        esquema = self._ask_gemini_deep(prompt, brain)
        
        prs = Presentation()
        
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        slide.shapes.title.text = topic.upper()
        slide.placeholders[1].text = "Generado por Jarvis AI"

        current_slide = None
        for linea in esquema.split('\n'):
            linea = linea.strip()
            if linea.startswith("T:"):
                bullet_slide_layout = prs.slide_layouts[1]
                current_slide = prs.slides.add_slide(bullet_slide_layout)
                current_slide.shapes.title.text = linea.replace("T:", "").strip()
            elif linea.startswith("C:") and current_slide:
                current_slide.placeholders[1].text += linea.replace("C:", "").strip() + "\n"

        filename = f"Presentacion_{topic.replace(' ', '_')[:20]}.pptx"
        path = os.path.join(self.output_folder, filename)
        prs.save(path)
        
        # Abre el archivo automáticamente en Windows
        os.startfile(path)
        
        return f"Presentación PowerPoint creada y abierta: {filename}"