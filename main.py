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

EMAIL2 = 'juanpedri45u@gmail.com'
PASSWORD2 = 'aive swol azfs jizr'

EMAIL3 = 'jianjai9@gmail.com'
PASSWORD3 = 'cqwm nysh vfob rjhk'


IMAP_SERVER = 'imap.gmail.com'

# Lista de asuntos permitidos
ASUNTOS_PERMITIDOS = [
    r"código de acceso único.*Disney\+",
    r"amazon\.com: Sign-in attempt",
    r"actualizar.*Hogar.*Disney\+",
    r"código de acceso temporal.*Netflix",
    r"Restablecimiento.*contraseña.*Paramount\+",
    r"Your one-time passcode for.*Disney\+",
    r"Universal\+ código de activación",
    r"(?i)(senha|contraseña).*Paramount\+.*(redefinida|restablecida|fue redefinida|foi redefinida)"



]

def es_asunto_permitido(asunto):
    """Verifica si el asunto del correo coincide con alguno de los permitidos."""
    return any(re.search(patron, asunto, re.IGNORECASE) for patron in ASUNTOS_PERMITIDOS)

def buscar_correo(email_user, password, correo_buscar):
    try:
        # Conectar al servidor IMAP
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(email_user, password)
        mail.select('inbox')

        # Buscar correos en la bandeja de entrada
        status, messages = mail.search(None, f'(TO "{correo_buscar}")')
        messages = messages[0].split()

        if not messages:
            return None  # No encontró correos en esta cuenta

        # Obtener el último mensaje encontrado
        for email_id in reversed(messages):  # Revisar desde el más reciente
            status, data = mail.fetch(email_id, '(RFC822)')
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)

            # Extraer y decodificar asunto
            subject = email_message['subject']
            decoded_subject = decode_header(subject)
            subject = ''.join(
                part.decode(encoding if encoding else 'utf-8', errors="ignore") if isinstance(part, bytes) else part
                for part, encoding in decoded_subject
            )

            # Si el asunto no está permitido, seguir con el siguiente correo
            if not es_asunto_permitido(subject):
                continue

            # Extraer cuerpo del correo electrónico
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

            mail.logout()

            return {'email_account': email_user, 'subject': subject, 'html': html_content or 'No se encontró contenido.'}

        mail.logout()
        return None  # Si ningún correo tenía un asunto permitido

    except Exception:
        return None  # Si hay un error en esta cuenta, simplemente pasamos a la otra

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    correo = request.form.get('email')
    if not correo:
        return jsonify({'success': False, 'message': 'No se proporcionó un correo.'})

    # Buscar en la primera cuenta
    resultado = buscar_correo(EMAIL, PASSWORD, correo)

    # Si no encuentra en la primera, intenta en la segunda
    if not resultado:
        resultado = buscar_correo(EMAIL2, PASSWORD2, correo)
      # Si no encuentra en la primera, intenta en la segunda
    if not resultado:
        resultado = buscar_correo(EMAIL3, PASSWORD3, correo)

    if not resultado:
        return jsonify({'success': False, 'message': f'No se encontraron correos para {correo}.'})

    return jsonify({'success': True, 'message': f'Correo encontrado: {resultado["subject"]}', 'html': resultado['html']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
