import os
import tkinter as tk
from tkinter import filedialog
from core.skill_registry import BaseSkill

class DocumentSkill(BaseSkill):
    TRIGGERS = ["analiza", "lee", "revisa"]

    def __init__(self, context):
        super().__init__(context)
        self.brain = context.brain
        self.event_bus = context.event_bus
        self.logger = context.logger

    def select_file(self):
        """Abre la ventana nativa de Windows para elegir un archivo."""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True) 
        
        ruta_archivo = filedialog.askopenfilename(
            title="Jarvis - Selecciona el documento a analizar",
            filetypes=[
                ("Todos los soportados", "*.pdf;*.docx;*.xlsx;*.txt;*.py;*.java;*.js;*.html;*.css;*.json;*.csv"),
                ("Documentos PDF", "*.pdf"),
                ("Word y Excel", "*.docx;*.xlsx"),
                ("Código y Texto", "*.txt;*.py;*.java;*.js;*.html;*.css;*.json;*.csv")
            ]
        )
        return ruta_archivo

    def execute(self, command, attachment_path=None):
        """Lee el archivo especificado o abre la ventana para elegirlo y lo analiza."""
        
        # Validación extra: asegurarnos de que la palabra "documento" o "archivo" esté presente
        if not ("documento" in command or "archivo" in command):
            return None

        if not attachment_path:
            self.event_bus.publish("SPEAK_REQUEST", {"text": "Claro, selecciona el archivo en la ventana que acaba de aparecer."})
            attachment_path = self.select_file()
        
        if not attachment_path:
            return "Operación cancelada. No seleccionaste ningún documento."
            
        filename = os.path.basename(attachment_path)
        ext = os.path.splitext(filename)[1].lower()
        texto_extraido = ""
        
        self.logger.info(f"Analizando documento: {filename}")

        try:
            # 1. TEXTO PLANO Y CÓDIGO
            if ext in ['.txt', '.py', '.java', '.js', '.html', '.css', '.json', '.csv']:
                with open(attachment_path, 'r', encoding='utf-8', errors='ignore') as f:
                    texto_extraido = f.read()
                    
            # 2. PDF
            elif ext == '.pdf':
                from pypdf import PdfReader
                reader = PdfReader(attachment_path)
                paginas = [page.extract_text() for page in reader.pages if page.extract_text()]
                texto_extraido = "\n".join(paginas)
                
            # 3. WORD
            elif ext == '.docx':
                import docx
                doc = docx.Document(attachment_path)
                texto_extraido = "\n".join([p.text for p in doc.paragraphs])
                
            # 4. EXCEL
            elif ext == '.xlsx':
                import openpyxl
                wb = openpyxl.load_workbook(attachment_path, data_only=True)
                lineas_excel = []
                for sheet in wb.sheetnames:
                    lineas_excel.append(f"--- Hoja: {sheet} ---")
                    ws = wb[sheet]
                    for row in ws.iter_rows(values_only=True):
                        if any(row):
                            lineas_excel.append(", ".join([str(c) if c is not None else "" for c in row]))
                texto_extraido = "\n".join(lineas_excel)
                
            else:
                return f"El formato {ext} no está soportado."
                
            if not texto_extraido.strip():
                return f"El archivo {filename} parece estar vacío o es una imagen sin texto seleccionable."
                
            # Protección contra archivos inmensos
            if len(texto_extraido) > 120000:
                texto_extraido = texto_extraido[:120000] + "\n... [Texto truncado] ..."

            super_prompt = (
                f"Analiza el contenido del archivo '{filename}':\n"
                f"========================================\n"
                f"{texto_extraido}\n"
                f"========================================\n"
                f"Teniendo ese archivo como contexto, responde a: {command}"
            )
            
            return self.brain.think(super_prompt)
            
        except Exception as e:
            self.logger.error(f"Error procesando documento {filename}: {e}")
            return f"Hubo un error al procesar el documento."