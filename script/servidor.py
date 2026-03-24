import cv2
import face_recognition
import pickle
import numpy as np
import threading
import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request

# CONFIGURAÇÕES
ARQUIVO_DADOS = "encodings.pickle"
BANCO_DADOS = "totem_banco.db"
PASTA_LOGS = "logs_imagens"
PASTA_DATASET = "dataset"
DELAY_RECONHECIMENTO = 5.0

app = Flask(__name__)
lock = threading.Lock()
lista_encodings = []
lista_nomes = []


# --- BANCO DE DADOS E ARMAZENAMENTO ---
def iniciar_banco():
    os.makedirs(PASTA_LOGS, exist_ok=True)
    os.makedirs(PASTA_DATASET, exist_ok=True)
    conn = sqlite3.connect(BANCO_DADOS)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            data_cadastro DATETIME,
            nivel_acesso TEXT
        )
    """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Logs_Acesso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            data_hora DATETIME,
            confianca_reconhecimento REAL,
            foto_momento TEXT,
            FOREIGN KEY(usuario_id) REFERENCES Usuarios(id)
        )
    """
    )
    conn.commit()
    conn.close()


def cadastrar_usuario_db(nome, nivel="Aluno"):
    conn = sqlite3.connect(BANCO_DADOS)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO Usuarios (nome, data_cadastro, nivel_acesso) VALUES (?, ?, ?)",
            (nome, datetime.now(), nivel),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def alinhar_rostos(image_rgb, face_location):
    """
    Recebe a imagem e rotaciona de forma que os olhos fiquem alinhados verticalmente (semelhante ao artigo do deepface)

    ----- (VS | 2005 🔱🪽)
    """

    # Extrai os pontos covulacionais (boca, nariz, olhos e orelhas)
    landmarks = face_recognition.face_landmarks(image_rgb), [face_location]

    # se nao conseguir extrair
    if not landmarks:
        return img_rgb  # retorna a imagem original se nao achar os marcos

    landmarks = landmarks[0]

    if "left_eye" in landmarks and "right_eye" in landmarks:
        left_eye_center = np.mean(landmarks["left_eye"], axis=0).astype("int")
        right_eye_center = np.mean(landmarks["right_eye"], axis=0).astype("int")

        # Calcula os diferencias entre os eixos X e Y
        dY = right_eye_center[1] - left_eye_center[1]
        dX = right_eye_center[0] - left_eye_center[0]

        # Calcula o angulo de rotacao necessario
        angle = np.degrees(np.arctan2(dY, dX))

        # Calculta o ponto central entre os olhos
        eyes_center = (
            left_eye_center[0] + right_eye_center[0] // 2,
            left_eye_center[1] + right_eye_center[1],
        ) // 2

        # obtem a matriz de rotacao e aplica a transformacao afim
        M = cv2.getRotationMatrix2D(eyes_center, angle, 1.0)
        h, w = image_rgb.shape[:2]
        imagem_alinhada = cv2.warpAffine(image_rgb, M, (w, h), flags=cv2.INTER_CUBIC)

        return imagem_alinhada
    return image_rgb


def registrar_acesso_db(nome, confianca, frame_capturado):
    conn = sqlite3.connect(BANCO_DADOS)
    c = conn.cursor()
    c.execute("SELECT id FROM Usuarios WHERE nome = ?", (nome,))
    row = c.fetchone()

    if not row:
        c.execute(
            "INSERT INTO Usuarios (nome, data_cadastro, nivel_acesso) VALUES (?, ?, ?)",
            (nome, datetime.now(), "Migrado"),
        )
        conn.commit()
        user_id = c.lastrowid
    else:
        user_id = row[0]

    agora_dt = datetime.now()
    nome_arquivo = f"{PASTA_LOGS}/{agora_dt.strftime('%Y%m%d_%H%M%S')}_{nome.replace(' ', '_')}.jpg"
    cv2.imwrite(nome_arquivo, frame_capturado)

    c.execute(
        """
        INSERT INTO Logs_Acesso (usuario_id, data_hora, confianca_reconhecimento, foto_momento)
        VALUES (?, ?, ?, ?)
    """,
        (user_id, agora_dt, confianca, nome_arquivo),
    )
    conn.commit()
    conn.close()


def carregar_dados():
    global lista_encodings, lista_nomes
    try:
        with open(ARQUIVO_DADOS, "rb") as f:
            data = pickle.load(f)
        lista_encodings = data["encodings"]
        lista_nomes = data["names"]
    except FileNotFoundError:
        lista_encodings, lista_nomes = [], []


def salvar_dados():
    global lista_encodings, lista_nomes
    data = {"encodings": lista_encodings, "names": lista_nomes}
    with open(ARQUIVO_DADOS, "wb") as f:
        f.write(pickle.dumps(data))


def treinar_novas_fotos(nome, lista_fotos):
    global lista_encodings, lista_nomes
    cadastrar_usuario_db(nome)

    pasta = os.path.join(PASTA_DATASET, nome)
    if not os.path.exists(pasta):
        os.makedirs(pasta)

    count = len(os.listdir(pasta))
    novos_encodings = 0

    for img in lista_fotos:
        filename = f"{pasta}/{count}.jpg"
        cv2.imwrite(filename, img)
        count += 1

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model="hog")
        encs = face_recognition.face_encodings(rgb, boxes)

        for enc in encs:
            with lock:
                lista_encodings.append(enc)
                lista_nomes.append(nome)
                novos_encodings += 1

    salvar_dados()
    return novos_encodings


# --- ROTAS DA API ---
@app.route("/api/reconhecer", methods=["POST"])
def reconhecer_rosto():
    if "foto" not in request.files:
        return jsonify({"erro": "Nenhuma foto enviada"}), 400

    file = request.files["foto"]
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    small = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    locs = face_recognition.face_locations(rgb)
    resultados = []

    if locs:
        encs = face_recognition.face_encodings(rgb, locs)
        for (top, right, bottom, left), enc in zip(locs, encs):
            name = "Desconhecido"

            with lock:
                if len(lista_encodings) > 0:
                    face_distances = face_recognition.face_distance(
                        lista_encodings, enc
                    )
                    best_match_index = np.argmin(face_distances)
                    distancia_minima = face_distances[best_match_index]

                    if distancia_minima < 0.5:
                        name = lista_nomes[best_match_index]
                        confianca_pct = round((1.0 - distancia_minima) * 100, 2)
                        registrar_acesso_db(name, confianca_pct, img)

            resultados.append(
                {"nome": name, "box": [top * 4, right * 4, bottom * 4, left * 4]}
            )

    return jsonify({"rostos": resultados}), 200


@app.route("/api/cadastrar_direto", methods=["POST"])
def cadastrar_direto():
    global lista_encodings, lista_nomes
    if "fotos" not in request.files or "nome" not in request.form:
        return jsonify({"erro": "Dados incompletos. Envie 'fotos' e 'nome'."}), 400

    files = request.files.getlist("fotos")
    name = request.form["nome"]
    lista_fotos = []

    for file in files:
        img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
        lista_fotos.append(img)

    try:
        total_treinado = treinar_novas_fotos(name, lista_fotos)
        return (
            jsonify(
                {
                    "msg": f"Sucesso! {name} cadastrado com {total_treinado} novos vetores faciais."
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"erro": f"Falha interna ao processar cadastro: {e}"}), 500


@app.route("/api/relatorio", methods=["GET"])
def relatorio_acessos():
    conn = sqlite3.connect(BANCO_DADOS)
    c = conn.cursor()
    c.execute(
        "SELECT u.nome, l.data_hora, l.confianca_reconhecimento, l.foto_momento FROM Logs_Acesso l JOIN Usuarios u ON l.usuario_id = u.id ORDER BY l.data_hora DESC LIMIT 100"
    )
    logs = [
        {
            "usuario": r[0],
            "data_hora": r[1],
            "confianca_pct": r[2],
            "foto_caminho": r[3],
        }
        for r in c.fetchall()
    ]
    conn.close()
    return jsonify({"total_logs": len(logs), "acessos": logs})


if __name__ == "__main__":
    iniciar_banco()
    carregar_dados()
    app.run(host="0.0.0.0", port=5001, debug=False)
