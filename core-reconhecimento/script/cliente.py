import cv2
import requests
import time
import numpy as np

# CONFIGURAÇÕES
URL_SERVIDOR = "http://127.0.0.1:5001/api"
LARGURA_TELA = 1920
ALTURA_TELA = 1080
INTERVALO_SCAN = 1.0

COR_BARRA_FUNDO = (180, 0, 0)
COR_BTN_FUNDO = (20, 20, 20)
COR_TEXTO = (255, 255, 255)
COR_STATUS = (0, 255, 255)
COR_RECONHECIDO = (0, 255, 0)

# ESTADOS DE OPERAÇÃO
MODO_RECONHECIMENTO = 0
MODO_ESCOLHA_NOME = 1
MODO_CAPTURANDO = 2
MODO_ESCOLHA_TELEFONE = 3

estado_atual = MODO_RECONHECIMENTO
nome_novo_cadastro = ""
telefone_novo_cadastro = ""
buffer_fotos_novas = []
ultimo_envio = 0
rostos_detectados = []
mensagem_status = ""
tempo_status = 0


# --- INTERFACE GRÁFICA ---
def desenhar_interface(frame):
    global mensagem_status, tempo_status
    cv2.rectangle(
        frame, (0, ALTURA_TELA - 100), (LARGURA_TELA, ALTURA_TELA), COR_BARRA_FUNDO, -1
    )

    desenhar_botao(
        frame,
        (50, ALTURA_TELA - 80),
        (300, ALTURA_TELA - 20),
        "Reconhecer",
        estado_atual == MODO_RECONHECIMENTO,
    )
    desenhar_botao(
        frame,
        (350, ALTURA_TELA - 80),
        (600, ALTURA_TELA - 20),
        "Cadastrar",
        estado_atual != MODO_RECONHECIMENTO,
    )

    cv2.rectangle(
        frame,
        (650, ALTURA_TELA - 80),
        (LARGURA_TELA - 50, ALTURA_TELA - 20),
        COR_BTN_FUNDO,
        -1,
    )
    cv2.rectangle(
        frame,
        (650, ALTURA_TELA - 80),
        (LARGURA_TELA - 50, ALTURA_TELA - 20),
        COR_TEXTO,
        1,
    )

    if mensagem_status and (time.time() - tempo_status) < 5:
        cv2.putText(
            frame,
            mensagem_status,
            (670, ALTURA_TELA - 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            COR_STATUS,
            1,
        )
    else:
        mensagem_status = ""


def desenhar_botao(frame, pt1, pt2, texto, ativo=False):
    cor_borda = (0, 255, 0) if ativo else COR_TEXTO
    cv2.rectangle(frame, pt1, pt2, COR_BTN_FUNDO, -1)
    cv2.rectangle(frame, pt1, pt2, cor_borda, 1)
    cv2.putText(
        frame,
        texto,
        (pt1[0] + 60, pt1[1] + 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        COR_TEXTO,
        2,
    )


def gerenciar_cliques(event, x, y, flags, param):
    global estado_atual, nome_novo_cadastro, telefone_novo_cadastro, buffer_fotos_novas, mensagem_status, tempo_status
    y_min = ALTURA_TELA - 80
    y_max = ALTURA_TELA - 20

    if event == cv2.EVENT_LBUTTONDOWN:
        if y_min < y < y_max:
            if 50 < x < 300:
                estado_atual = MODO_RECONHECIMENTO
                buffer_fotos_novas = []
            elif 350 < x < 600:
                estado_atual = MODO_ESCOLHA_NOME
                nome_novo_cadastro = ""
                telefone_novo_cadastro = ""
                buffer_fotos_novas = []


# --- COMUNICAÇÃO COM SERVIDOR ---
def enviar_cadastro_para_servidor():
    global buffer_fotos_novas, nome_novo_cadastro, estado_atual, mensagem_status, tempo_status

    if not nome_novo_cadastro:
        mensagem_status = "Erro: Digite um nome primeiro."
        tempo_status = time.time()
        estado_atual = MODO_ESCOLHA_NOME
        return

    if len(buffer_fotos_novas) < 3:
        mensagem_status = (
            f"Erro: Capture mais fotos (total: {len(buffer_fotos_novas)}/3)."
        )
        tempo_status = time.time()
        return

    mensagem_status = "Enviando cadastro para servidor..."
    tempo_status = time.time()

    files = []
    for count, frame in enumerate(buffer_fotos_novas):
        _, buffer = cv2.imencode(".jpg", frame)
        files.append(("fotos", (f"frame_{count}.jpg", buffer.tobytes(), "image/jpeg")))

    data = {"nome": nome_novo_cadastro, "telefone": telefone_novo_cadastro}

    try:
        url = URL_SERVIDOR + "/cadastrar_direto"
        resposta = requests.post(url, files=files, data=data, timeout=120)

        if resposta.status_code == 201:
            dados = resposta.json()
            mensagem_status = dados.get("msg", "Sucesso!")
            estado_atual = MODO_RECONHECIMENTO
            buffer_fotos_novas = []
        else:
            dados = resposta.json()
            mensagem_status = f"Erro no servidor: {dados.get('erro', 'Desconhecido')}"

    except requests.exceptions.RequestException as e:
        mensagem_status = f"Erro de rede: {e}"

    tempo_status = time.time()


# --- INICIALIZAÇÃO ---
stream = cv2.VideoCapture(0)
time.sleep(2)

cv2.namedWindow("Totem Cliente", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Totem Cliente", LARGURA_TELA, ALTURA_TELA)
cv2.setMouseCallback("Totem Cliente", gerenciar_cliques)

while True:
    ret, frame_cru = stream.read()
    if not ret:
        time.sleep(0.01)
        continue

    frame = cv2.resize(frame_cru, (LARGURA_TELA, ALTURA_TELA))
    desenhar_interface(frame)
    agora = time.time()

    # MODO RECONHECIMENTO
    if estado_atual == MODO_RECONHECIMENTO:
        if (agora - ultimo_envio) > INTERVALO_SCAN:
            ultimo_envio = agora
            _, buffer = cv2.imencode(".jpg", frame)

            try:
                url = URL_SERVIDOR + "/reconhecer"
                resposta = requests.post(
                    url,
                    files={"foto": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
                    timeout=2,
                )
                if resposta.status_code == 200:
                    dados = resposta.json()
                    rostos_detectados = dados.get("rostos", [])
            except requests.exceptions.RequestException:
                rostos_detectados = []

        for rosto in rostos_detectados:
            top, right, bottom, left = rosto["box"]
            nome = rosto["nome"]
            cor = COR_RECONHECIDO if nome != "Desconhecido" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), cor, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), cor, cv2.FILLED)
            cv2.putText(
                frame,
                nome,
                (left + 6, bottom - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                1,
            )

    # MODO DIGITAÇÃO DE NOME
    elif estado_atual == MODO_ESCOLHA_NOME:
        cv2.rectangle(frame, (100, 100), (LARGURA_TELA - 100, 300), (0, 0, 0), -1)
        cv2.rectangle(frame, (100, 100), (LARGURA_TELA - 100, 300), COR_TEXTO, 2)
        cv2.putText(
            frame,
            "DIGITE O NOME DO NOVO USUÁRIO:",
            (150, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            COR_TEXTO,
            2,
        )
        cv2.putText(
            frame,
            f"{nome_novo_cadastro}_",
            (150, 230),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            COR_STATUS,
            3,
        )
        cv2.putText(
            frame,
            "[ENTER] para Próximo | [ESC] para Cancelar",
            (250, 280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            COR_TEXTO,
            1,
        )

    # MODO DIGITAÇÃO DE TELEFONE
    elif estado_atual == MODO_ESCOLHA_TELEFONE:
        cv2.rectangle(frame, (100, 100), (LARGURA_TELA - 100, 300), (0, 0, 0), -1)
        cv2.rectangle(frame, (100, 100), (LARGURA_TELA - 100, 300), COR_TEXTO, 2)
        cv2.putText(
            frame,
            "DIGITE O TELEFONE (DDD + NUMERO):",
            (150, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            COR_TEXTO,
            2,
        )
        cv2.putText(
            frame,
            f"{telefone_novo_cadastro}_",
            (150, 230),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            COR_STATUS,
            3,
        )
        cv2.putText(
            frame,
            "[ENTER] para Capturar Fotos | [ESC] para Cancelar",
            (250, 280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            COR_TEXTO,
            1,
        )

    # MODO CAPTURA DE FOTOS
    elif estado_atual == MODO_CAPTURANDO:
        cv2.rectangle(frame, (0, 0), (LARGURA_TELA, 100), (200, 100, 0), -1)
        cv2.putText(
            frame,
            f"CADASTRANDO: {nome_novo_cadastro}",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            COR_TEXTO,
            2,
        )
        info = f"[ESPACO] CAPTURAR FOTO ({len(buffer_fotos_novas)})  |  [ENTER] FINALIZAR E ENVIAR  |  [ESC] VOLTAR"
        cv2.putText(
            frame, info, (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1
        )

    cv2.imshow("Totem Cliente", frame)

    # --- EVENTOS DE TECLADO ---
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    if estado_atual == MODO_ESCOLHA_NOME:
        if key == 13:  # Enter
            if nome_novo_cadastro:
                estado_atual = MODO_ESCOLHA_TELEFONE  # Vai para a tela de telefone
        elif key == 27:  # Esc
            estado_atual = MODO_RECONHECIMENTO
            nome_novo_cadastro = ""
        elif key == 8:  # Backspace
            nome_novo_cadastro = nome_novo_cadastro[:-1]
        elif 32 <= key <= 126:
            nome_novo_cadastro += chr(key)

    elif estado_atual == MODO_ESCOLHA_TELEFONE:
        if key == 13:  # Enter
            estado_atual = MODO_CAPTURANDO  # Vai para as fotos
            buffer_fotos_novas = []
        elif key == 27:  # Esc
            estado_atual = MODO_RECONHECIMENTO
            nome_novo_cadastro = ""
            telefone_novo_cadastro = ""
        elif key == 8:  # Backspace
            telefone_novo_cadastro = telefone_novo_cadastro[:-1]
        elif ord("0") <= key <= ord("9"):  # Aceita APENAS números
            telefone_novo_cadastro += chr(key)

    elif estado_atual == MODO_CAPTURANDO:
        if key == 13:
            enviar_cadastro_para_servidor()
        elif key == 27:
            estado_atual = MODO_ESCOLHA_NOME
        elif key == 32:
            buffer_fotos_novas.append(frame_cru.copy())

stream.release()
cv2.destroyAllWindows()
