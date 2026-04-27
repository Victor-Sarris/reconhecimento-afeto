# Rotas do Script:

```python
# Rota de Reconhecimento
http://127.0.0.1:5001/api/reconhecer
```

```python
# Rota de Cadastro Direto
http://127.0.0.1:5001/api/cadastrar_direto
```

```python
# Rota de Relatorio
http://127.0.0.1:5001/api/relatorio
```

# Bibliotes necessarias:

Nota: As bibliotecas terao que ser instaladas no diretorio: "C:\script\reconhecimento-afeto\core-reconhecimento"
(crie uma venv antes de fazer a instalacao)

```python

python.exe -m pip install --upgrade pip

pip install "setuptools<81"

pip install requests

pip install face_recognition

pip install flask

pip install opencv-python

pip install waitress

```

# API utilizada

Nota: As bibliotecas terao que ser instaladas no diretorio: "C:\script\reconhecimento-afeto\api-whatsapp"

<a href="https://github.com/EvolutionAPI/evolution-api">Evolution API</a>

```powershell
# Instalacao de dependencias
npm install
```

```powershell
# Migracao de dados para o banco
npm run db:deploy

# Caso de erro:

npm run db:deploy:win
```

```powershell
# Instalacao de dependencias
npx prisma generate --schema prisma/postgresql-schema.prisma
```

```powershell
# Builder
npm run build
```

```powershell
# Start Project
npm run start:prod
```

================== Configuração de BAT file ==================

```
Chave para acessar a API:
AFETOEIFPI
```

================== Configuração de BAT file ==================

### 1. Faxina de Desenvolvimento (Reset do Sistema)

<p>Antes de cadastrar pessoas reais, precisamos apagar todos os "lixos" e rostos distorcidos que geramos durante os testes de código para que a inteligência artificial não fique confusa.</p>
<p>Vá até a pasta core-reconhecimento e apague:</p>

<ul>
    <li>O arquivo totem_banco.db (o SQLite vai criar um novo, limpinho).</li>
    <li>O arquivo encodings.pickle (que guarda os vetores matemáticos antigos)</li>
    <li>Todo o conteúdo dentro da pasta dataset/ (apague as subpastas de testes)</li>
    <li>Todo o conteúdo dentro da pasta logs_imagens/ </li>
</ul>

### 2. Inicialização Automática (Modo Totem Autônomo)

<p>O totem precisa ligar sozinho se houver uma queda de energia, sem que ninguém precise abrir pastas ou digitar comandos. Vamos fazer o Windows iniciar o seu projeto automaticamente:</p>

<p>Clique com o botão direito no seu arquivo iniciar_servidores.bat e escolha Criar Atalho.</p>

<p>No teclado, pressione Windows + R, digite shell:startup e dê Enter. (Isso abrirá a pasta de inicialização do Windows).</p>

Arraste o atalho que você acabou de criar para dentro dessa pasta.
<strong>Pronto! Toda vez que o computador do totem for ligado, o seu sistema subirá o Node.js, o Flask e a câmera automaticamente.</strong>

### 3. Preparação do Ambiente Físico

<p>A IA de reconhecimento facial (face_recognition / dlib) é muito sensível à iluminação e ao ângulo.</p>

<p>Posicionamento: A câmera deve ficar idealmente na altura dos olhos da média das pessoas (cerca de 1,50m a 1,60m do chão). Se a câmera ficar olhando muito de baixo para cima ou de cima para baixo, a precisão cai drasticamente.</p>

<p>Iluminação: Evite colocar o totem contra a luz (uma janela ou porta de vidro brilhante atrás da pessoa). A luz deve bater no rosto de quem está sendo reconhecido.</p>

### 4. A Bateria de Testes (Homologação)

<p>Com tudo limpo e posicionado, ligue o sistema e chame 3 ou 4 pessoas diferentes para o teste.</p>

<p>Credenciamento: Cadastre o nome, o número de WhatsApp (com DDD) e deixe o sistema tirar as fotos com a pessoa se movendo levemente (para pegar pequenos ângulos).</p>

<p>O Teste de Estresse: Peça para as pessoas passarem na frente do totem usando óculos, com o cabelo diferente ou em duplas.</p>

<p>Validação: Verifique se as mensagens estão chegando em até 5 segundos no celular após a tela verde de "Acesso Liberado" aparecer.</p>

Victor S. | 🔱🪽
