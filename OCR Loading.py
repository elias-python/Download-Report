import customtkinter as ctk
import pyautogui
import time
import os
import shutil
import json
from datetime import datetime
import threading
from tkinter import messagebox, filedialog
from PIL import Image

# --- CONFIGURAÇÕES DE PERFORMANCE ---
pyautogui.PAUSE = 0.2 
pyautogui.FAILSAFE = True 

CAMINHO_ATLAS_EXE = r"C:\Users\esantan3\OneDrive - The Mosaic Company\Atlas\Atlas_Browser_1.3.3\AtlasBrowser.exe"
CAMINHO_DOWNLOADS = r'C:\Users\esantan3\Downloads'
ARQUIVO_CONFIG = "config_atlas.json"

# --- PALETA NEON MOSAIC ---
COR_DESTAQUE = "#FF8C00"
COR_FUNDO = "#1A1A1B"
COR_PAINEL = "#2D2D2E"

CENTROS_IMAGENS = {
    "UBERABA": "assets/uberaba.png",
    "CANDEIAS": "assets/candeias.png",
    "CATALÃO": "assets/catalao.png",
    "SORRISO": "assets/sorriso.png",
    "PGUA 1": "assets/pgua1.png",
    "RONDONÓPOLIS": "assets/rondonopolis.png",
    "RIO VERDE": "assets/rioverde.png",
    "RIO GRANDE": "assets/riogrande.png"
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mosaic Atlas Vision Pro")
        self.geometry("520x780")
        self.configure(fg_color=COR_FUNDO)
        self.executando = False 
        
        self.caminho_base = self.carregar_config()

        # --- HEADER ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(pady=20, padx=20, fill="x")
        
        try:
            # Carrega a logo mosaic_R_blk_1c_rgb_med.jpg
            img_logo = Image.open("mosaic_R_blk_1c_rgb_med.jpg")
            self.logo_mosaic = ctk.CTkImage(img_logo, size=(160, 80)) # Ajustado para a proporção da imagem
            ctk.CTkLabel(self.header, image=self.logo_mosaic, text="").pack(side="left")
        except:
            ctk.CTkLabel(self.header, text="MOSAIC", font=("Orbitron", 26, "bold"), text_color=COR_DESTAQUE).pack(side="left")

        # Botão de engrenagem para configurar o caminho
        self.btn_config = ctk.CTkButton(self.header, text="⚙️", width=40, fg_color=COR_PAINEL, hover_color="#444",
                                        command=self.selecionar_caminho_base)
        self.btn_config.pack(side="right")

        # --- PAINEL PRINCIPAL ---
        self.main_frame = ctk.CTkFrame(self, fg_color=COR_PAINEL, corner_radius=15, border_width=2, border_color=COR_DESTAQUE)
        self.main_frame.pack(pady=10, padx=30, fill="both")

        ctk.CTkLabel(self.main_frame, text="CONFIGURAÇÃO DE ROTA", font=("Roboto", 16, "bold")).pack(pady=10)

        self.lbl_path = ctk.CTkLabel(self.main_frame, text=f"Destino: {self.obter_caminho_curto()}", 
                                     font=("Roboto", 10), text_color="#aaa")
        self.lbl_path.pack(pady=2)

        self.combo_unidades = ctk.CTkComboBox(self.main_frame, values=list(CENTROS_IMAGENS.keys()), 
                                             width=300, height=35, corner_radius=10, border_color=COR_DESTAQUE)
        self.combo_unidades.pack(pady=15)

        self.btn_iniciar = ctk.CTkButton(self.main_frame, text="INICIAR AUTOMAÇÃO ⚡", command=self.start_thread,
                                        fg_color=COR_DESTAQUE, hover_color="#e67e00", font=("Roboto", 14, "bold"), height=45)
        self.btn_iniciar.pack(pady=20, padx=40, fill="x")

        # --- LOG TERMINAL (Agora Blindado contra escrita!) ---
        self.log_text = ctk.CTkTextbox(self, fg_color="#000", text_color="#0F0", font=("Consolas", 12), 
                                      border_width=1, border_color="#333", state="disabled")
        self.log_text.pack(pady=20, padx=30, fill="both", expand=True)
        self.log_text.tag_config("sucesso", foreground=COR_DESTAQUE)

    def carregar_config(self):
        if os.path.exists(ARQUIVO_CONFIG):
            with open(ARQUIVO_CONFIG, 'r') as f:
                return json.load(f).get("caminho_base", "")
        return ""

    def salvar_config(self, caminho):
        with open(ARQUIVO_CONFIG, 'w') as f:
            json.dump({"caminho_base": caminho}, f)

    def selecionar_caminho_base(self):
        caminho = filedialog.askdirectory(title="Selecione a pasta de destino final (G:)")
        if caminho:
            self.caminho_base = caminho
            self.salvar_config(caminho)
            self.lbl_path.configure(text=f"Destino: {self.obter_caminho_curto()}")
            self.adicionar_log(f"Pasta destino alterada para: {caminho}")

    def obter_caminho_curto(self):
        if not self.caminho_base: return "Clique na ⚙️ para configurar!"
        return f"...{self.caminho_base[-35:]}" if len(self.caminho_base) > 35 else self.caminho_base

    def adicionar_log(self, msg, tipo=None):
        hora = datetime.now().strftime("%H:%M:%S")
        def update():
            # Habilita para o Python escrever, depois bloqueia para o usuário
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"[{hora}] ", "sucesso" if tipo=="OK" else None)
            self.log_text.insert("end", f"{msg}\n")
            self.log_text.configure(state="disabled")
            self.log_text.see("end")
        self.after(0, update)

    def clicar_img(self, img, desc, timeout=20, confidence=0.7, double=False):
        self.adicionar_log(f"🔍 Buscando: {desc}")
        inicio = time.time()
        while time.time() - inicio < timeout:
            if not self.executando: return False
            try:
                # Localiza a imagem na tela (como a setinha do ComboBox)
                pos = pyautogui.locateCenterOnScreen(img, confidence=confidence)
                if pos:
                    if double: pyautogui.doubleClick(pos)
                    else: pyautogui.click(pos)
                    self.adicionar_log(f"-> {desc} OK!", "OK")
                    return True
            except: pass
            time.sleep(0.1)
        return False

    def start_thread(self):
        if not self.caminho_base or not os.path.exists(self.caminho_base):
            messagebox.showwarning("Atenção", "Configure a pasta de destino na engrenagem ⚙️ primeiro.")
            return
        self.executando = True
        self.btn_iniciar.configure(state="disabled")
        threading.Thread(target=self.executar_robo, daemon=True).start()

    def executar_robo(self):
        try:
            unidade = self.combo_unidades.get()
            self.after(0, self.iconify)
            os.startfile(CAMINHO_ATLAS_EXE)
            
            if not self.clicar_img("assets/selectcenter.png", "Seletor", timeout=30): raise Exception("Atlas off")
            self.clicar_img(CENTROS_IMAGENS[unidade], unidade)
            self.clicar_img("assets/iniciar.png", "Botão Iniciar")
            
            if self.clicar_img("assets/user.png", "Usuário", timeout=15):
                pyautogui.write('ESANTAN3')
                self.clicar_img("assets/senha.png", "Senha")
                pyautogui.write('Mosaic@2026')
                pyautogui.press('enter')
            
            self.clicar_img("assets/impressao.png", "Menu Impressão", timeout=25)
            self.clicar_img("assets/relatorios.png", "Menu Relatórios")
            
            if unidade == "UBERABA":
                self.clicar_img("assets/relatorios_ubr.png", "Relatórios UBR")
            else:
                self.clicar_img("assets/relatordiariobal.png", "Balança")

            hoje = datetime.now()
            primeiro_dia = hoje.strftime("01/%m/%Y")
            if self.clicar_img("assets/secao_data_inicial.png", "Data", double=True):
                pyautogui.hotkey('ctrl', 'a'); pyautogui.press('backspace')
                pyautogui.write(primeiro_dia); pyautogui.press('tab')
                for _ in range(3): pyautogui.hotkey('ctrl', 'a'); pyautogui.write('0'); pyautogui.press('tab')

            if unidade in ["UBERABA", "RONDONÓPOLIS"]:
                if self.clicar_img("assets/selectfluxo.png", "Fluxo"):
                    pyautogui.write("CARREGAMENTO"); pyautogui.press('down'); pyautogui.press('enter')
            else:
                if self.clicar_img("assets/selectrota.png", "Rota"): 
                    self.clicar_img("assets/rota_exped.png", "Expedição")

            self.clicar_img("assets/selecttype.png", "Tipo Saída")
            self.clicar_img("assets/tipo_excel.png", "Excel")
            self.clicar_img("assets/gerar_relatorio.png", "Gerar")
                 
            self.adicionar_log("📂 Aguardando arquivo no Downloads...")
            self.mover_arquivo(unidade, hoje.strftime("%m.%Y"))

        except Exception as e:
            self.adicionar_log(f"❌ ERRO: {str(e)}")
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.executando = False
            self.after(0, self.deiconify)
            self.after(0, lambda: self.btn_iniciar.configure(state="normal"))

    def mover_arquivo(self, unidade, mes_ano):
        nomes = {"PGUA 1": "Paranagua 1", "UBERABA": "Uberaba", "SORRISO": "Sorriso", 
                 "RONDONÓPOLIS": "Rondonópolis", "RIO VERDE": "Rio Verde", 
                 "RIO GRANDE": "Rio Grande", "CATALÃO": "Catalão", "CANDEIAS": "Candeias"}
        nome_exibicao = nomes.get(unidade, unidade)

        for _ in range(60): 
            if not self.executando: return
            arquivos = [f for f in os.listdir(CAMINHO_DOWNLOADS) if f.lower().endswith(('.xls', '.xlsx'))]
            
            if arquivos:
                # Aqui definimos o caminho_recente para evitar o erro de variável
                caminho_recente = max([os.path.join(CAMINHO_DOWNLOADS, f) for f in arquivos], key=os.path.getmtime)
                nome_original = os.path.basename(caminho_recente)
                
                if not nome_original.endswith(('.tmp', '.crdownload')):
                    time.sleep(2) 
                    try:
                        extensao = os.path.splitext(nome_original)[1]
                        novo_nome = f"{nome_exibicao} {mes_ano}{extensao}"
                        destino_final = os.path.join(self.caminho_base, novo_nome)
                        
                        if os.path.exists(destino_final): os.remove(destino_final)
                        shutil.move(caminho_recente, destino_final)
                        self.adicionar_log(f"✅ SUCESSO: {novo_nome}", "OK")
                        return
                    except Exception as e:
                        self.adicionar_log(f"⚠️ Tentando mover... {str(e)}")
            time.sleep(1)
        self.adicionar_log("❌ Tempo esgotado: Arquivo não encontrado.")

if __name__ == "__main__":
    App().mainloop()