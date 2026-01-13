from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

@app.route('/api/lead', methods=['POST'])
def capture_lead():
    try:
        data = request.json
        nome = data.get('nome')
        email = data.get('email')
        empresa = data.get('empresa', '')
        
        if not nome or not email:
            return jsonify({'error': 'Nome e email são obrigatórios'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO leads (nome, email, empresa, recurso) VALUES (%s, %s, %s, %s)",
            (nome, email, empresa, 'Guia NR-1')
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        enviar_email_com_pdf(nome, email)
        
        return jsonify({'success': True, 'message': 'Lead capturado com sucesso!'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def enviar_email_com_pdf(nome, email_destino):
    email_remetente = os.getenv('EMAIL_USER')
    senha_email = os.getenv('EMAIL_PASSWORD')
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    
    msg = MIMEMultipart()
    msg['From'] = email_remetente
    msg['To'] = email_destino
    msg['Subject'] = '📥 Seu Guia NR-1 - DNF Ocupacional'
    
    corpo = f"""
    <html>
    <body style='font-family: Arial, sans-serif; color: #333;'>
        <h2 style='color: #0052CC;'>Olá, {nome}!</h2>
        <p>Obrigado pelo seu interesse no nosso material sobre <strong>NR-1</strong>.</p>
        <p>Segue em anexo o Guia Completo da NR-1 que você solicitou.</p>
        <p>Se tiver dúvidas ou precisar de consultoria especializada, estamos à disposição!</p>
        <br>
        <p>Atenciosamente,<br><strong>Equipe DNF Ocupacional</strong></p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(corpo, 'html'))
    
    pdf_path = '/var/www/dnf-ocupacional/resources/guia-nr1.pdf'
    with open(pdf_path, 'rb') as arquivo:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(arquivo.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename=Guia-NR1-DNF-Ocupacional.pdf')
        msg.attach(part)
    
    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    server.login(email_remetente, senha_email)
    server.send_message(msg)
    server.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)