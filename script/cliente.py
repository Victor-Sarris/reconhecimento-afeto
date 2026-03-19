import cv2
import requests
import time
import numpy as np

# CONFIGURAÇÕES
URL_SERVIDOR = "http://127.0.0.1:5001/api"  # Caminho base para a API
LARGURA_TELA = 1024
ALTURA_TELA = 600
INTERVALO_SCAN = 1.0  # Envia foto para o servidor a cada 1 segundo no modo Reconhecer

COR_BARRA_FUNDO = (180, 0, 0)  # Azul escuro
COR_BTN_FUNDO = (20, 20, 20)  # Cinza quase preto
COR_TEXTO = (255, 255, 255)  # Branco
COR_STATUS = (0, 255, 255)  # Amarelo
COR_RECONHECIDO = (0, 255, 0)  # Verde

# ESTADOS DE OPERAÇÃO
MODO_RECONHECIMENTO = 0
MODO_ESCOLHA_NOME = 1
MODO_CAPTURANDO = 2

# Variáveis Globais de Estado
estado_atual = MODO_RECONHECIMENTO
nome_novo_cadastro = ""
buffer_fotos_novas = []  # Temporário para guardar as fotos antes de enviar
ultimo_envio = 0
rostos_detectados = []
mensagem_status = ""  # Para mostrar erros ou confirmações na tela
tempo_status = 0  # Para limpar a mensagem de status após alguns segundos


# --- FUNÇÃO PARA DESENHAR A INTERFACE (Simulando botões) ---
def desenhar_interface(frame):
    global mensagem_status, tempo_status
    # Barra inferior
    cv2.rectangle(
        frame, (0, ALTURA_TELA - 100), (LARGURA_TELA, ALTURA_TELA), COR_BARRA_FUNDO, -1
    )

    # Botão "Reconhecer"
    desenhar_botao(
        frame,
        (50, ALTURA_TELA - 80),
        (300, ALTURA_TELA - 20),
        "Reconhecer",
        estado_atual == MODO_RECONHECIMENTO,
    )

    # Botão "Cadastrar"
    desenhar_botao(
        frame,
        (350, ALTURA_TELA - 80),
        (600, ALTURA_TELA - 20),
        "Cadastrar",
        estado_atual != MODO_RECONHECIMENTO,
    )

    # Área de Texto/Status
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

    # Mostra mensagem de status se houver e o tempo não tiver expirado
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


# --- GERENCIADOR DE CLIQUES DO MOUSE (COPIADO E ADAPTADO) ---
def gerenciar_cliques(event, x, y, flags, param):
    global estado_atual, nome_novo_cadastro, buffer_fotos_novas, mensagem_status, tempo_status
    y_min = ALTURA_TELA - 80
    y_max = ALTURA_TELA - 20

    if event == cv2.EVENT_LBUTTONDOWN:
        # Verifica se o clique foi dentro da barra de botões
        if y_min < y < y_max:
            # Botão "Reconhecer"
            if 50 < x < 300:
                print("[INTERFACE] Alternando para Modo Reconhecimento.")
                estado_atual = MODO_RECONHECIMENTO
                buffer_fotos_novas = []  # Limpa buffer

            # Botão "Cadastrar"
            elif 350 < x < 600:
                print("[INTERFACE] Alternando para Modo Cadastro.")
                estado_atual = MODO_ESCOLHA_NOME
                nome_novo_cadastro = ""  # Reinicia nome
                buffer_fotos_novas = []  # Limpa buffer


# --- FUNÇÃO PARA ENVIAR O CADASTRO COMPLETO PARA O SERVIDOR ---
def enviar_cadastro_para_servidor():
    global buffer_fotos_novas, nome_novo_cadastro, estado_atual, mensagem_status, tempo_status

    if not nome_novo_cadastro:
        mensagem_status = "Erro: Digite um nome primeiro."
        tempo_status = time.time()
        estado_atual = MODO_ESCOLHA_NOME
        return

    if len(buffer_fotos_novas) < 3:  # Exige pelo menos 3 fotos
        mensagem_status = (
            f"Erro: Capture mais fotos (total: {len(buffer_fotos_novas)}/3)."
        )
        tempo_status = time.time()
        return

    mensagem_status = "Enviando cadastro para servidor..."
    tempo_status = time.time()

    # Prepara o dicionário de arquivos para o requests
    files = []
    for count, frame in enumerate(buffer_fotos_novas):
        # Converte a imagem do OpenCV em memória para o formato JPG
        _, buffer = cv2.imencode(".jpg", frame)
        files.append(("fotos", (f"frame_{count}.jpg", buffer.tobytes(), "image/jpeg")))

    # Prepara o formulário com o nome
    data = {"nome": nome_novo_cadastro}

    try:
        # Dispara um POST para a nova rota do servidor
        url = URL_SERVIDOR + "/cadastrar_direto"
        resposta = requests.post(
            url, files=files, data=data, timeout=120
        )  # Timeout maior para upload

        if resposta.status_code == 201:
            dados = resposta.json()
            mensagem_status = dados.get("msg", "Sucesso!")
            print(f"[IA] {mensagem_status}")
            estado_atual = MODO_RECONHECIMENTO  # Volta ao modo normal
            buffer_fotos_novas = []
        else:
            dados = resposta.json()
            mensagem_status = f"Erro no servidor: {dados.get('erro', 'Desconhecido')}"
            print(f"[ERRO] {mensagem_status}")

    except requests.exceptions.RequestException as e:
        mensagem_status = f"Erro de rede: {e}"
        print(f"[ERRO] Falha ao conectar no servidor para cadastro: {e}")

    tempo_status = time.time()


# --- INICIALIZAÇÃO DA CÂMERA E JANELA ---
# Conecta na webcam (pode ser o link do ESP32-CAM aqui depois)
stream = cv2.VideoCapture(0)
time.sleep(2)

cv2.namedWindow("Totem Cliente", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Totem Cliente", LARGURA_TELA, ALTURA_TELA)
# Ativa o gerenciamento de cliques
cv2.setMouseCallback("Totem Cliente", gerenciar_cliques)

print("[CLIENTE] Totem Iniciado. Aguardando conexão com servidor...")

while True:
    ret, frame_cru = stream.read()
    if not ret:
        time.sleep(0.01)
        continue

    frame = cv2.resize(frame_cru, (LARGURA_TELA, ALTURA_TELA))
    desenhar_interface(frame)
    agora = time.time()

    # --- LÓGICA DO MODO RECONHECIMENTO (existente) ---
    if estado_atual == MODO_RECONHECIMENTO:
        # Só faz a requisição pesada a cada INTERVALO_SCAN
        if (agora - ultimo_envio) > INTERVALO_SCAN:
            ultimo_envio = agora

            # Converte a imagem do OpenCV em memória para o formato JPG para enviar pela rede
            _, buffer = cv2.imencode(".jpg", frame)

            try:
                # Dispara um POST para a rota de reconhecimento
                url = URL_SERVIDOR + "/reconhecer"
                resposta = requests.post(
                    url,
                    files={"foto": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
                    timeout=2,
                )

                if resposta.status_code == 200:
                    dados = resposta.json()
                    rostos_detectados = dados.get("rostos", [])
            except requests.exceptions.RequestException as e:
                # print("[ERRO] Falha ao conectar no servidor de reconhecimento:", e)
                rostos_detectados = []

        # Desenha os resultados devolvidos pelo Servidor na tela local
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

    # --- LÓGICA DO MODO CAPTURA DE NOME ---
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

        # Simula a digitação na tela
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

    # --- LÓGICA DO MODO CAPTURA DE FOTOS ---
    elif estado_atual == MODO_CAPTURANDO:
        cv2.rectangle(
            frame, (0, 0), (LARGURA_TELA, 100), (200, 100, 0), -1
        )  # Barra superior azul clara
        cv2.putText(
            frame,
            f"CADASTRANDO: {nome_novo_cadastro}",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            COR_TEXTO,
            2,
        )

        info = f"[ESPAÇO] CAPTURAR FOTO ({len(buffer_fotos_novas)})  |  [ENTER] FINALIZAR E ENVIAR  |  [ESC] VOLTAR"
        cv2.putText(
            frame, info, (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1
        )

    # Mostra o frame com a interface na janela
    cv2.imshow("Totem Cliente", frame)

    # --- GERENCIADOR DE TECLADO (COPIADO E ADAPTADO) ---
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    # Lógica de digitação de nome
    if estado_atual == MODO_ESCOLHA_NOME:
        if key == 13:  # ENTER
            if nome_novo_cadastro:
                estado_atual = MODO_CAPTURANDO
                buffer_fotos_novas = []  # Garante buffer limpo
                print(
                    f"[INTERFACE] Nome '{nome_novo_cadastro}' escolhido. Alternando para Modo Captura."
                )
        elif key == 27:  # ESC
            estado_atual = MODO_RECONHECIMENTO
            nome_novo_cadastro = ""
            print("[INTERFACE] Cadastro cancelado pelo teclado.")
        elif key == 8:  # BACKSPACE
            nome_novo_cadastro = nome_novo_cadastro[:-1]
        elif 32 <= key <= 126:  # Teclas imprimíveis
            nome_novo_cadastro += chr(key)

    # Lógica de captura de fotos
    elif estado_atual == MODO_CAPTURANDO:
        if key == 13:  # ENTER - Finalizar e Enviar
            enviar_cadastro_para_servidor()
        elif key == 27:  # ESC - Voltar para escolha de nome
            estado_atual = MODO_ESCOLHA_NOME
            print("[INTERFACE] Voltando para escolha de nome.")
        elif key == 32:  # ESPAÇO - Capturar Foto
            # Adiciona a imagem capturada original (crua, maior resolução) ao buffer
            buffer_fotos_novas.append(frame_cru.copy())
            print(
                f"[INTERFACE] Foto {len(buffer_fotos_novas)} capturada para o buffer."
            )

# Encerramento
stream.release()
cv2.destroyAllWindows()
