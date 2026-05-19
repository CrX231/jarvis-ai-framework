import os
import discord
import asyncio
import threading
from dotenv import load_dotenv

class DiscordBot(discord.Client):
    def __init__(self, command_handler):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.command_handler = command_handler 

    async def on_ready(self):
        print(f'\n[Discord] Enlace satelital establecido. Conectado como {self.user}')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if self.user in message.mentions or isinstance(message.channel, discord.DMChannel):
            comando = message.content.replace(f'<@{self.user.id}>', '').strip()
            
            # Detectar y descargar archivos adjuntos si existen
            attachment_path = None
            if message.attachments:
                attachment = message.attachments[0]
                folder = "documentos"
                if not os.path.exists(folder):
                    os.makedirs(folder)
                
                attachment_path = os.path.join(folder, attachment.filename)
                print(f"[Discord] Descargando archivo adjunto: {attachment.filename}...")
                await attachment.save(attachment_path)

            # Si envió un archivo vacío sin texto, le asignamos una orden por defecto
            if not comando and attachment_path:
                comando = "analiza este archivo"

            if comando:
                print(f"[Discord] Orden recibida de {message.author}: {comando}")
                async with message.channel.typing():
                    # Pasamos el comando y la ruta del archivo adjunto al enrutador maestro
                    respuesta = self.command_handler(comando, attachment_path=attachment_path)
                    await message.channel.send(respuesta)

class DiscordInterface:
    def __init__(self, command_handler):
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")
        self.bot = DiscordBot(command_handler)

    def _start_bot(self):
        if not self.token:
            print("[Error] No se encontró DISCORD_TOKEN en .env")
            return
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.bot.start(self.token))
        except Exception as e:
            print(f"[Error de Discord] {e}")

    def run_in_background(self):
        thread = threading.Thread(target=self._start_bot, daemon=True)
        thread.start()