import customtkinter as ctk
import pyautogui
import time
import os
import shutil
from datetime import datetime
import threading
from tkinter import messagebox

# --- CONFIGURAÇÕES ---
pyautogui.PAUSE = 1.2
pyautogui.FAILSAFE = True # Mantemos o failsafe do mouse por segurança extrema

CAMINHO_ATLAS_EXE = r"C:\ATLAS\Atlas_Browser_1.3.3\AtlasBrowser.exe"

CENTROS = {
    "UBERABA": (436, 268),
    "PGUA 1": (475, 338),
    "RONDONÓPOLIS": (463, 361),
    "RIO GRANDE": (443, 405),
}

CAMINHO_DOWNLOADS = r'C:\Users\esantan3\Downloads'
CAMINHO_BASE = r'G:\expedicao\Business Inteligence & Data Modelling\Colar Arquivos\Colar ATLAS\Colar ATLAS Carregamento'

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Automação ATLAS - Mosaic")
        self.geometry("500x600")
        ctk.set_appearance_mode("dark")

        # Variável de controle de execução
        self.executando = False 

        # --- Elementos da Interface ---
        self.label = ctk.CTkLabel(self, text="Relatório Diário de Balança", font=("Roboto", 20, "bold"))
        self.label.pack(pady=20)

        self.combo_unidades = ctk.CTkComboBox(self, values=list(CENTROS.keys()), width=250)
        self.combo_unidades.pack(pady=10)

        # Botão Iniciar
        self.btn_iniciar = ctk.CTkButton(self, text="Iniciar Download", command=self.start_thread, fg_color="green", hover_color="darkgreen")
        self.btn_iniciar.pack(pady=10)

        # Botão Parar (Novo)
        self.btn_parar = ctk.CTkButton(self, text="Parar Automação", command=self.parar_macro, fg_color="red", hover_color="darkred", state="disabled")
        self.btn_parar.pack(pady=10)

        self.log_text = ctk.CTkTextbox(self, width=400, height=200)
        self.log_text.pack(pady=20)

    def adicionar_log(self, mensagem):
        hora = datetime.now().strftime("%H:%M:%S")
        texto = f"[{hora}] {mensagem}\n"
        self.after(0, lambda: self._update_log_ui(texto))

    def _update_log_ui(self, texto):
        self.log_text.insert("end", texto)
        self.log_text.see("end")

    def parar_macro(self):
        """Altera a flag para interromper a thread do robô."""
        if self.executando:
            self.executando = False
            self.adicionar_log("⚠️ Solicitando interrupção... Aguarde.")
            self.btn_parar.configure(state="disabled")

    def start_thread(self):
        unidade_selecionada = self.combo_unidades.get()
        if not unidade_selecionada:
            messagebox.showwarning("Aviso", "Selecione uma unidade!")
            return
            
        self.executando = True
        self.btn_iniciar.configure(state="disabled")
        self.btn_parar.configure(state="normal")
        
        t = threading.Thread(target=self.executar_robo, args=(unidade_selecionada,))
        t.daemon = True 
        t.start()

    def check_status(self):
        """Verifica se o usuário clicou em parar durante a execução."""
        if not self.executando:
            raise InterruptedError("Automação cancelada pelo usuário.")

    def executar_robo(self, nome_unidade):
        try:
            self.after(0, self.iconify)
            time.sleep(1.5)

            self.adicionar_log(f"Iniciando {nome_unidade}...")
            os.startfile(CAMINHO_ATLAS_EXE)
            
            # Esperas fracionadas para permitir a interrupção durante o sleep
            for _ in range(15): 
                self.check_status()
                time.sleep(1)

            coord_unidade = CENTROS[nome_unidade]
            hoje = datetime.now()
            mes_ano = hoje.strftime("%m.%Y")
            
            # Sequência de cliques com checagem de status
            self.check_status(); pyautogui.click(378, 813)
            self.check_status(); pyautogui.click(coord_unidade[0], coord_unidade[1])
            self.check_status(); pyautogui.click(405, 233)
            
            time.sleep(10) # Carregamento
            
            self.check_status(); pyautogui.click(665, 490)
            pyautogui.write('ESANTAN3')
            self.check_status(); pyautogui.click(1187, 692)
            pyautogui.write('Mosaic@2026')
            self.check_status(); pyautogui.click(1289, 685)
            self.check_status(); pyautogui.click(1480, 204) 
            
            time.sleep(5)
            self.check_status()

            # Navegação e Filtros
            pyautogui.click(542, 75); pyautogui.click(553, 108); pyautogui.click(693, 157)
            
            self.check_status()
            pyautogui.click(69, 204)
            pyautogui.hotkey('ctrl', 'a'); pyautogui.press('backspace')
            pyautogui.write(hoje.strftime("01/%m/%Y"))
            pyautogui.press('tab')

            for campo in [(161, 195), (199, 205), (250, 202)]:
                self.check_status(); pyautogui.click(campo)
                pyautogui.hotkey('ctrl', 'a'); pyautogui.press('backspace')
                pyautogui.write('0')

            self.check_status()
            pyautogui.click(280, 244); pyautogui.click(125, 358) 
            pyautogui.click(1343, 357); pyautogui.click(1298, 401) 
            pyautogui.click(67, 927)

            self.adicionar_log("Download iniciado. Organizando arquivo...")
            self.mover_arquivo(nome_unidade, mes_ano)

        except InterruptedError:
            self.adicionar_log("🛑 Automação PARADA pelo usuário.")
        except Exception as e:
            self.adicionar_log(f"❌ Erro: {str(e)}")
        
        # Reset da Interface
        self.executando = False
        self.after(0, self.deiconify)
        self.btn_iniciar.configure(state="normal")
        self.btn_parar.configure(state="disabled")

    def mover_arquivo(self, nome_unidade, mes_ano):
        tentativas = 0
        while tentativas < 20 and self.executando:
            arquivos = [f for f in os.listdir(CAMINHO_DOWNLOADS) if f.lower().endswith(('.xls', '.xlsx'))]
            if arquivos:
                recente = max([os.path.join(CAMINHO_DOWNLOADS, f) for f in arquivos], key=os.path.getmtime)
                if not recente.endswith(('.tmp', '.crdownload')):
                    t1 = os.path.getsize(recente)
                    time.sleep(2)
                    t2 = os.path.getsize(recente)
                    if t1 == t2 and t1 > 0:
                        novo_nome = f"{nome_unidade} {mes_ano}.xls"
                        destino = os.path.join(CAMINHO_BASE, novo_nome)
                        if os.path.exists(destino): os.remove(destino)
                        shutil.move(recente, destino)
                        self.adicionar_log(f"✅ CONCLUÍDO: {novo_nome}")
                        return
            time.sleep(2)
            tentativas += 1
        if self.executando:
            self.adicionar_log("❌ Arquivo não localizado.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
    