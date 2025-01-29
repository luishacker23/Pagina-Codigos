import imaplib
import email
import re
from email.header import decode_header
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup


app = Flask(__name__)

EMAIL = 'luismi003022@gmail.com'
PASSWORD = 'unsn xfdz qaob uglx'
IMAP_SERVER = 'imap.gmail.com'

# Expresiones regulares para filtrar los asuntos
ASUNTOS_PERMITIDOS = [
    r"código de acceso único.*Disney\+",
    r"amazon\.com: Sign-in attempt",
    r"actualizar.*Hogar.*Disney\+",
    r"código de acceso temporal.*Netflix",
    r"Restablecimiento.*contraseña.*Paramount\+",
    r"Your one-time passcode for.*Disney\+"
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    correo = request.form.get('email')
    if not correo:
        return jsonify({'success': False, 'message': 'No se proporcionó un correo.'})

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox')

        status, messages = mail.search(None, f'(TO "{correo}")')
        messages = messages[0].split()

        if not messages:
            return jsonify({'success': False, 'message': f'No se encontraron correos para {correo}.'})

        for email_id in reversed(messages):  # Recorrer de más reciente a más antiguo
            status, data = mail.fetch(email_id, '(RFC822)')
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)

            # Decodificar asunto
            subject = email_message['subject']
            decoded_subject = decode_header(subject)
            subject = ''.join(
                part.decode(encoding if encoding else 'utf-8', errors="ignore") if isinstance(part, bytes) else part
                for part, encoding in decoded_subject
            )

            

            # Filtrar si el asunto coincide con los permitidos
            if any(re.search(pattern, subject, re.IGNORECASE) for pattern in ASUNTOS_PERMITIDOS):
                

                html_content = None
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if "attachment" in content_disposition:
                            continue

                        if content_type == "text/html":
                            html_content = part.get_payload(decode=True).decode('utf-8', errors="ignore")
                            break
                else:
                    html_content = email_message.get_payload(decode=True).decode('utf-8', errors="ignore")

                if html_content:
                    mail.logout()
                    return jsonify({
                        'success': True,
                        'message': f'Correo encontrado: {subject}',
                        'html': html_content
                    })

        mail.logout()
        return jsonify({'success': False, 'message': 'No se encontraron correos con los asuntos permitidos.'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al buscar correos: {str(e)}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
