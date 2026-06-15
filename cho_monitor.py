import customtkinter as ctk
import threading
import json
import os
import time
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

# =========================
# CONFIGURAÇÕES E VARIÁVEIS (AMBIENTE DA EMPRESA)
# =========================
CAMINHO_CSV = Path("Y:/cho_events.csv")
TEAMS_WEBHOOK = "" # link não incluído por privacidade e segurança
ARQUIVO_CONTROLE = "historico.json"
INTERVALO_SEGUNDOS = 120

estado_global = "Desconhecido"
historico = set()

# Carrega histórico
if os.path.exists(ARQUIVO_CONTROLE):
    try:
        with open(ARQUIVO_CONTROLE, "r") as f:
            dados = json.load(f)
            if isinstance(dados, list):
                historico = set(dados)
            else:
                historico = set(dados.get("eventos", []))
                estado_global = dados.get("estado_global", "Desconhecido")
    except:
        pass

def salvar_historico():
    with open(ARQUIVO_CONTROLE, "w") as f:
        json.dump({"estado_global": estado_global, "eventos": list(historico)}, f)

def parse_dt(ts):
    try: return datetime.strptime(ts.strip(), "%a %d %b %Y %H-%M-%S")
    except: return None

def hora(dt):
    return dt.strftime("%H:%M:%S") if dt else "??:??:??"

def obter_nome_recepcao(estado_bruto):
    if "PGM ION TIT" in estado_bruto: return "NIMBRA 1 (TITULAR)"
    if "PGM ION BY" in estado_bruto: return "NIMBRA 2 (BY)"
    if "PGM RIST" in estado_bruto: return "NIMBRA RIST (DR)"

    return estado_bruto

# ===================
# INTERFACE GRÁFICA 
# ===================
class AppMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configurações da Janela
        self.title("Change-Over Monitor - CED Recife")
        self.geometry("700x500")
        self.iconbitmap(r"C:\Users\TRANSCODER 2\Documents\app_com\vermelho_globo.ico")
        
        ctk.set_appearance_mode("dark") # modo escuro nativo
        ctk.set_default_color_theme("blue")

        self.monitorando = False # variável de controle do loop

        # --- Elementos da Tela ---
        
        # Título
        self.lbl_titulo = ctk.CTkLabel(self, text="Monitor de Eventos", font=("Arial", 50, "bold"))
        self.lbl_titulo.pack(pady=(20, 5))

        # Mostrador do Estado Global
        self.lbl_estado = ctk.CTkLabel(self, text=f"Estado Atual: {estado_global}", font=("Arial", 25), text_color="#00FF00")
        self.lbl_estado.pack(pady=(0, 20))

        # Caixa de Texto (Logs)
        self.caixa_logs = ctk.CTkTextbox(self, width=600, height=250, font=("Consolas", 18))
        self.caixa_logs.pack(pady=10)
        self.caixa_logs.insert("0.0", "Aguardando inicialização...\n")

        # Frame para os botões ficarem lado a lado
        self.frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botoes.pack(pady=20)

        # Botão Iniciar
        self.btn_iniciar = ctk.CTkButton(self.frame_botoes, text="▶ Iniciar Monitoramento", fg_color="green", hover_color="darkgreen", command=self.iniciar_thread, font=("Arial", 18))
        self.btn_iniciar.pack(side="left", padx=20)

        # Botão Parar
        self.btn_parar = ctk.CTkButton(self.frame_botoes, text="⏹ Parar", fg_color="red", hover_color="darkred", state="disabled", command=self.parar_monitoramento, font=("Arial", 18))
        self.btn_parar.pack(side="right", padx=20)

    def log_tela(self, mensagem):
        hora_atual = datetime.now().strftime('%H:%M:%S')
        self.caixa_logs.insert("end", f"[{hora_atual}] {mensagem}\n")
        self.caixa_logs.see("end") 

    def ler_csv(self):
        if not CAMINHO_CSV.exists():
            self.log_tela("Aviso: Rede desconectada ou arquivo ausente.")
            return pd.DataFrame()
        try:
            return pd.read_csv(CAMINHO_CSV, encoding="latin-1", sep=";")
        except Exception:
            try: return pd.read_csv(CAMINHO_CSV, encoding="latin-1", sep=",")
            except Exception as e:
                self.log_tela(f"Erro de leitura no CSV: {e}")
                return pd.DataFrame()

    def processar(self, df):
        global estado_global
        mensagens = []
        for _, r in df.iterrows():
            dt = parse_dt(str(r["Timestamp"]))
            if not dt: continue

            canal = str(r["Change-Over afetado"])
            novo = str(r["Novo estado"])
            anterior = str(r["Estado anterior"])
            evento_id = f"{r['Timestamp']}_{canal}_{novo}"

            if evento_id in historico: continue
            historico.add(evento_id)
            h = hora(dt)

            if canal in ["CHO3", "CHO4"]:
                if "MX CED" in novo:
                    estado_global = "MX CED (MCPC)"
                    mensagens.append(f"{h} - AR: {anterior} -> MX CED (MCPC)")
                elif "MX DR" in novo:
                    estado_global = "MATRIX DR"
                    mensagens.append(f"{h} - AR: {anterior} -> MATRIX DR")
                elif "CHO-1" in novo or "CHO-2" in novo:
                    estado_global = "NIMBRA"
                    mensagens.append(f"{h} - AR: {anterior} -> NIMBRA (TITULAR)")

            elif canal in ["CHO1", "CHO2"]:
                nome_ant = obter_nome_recepcao(anterior)
                nome_nov = obter_nome_recepcao(novo)
                if nome_ant != nome_nov:
                    mensagens.append(f"{h} - {nome_ant} -> {nome_nov} ({canal})")
            
            self.lbl_estado.configure(text=f"Estado Atual: {estado_global}")

        salvar_historico()
        return mensagens

    def enviar(self, mensagens):
        if not mensagens: 
            return
            
        linhas = []
        for m in mensagens:
            partes = m.split(" - ", 1)
            hora_txt = partes[0]
            evento = partes[1] if len(partes) > 1 else m
            linhas.append({
                "type": "ColumnSet",
                "columns": [
                    { "type": "Column", "width": "auto", "items": [{"type": "TextBlock", "text": hora_txt}] },
                    { "type": "Column", "width": "stretch", "items": [{"type": "TextBlock", "text": evento, "wrap": True}] }
                ]
            })

        # utiliza a variável global que foi alimentada pela função processar
        estado_final = f"{estado_global} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        card = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        { "type": "TextBlock", "text": "Comutação Nimbra / MCPC / DR", "weight": "Bolder", "size": "Medium" },
                        { "type": "Container", "items": linhas },
                        { "type": "TextBlock", "text": f"Estado atual: {estado_final}", "weight": "Bolder" }
                    ]
                }
            }]
        }

        try:
            resposta = requests.post(TEAMS_WEBHOOK, json=card)

            if resposta.status_code not in [200, 201, 202]:
                self.log_tela(f"Erro ao enviar para o Teams: HTTP {resposta.status_code} - {resposta.text}")
            else:
                self.log_tela("Sucesso! Notificação enviada ao Teams.")

        except Exception as e:
            self.log_tela(f"Falha de conexão com o Teams: {e}")

    # --- Lógica de Controle da Interface ---

    def iniciar_thread(self):
        self.monitorando = True
        self.btn_iniciar.configure(state="disabled")
        self.btn_parar.configure(state="normal")
        self.log_tela("Monitoramento INICIADO.")
        
        # inicia o loop infinito num segundo plano pra não travar a tela
        threading.Thread(target=self.loop_principal, daemon=True).start()

    def parar_monitoramento(self):
        # Abre a janelinha de Sim ou Não
        resposta = messagebox.askyesno("Confirmação", "Você tem certeza que deseja parar o monitoramento?")
        
        # Se a pessoa clicar em "Sim" (resposta == True), ele executa a parada
        if resposta:
            self.monitorando = False
            self.btn_iniciar.configure(state="normal")
            self.btn_parar.configure(state="disabled")
            self.log_tela("Monitoramento PARADO.")
        else:
            self.log_tela("Aviso: Tentativa de parada cancelada.")

    def loop_principal(self):
        while self.monitorando:
            df = self.ler_csv()
            msgs = self.processar(df)
            for m in msgs:
                self.log_tela(f"EVENTO: {m}")
            self.enviar(msgs)
            
            # ao invés de dormir 120s de uma vez, dorme de 1 em 1 segundo
            # isso permite que o botão "Parar" funcione na hora que clicar
            for _ in range(INTERVALO_SEGUNDOS):
                if not self.monitorando: break
                time.sleep(1)

if __name__ == "__main__":
    app = AppMonitor()
    app.mainloop()
