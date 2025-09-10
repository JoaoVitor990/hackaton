from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import os
import mysql.connector
from fpdf import FPDF

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------------------
# Configuração MySQL
# ------------------------------
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "hackaton_db"
}

# Criar banco e tabela se não existirem
try:
    conn = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password']
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS hackaton_db")
    conn.database = db_config['database']
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resultados (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(100),
        rm INT,
        nota FLOAT,
        respostas VARCHAR(255)
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()
except Exception as e:
    print("Erro ao configurar MySQL:", e)

# ------------------------------
# Função PDF
# ------------------------------
def gerar_pdf(nome, rm, respostas_gabarito, respostas_aluno, nota, erros, caminho_saida):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Correção de Prova", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Nome: {nome}", ln=True)
    pdf.cell(0, 10, f"RM: {rm}", ln=True)
    pdf.cell(0, 10, f"Nota: {nota:.2f}", ln=True)
    pdf.ln(5)

    pdf.cell(0, 10, "Respostas do Gabarito:", ln=True)
    pdf.multi_cell(0, 8, ", ".join(respostas_gabarito))
    pdf.ln(3)

    pdf.cell(0, 10, "Respostas do Aluno:", ln=True)
    pdf.multi_cell(0, 8, ", ".join(respostas_aluno))
    pdf.ln(3)

    pdf.cell(0, 10, "Erros:", ln=True)
    if erros:
        pdf.multi_cell(0, 8, " | ".join(erros))
    else:
        pdf.cell(0, 10, "Nenhum", ln=True)

    pdf.output(caminho_saida)

# ------------------------------
# Extrair respostas
# ------------------------------
def extrair_respostas_por_bolinhas(imagem_path, num_questoes=5, num_alternativas=5):
    img = cv2.imread(imagem_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Imagem não encontrada: {imagem_path}")
    _, img_bin = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contornos, _ = cv2.findContours(img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bolinhas = []
    for cnt in contornos:
        area = cv2.contourArea(cnt)
        if 80 < area < 3000:
            (x, y), r = cv2.minEnclosingCircle(cnt)
            bolinhas.append((int(x), int(y), int(r)))
    bolinhas = sorted(bolinhas, key=lambda b: b[1])
    linhas = []
    for i in range(num_questoes):
        inicio = i * num_alternativas
        fim = (i + 1) * num_alternativas
        linha = sorted(bolinhas[inicio:fim], key=lambda b: b[0])
        linhas.append(linha)
    alternativas = ['A', 'B', 'C', 'D', 'E']
    respostas = []
    for linha in linhas:
        resposta_questao = None
        maior_preenchimento = 0
        for j, bolinha in enumerate(linha):
            x, y, r = bolinha
            roi = img_bin[max(0,y-r):y+r, max(0,x-r):x+r]
            if roi.size == 0:
                continue
            proporcao = cv2.countNonZero(roi) / roi.size
            if proporcao > maior_preenchimento:
                maior_preenchimento = proporcao
                resposta_questao = alternativas[j]
        if maior_preenchimento < 0.35:
            resposta_questao = '-'
        respostas.append(resposta_questao)
    return respostas

# ------------------------------
# Calcular nota
# ------------------------------
def calcular_nota(gabarito, respostas):
    acertos = 0
    erros = []
    for i in range(len(gabarito)):
        if i < len(respostas):
            if gabarito[i] == respostas[i]:
                acertos += 1
            else:
                erros.append(f"Q{i+1}: correto {gabarito[i]}, marcado {respostas[i]}")
    nota = (acertos / len(gabarito)) * 10
    return nota, acertos, len(gabarito), erros

# ------------------------------
# Servir uploads (PDFs)
# ------------------------------
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ------------------------------
# Endpoint corrigir
# ------------------------------
@app.route('/corrigir', methods=['POST'])
def corrigir():
    try:
        gabarito_file = request.files.get('gabarito')
        aluno_file = request.files.get('aluno')
        nome = request.form.get('nome', 'Aluno X')
        rm = int(request.form.get('rm', 0))
        num_questoes = int(request.form.get('num_questoes', 5))
        num_alternativas = int(request.form.get('num_alternativas', 5))

        if not gabarito_file or not aluno_file:
            return jsonify({"error": "Envie ambas as imagens"}), 400

        path_g = os.path.join(UPLOAD_FOLDER, secure_filename(gabarito_file.filename))
        path_a = os.path.join(UPLOAD_FOLDER, secure_filename(aluno_file.filename))
        gabarito_file.save(path_g)
        aluno_file.save(path_a)

        respostas_g = extrair_respostas_por_bolinhas(path_g, num_questoes, num_alternativas)
        respostas_a = extrair_respostas_por_bolinhas(path_a, num_questoes, num_alternativas)
        nota, acertos, total, erros = calcular_nota(respostas_g, respostas_a)

        # 1️⃣ Salvar no MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resultados (nome, rm, nota, respostas)
            VALUES (%s, %s, %s, %s)
        """, (nome, rm, nota, ",".join(respostas_a)))
        conn.commit()
        cursor.close()
        conn.close()

        # 2️⃣ Gerar PDF após salvar
        pdf_name = f"{nome}_correcao.pdf".replace(" ", "_")
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_name)
        gerar_pdf(nome, rm, respostas_g, respostas_a, nota, erros, pdf_path)
        pdf_url = f"/uploads/{pdf_name}"

        return jsonify({
            "respostas_gabarito": respostas_g,
            "respostas_aluno": respostas_a,
            "nota": nota,
            "acertos": acertos,
            "total": total,
            "erros": erros,
            "pdf_url": pdf_url
        })
    except Exception as e:
        return jsonify({"error": "Erro interno", "detalhes": str(e)}), 500

# ------------------------------
# Endpoint para ver resultados
# ------------------------------
@app.route('/resultados')
def resultados():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resultados")
        dados = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(dados)
    except Exception as e:
        return jsonify({"error": "Não foi possível acessar o banco", "detalhes": str(e)}), 500

# ------------------------------
# Rota principal
# ------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# ------------------------------
# Rodar servidor
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)
