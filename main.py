import imaplib
import email
from email.header import decode_header
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Configuración de tu correo
EMAIL = 'luismi003022@gmail.com'
PASSWORD = 'unsn xfdz qaob uglx'
IMAP_SERVER = 'imap.gmail.com'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    correo = request.form.get('email')
    if not correo:
        return jsonify({'success': False, 'message': 'No se proporcionó un correo.'})

    try:
        # Conexión al servidor IMAP
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox')

        # Buscar correos específicos
        status, messages = mail.search(None, f'(TO "{correo}")')
        messages = messages[0].split()

        if not messages:
            return jsonify({'success': False, 'message': f'No se encontraron correos para {correo}.'})

        # Obtener el último mensaje
        latest_email_id = messages[-1]
        status, data = mail.fetch(latest_email_id, '(RFC822)')
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        # Extraer y decodificar asunto
        subject = email_message['subject']
        decoded_subject = decode_header(subject)
        subject = ''.join(
            part.decode(encoding if encoding else 'utf-8', errors="ignore") if isinstance(part, bytes) else part
            for part, encoding in decoded_subject

        )


        # Extraer cuerpo del correo electrónico
        html_content = None

        if email_message.is_multipart():
            # Recorrer las partes del correo
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Ignorar archivos adjuntos
                if "attachment" in content_disposition:
                    continue

                # Procesar contenido HTML
                if content_type == "text/html":
                    html_content = part.get_payload(decode=True).decode('utf-8', errors="ignore")
                    break
        else:
            # Si no es multipart, tratar el contenido como HTML
            html_content = email_message.get_payload(decode=True).decode('utf-8', errors="ignore")

        if not html_content:
            return jsonify({'success': False, 'message': 'No se encontró contenido HTML en el correo.'})

        # Cerrar conexión
        mail.logout()

        # Renderizar el HTML directamente
        return jsonify({
            'success': True,
            'message': f'Correo encontrado: {subject}',
            'html': html_content
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al buscar correos: {str(e)}'})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)