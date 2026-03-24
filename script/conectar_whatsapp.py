import requests
import time


def conectar():
    url_base = "http://localhost:8080"
    headers = {
        "apikey": "AfetoTotem2026",  # senha do .env
        "Content-Type": "application/json",
    }

    try:
        print("1. Limpando conexões antigas...")
        requests.delete(f"{url_base}/instance/delete/totem_afeto", headers=headers)
        time.sleep(2)

        print("2. Gerando o QR Code...")
        payload = {
            "instanceName": "totem_afeto",
            "integration": "WHATSAPP-BAILEYS",
            "qrcode": True,
        }

        resposta = requests.post(
            f"{url_base}/instance/create", json=payload, headers=headers
        )

        if resposta.status_code in [200, 201]:
            print("\n✅ SUCESSO! A sessão foi aberta.")
            print(
                "👉 Agora olhe para a tela preta (terminal) onde a Evolution API está rodando."
            )
            print("O QR Code foi desenhado lá!")
        else:
            print(f"\n❌ A API recusou o comando. Motivo: {resposta.text}")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO DE CONEXÃO: O servidor da Evolution API está desligado!")


if __name__ == "__main__":
    conectar()
