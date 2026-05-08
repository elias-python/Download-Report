import customtkinter as ctk
import pyautogui
import time
import os
import shutil
import json
import subprocess
from datetime import datetime
import threading
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURAÇÕES DE PERFORMANCE ---
pyautogui.PAUSE = 0.2
pyautogui.FAILSAFE = True

# Tenta importar opencv para melhor precisão no locateCenterOnScreen
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# --- CAMINHOS DINÂMICOS (Funciona em qualquer máquina da Mosaic) ---
pasta_usuario = os.environ.get('USERPROFILE')

CAMINHO_ATLAS_EXE = os.path.join(pasta_usuario, 'OneDrive - The Mosaic Company', 'Atlas', 'Atlas_Browser_1.3.3', 'AtlasBrowser.exe')
CAMINHO_DOWNLOADS = os.path.join(pasta_usuario, 'Downloads')

ARQUIVO_CONFIG = "config_atlas_unified.json"

# --- PALETA DE CORES (TEMAS DINÂMICOS) ---
TEMA_DESCARGA     = {"base": "#22577a", "hover": "#22577a"} # Azul
TEMA_CARREGAMENTO = {"base": "#52796f", "hover": "#52796f"} # Laranja
TEMA_AMBOS        = {"base": "#d4d700", "hover": "#d4d700"} # Roxo

COR_FUNDO       = "#F5F4F2"       
COR_CARD        = "#FFFFFF"       
COR_BORDA       = "#E0DDD8"       
COR_TEXTO       = "#1C1C1B"       
COR_MUTED       = "#8A8880"       
COR_TERMINAL_BG = "#1C1C1B"       
COR_TERMINAL_FG = "#A0A09A"
COR_SUCCESS     = "#2D8A4E"
COR_ERROR       = "#C0392B"

CENTROS_IMAGENS = {
    "UBERABA": "assets/uberaba.png",
    "CANDEIAS": "assets/candeias.png",
    "CATALÃO": "assets/catalao.png",
    "SORRISO": "assets/sorriso.png",
    "PGUA 1": "assets/pgua1.png",
    "PGUA 2": "assets/selecionar_pg2.png", 
    "RONDONÓPOLIS": "assets/rondonopolis.png",
    "RIO VERDE": "assets/rioverde.png",
    "RIO GRANDE": "assets/riogrande.png",
    "PALMEIRANTE": "assets/palmeirante.png"
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mosaic Atlas Vision v4.3 - Master")
        self.geometry("650x880") # ALTURA AUMENTADA PARA CABER O NOVO CARD
        self.resizable(False, False)
        self.configure(fg_color=COR_FUNDO)

        self.executando = False
        
        # Carrega as configurações de pasta e credenciais
        config_data = self.carregar_config()
        self.caminho_descarga = config_data.get("caminho_descarga", "")
        self.caminho_carregamento = config_data.get("caminho_carregamento", "")
        self.user_atlas = config_data.get("user_atlas", "")
        self.pass_atlas = config_data.get("pass_atlas", "")
        self.ultima_att = config_data.get("ultima_att", "Nunca")

        self.modo_var = ctk.StringVar(value="📥 Descarga")
        self.tema_atual = TEMA_DESCARGA

        self._build_ui()
        self.atualizar_relogio()
        self.ao_mudar_modo(self.modo_var.get()) 

    def carregar_config(self):
        if os.path.exists(ARQUIVO_CONFIG):
            try:
                with open(ARQUIVO_CONFIG, 'r') as f:
                    return json.load(f)
            except: pass
        return {}

    def salvar_config(self, caminho_desc=None, caminho_carr=None, ultima_att=None, user=None, senha=None):
        dados = self.carregar_config()
        if caminho_desc is not None: dados["caminho_descarga"] = caminho_desc
        if caminho_carr is not None: dados["caminho_carregamento"] = caminho_carr
        if ultima_att is not None: dados["ultima_att"] = ultima_att
        if user is not None: dados["user_atlas"] = user
        if senha is not None: dados["pass_atlas"] = senha
        with open(ARQUIVO_CONFIG, 'w') as f:
            json.dump(dados, f)

    def salvar_credenciais(self):
        user = self.ent_user.get()
        senha = self.ent_pass.get()
        self.salvar_config(user=user, senha=senha)
        self.adicionar_log("Credenciais do Atlas salvas com sucesso!", "suc")

    def selecionar_caminho_base(self):
        modo_atual = self.modo_var.get()
        
        if "Ambos" in modo_atual:
            messagebox.showinfo("Atenção", "Para configurar as pastas, selecione a aba 'Descarga' ou 'Carregamento' individualmente na parte superior.")
            return

        is_descarga = "Descarga" in modo_atual
        caminho = filedialog.askdirectory(title=f"Selecione a pasta destino para {modo_atual}")
        
        if caminho:
            if is_descarga:
                self.caminho_descarga = caminho
                self.salvar_config(caminho_desc=caminho)
            else:
                self.caminho_carregamento = caminho
                self.salvar_config(caminho_carr=caminho)
                
            self._atualizar_dest()
            self.adicionar_log(f"Destino para {modo_atual} salvo: {caminho}", "ok")

    def _atualizar_dest(self):
        modo_atual = self.modo_var.get()
        
        if "Ambos" in modo_atual:
            if self.caminho_descarga and self.caminho_carregamento:
                self.lbl_dest_path.configure(text="✔️ Ambas as pastas estão configuradas corretamente.", text_color=COR_SUCCESS)
                self.lbl_dest_badge.configure(text=" OK ", text_color=COR_SUCCESS, fg_color="#E6F4EC")
            else:
                self.lbl_dest_path.configure(text="⚠️ Falta configurar caminhos. Vá nas abas individuais.", text_color=COR_ERROR)
                self.lbl_dest_badge.configure(text=" ERRO ", text_color=COR_ERROR, fg_color="#FDECEA")
            return

        is_descarga = "Descarga" in modo_atual
        caminho_exibido = self.caminho_descarga if is_descarga else self.caminho_carregamento

        if caminho_exibido:
            self.lbl_dest_path.configure(text=caminho_exibido, text_color=COR_TEXTO)
            self.lbl_dest_badge.configure(text=" OK ", text_color=COR_SUCCESS, fg_color="#E6F4EC")
        else:
            self.lbl_dest_path.configure(text=f"Clique em ⚙ para configurar a pasta de {modo_atual}", text_color=COR_MUTED)
            self.lbl_dest_badge.configure(text="  —  ", text_color=COR_MUTED, fg_color=COR_FUNDO)

    def ao_mudar_modo(self, valor_selecionado):
        if "Descarga" in valor_selecionado:
            self.tema_atual = TEMA_DESCARGA
        elif "Carregamento" in valor_selecionado:
            self.tema_atual = TEMA_CARREGAMENTO
        else:
            self.tema_atual = TEMA_AMBOS

        cor_base = self.tema_atual["base"]
        cor_hover = self.tema_atual["hover"]

        self.logo_box.configure(fg_color=cor_base)
        self.seg_button.configure(selected_color=cor_base, selected_hover_color=cor_hover)
        self.btn_iniciar.configure(fg_color=cor_base, hover_color=cor_hover)
        self.log_text.tag_config("ok", foreground=cor_base) 
        
        for chk in self.checkboxes.values():
            chk.configure(fg_color=cor_base, hover_color=cor_hover)

        self._atualizar_dest()

    def toggle_all(self):
        algum_desmarcado = any(chk.get() == 0 for chk in self.checkboxes.values())
        if algum_desmarcado:
            for chk in self.checkboxes.values(): chk.select()
            self.btn_toggle_all.configure(text="Desmarcar Todos")
        else:
            for chk in self.checkboxes.values(): chk.deselect()
            self.btn_toggle_all.configure(text="Marcar Todos")

    def atualizar_relogio(self):
        agora = datetime.now()
        self.lbl_data.configure(text=agora.strftime("%d/%m/%Y"))
        self.lbl_hora.configure(text=agora.strftime("%H:%M:%S"))
        self.after(1000, self.atualizar_relogio)

    def _build_ui(self):
        PAD = 25 
        
        # ── HEADER & RELÓGIO ───────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD, pady=(20, 5))
        
        self.logo_box = ctk.CTkFrame(header, width=42, height=42, corner_radius=10)
        self.logo_box.pack(side="left")
        self.logo_box.pack_propagate(False)
        ctk.CTkLabel(self.logo_box, text="⊞", font=("Segoe UI", 20, "bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")
        
        txt_frame = ctk.CTkFrame(header, fg_color="transparent")
        txt_frame.pack(side="left", padx=10)
        ctk.CTkLabel(txt_frame, text="Mosaic RDE - Extração de Relatórios", font=("Segoe UI Semibold", 18, "bold"), text_color=COR_TEXTO).pack(anchor="w")
        self.lbl_last_run = ctk.CTkLabel(txt_frame, text=f"Última atualização: {self.ultima_att}", font=("Segoe UI", 12), text_color=COR_MUTED)
        self.lbl_last_run.pack(anchor="w")
        
        relogio_frame = ctk.CTkFrame(header, fg_color="transparent")
        relogio_frame.pack(side="right", anchor="e")
        self.lbl_hora = ctk.CTkLabel(relogio_frame, text="00:00:00", font=("Consolas", 18, "bold"), text_color=COR_TEXTO)
        self.lbl_hora.pack(anchor="e")
        self.lbl_data = ctk.CTkLabel(relogio_frame, text="00/00/0000", font=("Segoe UI", 11), text_color=COR_MUTED)
        self.lbl_data.pack(anchor="e", pady=(0,0))

        # ── CARD: CREDENCIAIS ATLAS (NOVO) ───────────
        card_creds = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_creds.pack(fill="x", padx=PAD, pady=6)
        
        ctk.CTkLabel(card_creds, text="ACESSO AO ATLAS", font=("Segoe UI", 11, "bold"), text_color=COR_MUTED).pack(anchor="w", padx=16, pady=(10, 5))
        
        inputs_frame = ctk.CTkFrame(card_creds, fg_color="transparent")
        inputs_frame.pack(fill="x", padx=12, pady=(0, 10))
        
        self.ent_user = ctk.CTkEntry(inputs_frame, placeholder_text="Usuário (Ex: ESANTAN3)", width=220, height=32)
        self.ent_user.pack(side="left", padx=5)
        self.ent_user.insert(0, self.user_atlas)
        
        self.ent_pass = ctk.CTkEntry(inputs_frame, placeholder_text="Senha", width=220, height=32, show="*")
        self.ent_pass.pack(side="left", padx=5)
        self.ent_pass.insert(0, self.pass_atlas)
        
        self.btn_save_creds = ctk.CTkButton(inputs_frame, text="Salvar", width=80, height=32, fg_color=COR_FUNDO, text_color=COR_TEXTO, hover_color=COR_BORDA, command=self.salvar_credenciais)
        self.btn_save_creds.pack(side="right", padx=5)

        # ── SELETOR DE MODO ───────────
        modo_frame = ctk.CTkFrame(self, fg_color="transparent")
        modo_frame.pack(fill="x", padx=PAD, pady=(10, 5))
        
        self.seg_button = ctk.CTkSegmentedButton(
            modo_frame, 
            values=["📥 Descarga", "📤 Carregamento", "🔄 Ambos"], 
            variable=self.modo_var,
            command=self.ao_mudar_modo, 
            font=("Segoe UI", 14, "bold"),
            unselected_color=COR_CARD,
            unselected_hover_color=COR_FUNDO,
            height=40
        )
        self.seg_button.pack(fill="x", expand=True)

        # ── CARD: PASTA DESTINO ───────────
        card_dest = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_dest.pack(fill="x", padx=PAD, pady=6)
        
        topo_dest = ctk.CTkFrame(card_dest, fg_color="transparent")
        topo_dest.pack(fill="x", padx=16, pady=(10, 2))
        ctk.CTkLabel(topo_dest, text="PASTA DE DESTINO (RAIZ)", font=("Segoe UI", 11, "bold"), text_color=COR_MUTED).pack(side="left")
        self.btn_configurar = ctk.CTkButton(topo_dest, text="⚙ Configurar", width=90, height=24, fg_color=COR_FUNDO, text_color=COR_TEXTO, hover_color=COR_BORDA, command=self.selecionar_caminho_base)
        self.btn_configurar.pack(side="right")
        
        dest_row = ctk.CTkFrame(card_dest, fg_color="transparent")
        dest_row.pack(fill="x", padx=12, pady=(0, 10))
        self.lbl_dest_path = ctk.CTkLabel(dest_row, text="", font=("Consolas", 12), text_color=COR_TEXTO, anchor="w", justify="left", wraplength=450)
        self.lbl_dest_path.pack(side="left", padx=5)
        self.lbl_dest_badge = ctk.CTkLabel(dest_row, text="  —  ", font=("Segoe UI", 11, "bold"), text_color=COR_MUTED, fg_color=COR_FUNDO, corner_radius=6, height=22)
        self.lbl_dest_badge.pack(side="right", padx=5)

        # ── CARD: CONFIGURAÇÃO DE ROTA ───────────
        card_rota = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_rota.pack(fill="x", padx=PAD, pady=6)
        
        topo_rota = ctk.CTkFrame(card_rota, fg_color="transparent")
        topo_rota.pack(fill="x", padx=16, pady=(10, 6))
        ctk.CTkLabel(topo_rota, text="UNIDADES PARA EXTRAÇÃO", font=("Segoe UI", 11, "bold"), text_color=COR_MUTED).pack(side="left")
        
        self.btn_toggle_all = ctk.CTkButton(topo_rota, text="Desmarcar", width=80, height=22, fg_color=COR_FUNDO, text_color=COR_TEXTO, hover_color=COR_BORDA, command=self.toggle_all)
        self.btn_toggle_all.pack(side="right")

        self.frame_checks = ctk.CTkScrollableFrame(card_rota, height=140, fg_color="transparent")
        self.frame_checks.pack(fill="x", padx=12, pady=(0, 5))

        self.checkboxes = {}
        for centro in CENTROS_IMAGENS.keys():
            chk = ctk.CTkCheckBox(self.frame_checks, text=centro, font=("Segoe UI", 13), text_color=COR_TEXTO)
            chk.pack(anchor="w", pady=5, padx=5)
            chk.select()
            self.checkboxes[centro] = chk

        self.lbl_unidade_status = ctk.CTkLabel(card_rota, text="Pronto para iniciar.", font=("Segoe UI", 12), text_color=COR_MUTED, anchor="w")
        self.lbl_unidade_status.pack(fill="x", padx=16, pady=(0, 10))
        
        self.btn_iniciar = ctk.CTkButton(card_rota, text="▶   Iniciar Automação", height=50, corner_radius=10, text_color="white", font=("Segoe UI Semibold", 15, "bold"), command=self.start_thread)
        self.btn_iniciar.pack(fill="x", padx=12, pady=(0, 14))

        # ── CARD: TERMINAL GIGANTE ───────────
        card_log = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_log.pack(fill="both", expand=True, padx=PAD, pady=(6, 20))
        
        log_header = ctk.CTkFrame(card_log, fg_color="transparent")
        log_header.pack(fill="x", padx=16, pady=(10, 6))
        ctk.CTkLabel(log_header, text="TERMINAL DE LOGS", font=("Segoe UI", 11, "bold"), text_color=COR_MUTED).pack(side="left")
        ctk.CTkButton(log_header, text="Limpar", width=60, height=24, corner_radius=6, fg_color="transparent", hover_color=COR_FUNDO, border_width=0, text_color=COR_MUTED, font=("Segoe UI", 11), command=self.limpar_log).pack(side="right")
        
        self.log_text = ctk.CTkTextbox(card_log, fg_color=COR_TERMINAL_BG, text_color=COR_TERMINAL_FG, font=("Consolas", 12), border_width=0, corner_radius=8, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.log_text.tag_config("err", foreground=COR_ERROR)
        self.log_text.tag_config("suc", foreground=COR_SUCCESS)

    def adicionar_log(self, msg, tipo=None):
        hora = datetime.now().strftime("%H:%M:%S")
        def update():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"[{hora}] ", "ok" if tipo else None)
            tag = tipo if tipo in ("ok", "err", "suc") else None
            self.log_text.insert("end", f"{msg}\n", tag)
            self.log_text.configure(state="disabled")
            self.log_text.see("end")
        self.after(0, update)

    def limpar_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _set_unidade_status(self, text): 
        self.after(0, lambda: self.lbl_unidade_status.configure(text=text))

    def clicar_img(self, img, desc, timeout=15, max_tentativas=4, confidence=0.7, double=False, click_type="standard"):
        for tentativa in range(1, max_tentativas + 1):
            self.adicionar_log(f"Buscando: {desc} ({tentativa}/{max_tentativas})")
            inicio = time.time()
            
            while time.time() - inicio < timeout:
                if not self.executando:
                    return False
                try:
                    pos = None
                    if desc == "Botão Iniciar":
                        screen_width, screen_height = pyautogui.size()
                        search_region = (0, 0, screen_width // 2, screen_height // 2)
                        pos = pyautogui.locateCenterOnScreen(img, confidence=confidence, region=search_region)
                    else:
                        pos = pyautogui.locateCenterOnScreen(img, confidence=confidence)
                    
                    if pos:
                        if click_type == "force":
                            pyautogui.moveTo(pos.x, pos.y, duration=0.2)
                            pyautogui.mouseDown()
                            time.sleep(0.1)
                            pyautogui.mouseUp()
                            time.sleep(0.3)
                        elif double:
                            pyautogui.doubleClick(pos)
                        else:
                            pyautogui.click(pos)
                        self.adicionar_log(f"{desc} encontrado!", "ok")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            
            if tentativa < max_tentativas:
                self.adicionar_log("Timeout: Tentando fechar pop-up com [ESC]...", "err")
                pyautogui.press('esc') 
                time.sleep(2)
        
        self.adicionar_log(f"ERRO: '{desc}' não encontrado. Abortando etapa.", "err")
        return False

    def fechar_atlas(self):
        self.adicionar_log("Fechando Atlas Browser...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "AtlasBrowser.exe"], capture_output=True, text=True, check=False)
            time.sleep(2)
        except: pass

    def start_thread(self):
        user_atual = self.ent_user.get().strip()
        pass_atual = self.ent_pass.get().strip()

        if not user_atual or not pass_atual:
            messagebox.showwarning("Atenção", "Preencha o Usuário e Senha do Atlas antes de iniciar.")
            return

        modo_atual = self.modo_var.get()
        
        # Verificação de Segurança de Caminhos
        if "Ambos" in modo_atual:
            if not self.caminho_descarga or not self.caminho_carregamento:
                messagebox.showwarning("Atenção", "Para rodar Ambos, configure as duas pastas nas abas individuais primeiro.")
                return
        else:
            is_descarga = "Descarga" in modo_atual
            caminho_requirido = self.caminho_descarga if is_descarga else self.caminho_carregamento
            if not caminho_requirido or not os.path.exists(caminho_requirido):
                messagebox.showwarning("Atenção", f"Configure a pasta de destino para {modo_atual} primeiro.")
                return
        
        self.executando = True
        self.seg_button.configure(state="disabled")
        self.btn_configurar.configure(state="disabled")
        self.btn_iniciar.configure(state="disabled", text="⏹   Executando...")
        self.ent_user.configure(state="disabled")
        self.ent_pass.configure(state="disabled")
        self.btn_save_creds.configure(state="disabled")
        
        threading.Thread(target=self.executar_sequencial, daemon=True).start()

    def executar_sequencial(self):
        centros_selecionados = [centro for centro, chk in self.checkboxes.items() if chk.get() == 1]

        if not centros_selecionados:
            self.adicionar_log("Nenhuma unidade selecionada para execução.", "err")
            self.finalizar_execucao(total=0)
            return

        # Define quais rotinas vão rodar
        modo_geral = self.modo_var.get()
        if "Ambos" in modo_geral:
            modos_a_rodar = ["Descarga", "Carregamento"]
        elif "Descarga" in modo_geral:
            modos_a_rodar = ["Descarga"]
        else:
            modos_a_rodar = ["Carregamento"]

        total_execucoes = len(centros_selecionados) * len(modos_a_rodar)
        sucessos = 0
        falhas = 0
        lista_falhas = []
        contador = 0

        self.adicionar_log(f"--- INICIANDO MODO {modo_geral.upper()} ({total_execucoes} tarefas) ---", "ok")

        for centro in centros_selecionados:
            for modo_especifico in modos_a_rodar:
                if not self.executando: break
                
                contador += 1
                self._set_unidade_status(f"[{contador}/{total_execucoes}] {centro} ({modo_especifico}): Extraindo...")
                self.adicionar_log(f"\n--- Iniciando: {centro} | Rota: {modo_especifico} ---")
                
                if self.executar_robo(centro, modo_especifico):
                    self.adicionar_log(f"✅ Sucesso: {centro} ({modo_especifico})", "suc")
                    sucessos += 1
                else:
                    self.adicionar_log(f"❌ Falha: {centro} ({modo_especifico}).", "err")
                    falhas += 1
                    lista_falhas.append(f"{centro} ({modo_especifico})")
                
                self.fechar_atlas()
                time.sleep(1)
            
        self.finalizar_execucao(total=total_execucoes, suc=sucessos, fal=falhas, lista_fal=lista_falhas)

    def finalizar_execucao(self, total=0, suc=0, fal=0, lista_fal=None):
        self.executando = False
        self._set_unidade_status("Processo Finalizado.")
        
        if total > 0:
            agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
            self.ultima_att = agora_str
            self.salvar_config(ultima_att=agora_str)
            self.after(0, lambda: self.lbl_last_run.configure(text=f"Última atualização: {self.ultima_att}"))
        
        self.after(0, lambda: self.seg_button.configure(state="normal"))
        self.after(0, lambda: self.btn_configurar.configure(state="normal"))
        self.after(0, lambda: self.ent_user.configure(state="normal"))
        self.after(0, lambda: self.ent_pass.configure(state="normal"))
        self.after(0, lambda: self.btn_save_creds.configure(state="normal"))
        self.after(0, lambda: self.btn_iniciar.configure(state="normal", text="▶   Iniciar Automação"))
        
        if total > 0:
            self.after(0, lambda: self.mostrar_resumo(total, suc, fal, lista_fal))

    def mostrar_resumo(self, total, sucessos, falhas, lista_falhas):
        modal = ctk.CTkToplevel(self)
        modal.title("Resumo da Automação")
        modal.geometry("450x420")
        modal.resizable(False, False)
        modal.configure(fg_color=COR_FUNDO)
        modal.transient(self) 
        modal.grab_set() 
        
        taxa_sucesso = (sucessos / total) * 100 if total > 0 else 0
        
        if taxa_sucesso == 100:
            cor_destaque = COR_SUCCESS; icone = "✅"; titulo_texto = "100% CONCLUÍDO!"; msg_texto = "Todos os relatórios foram extraídos."
        elif taxa_sucesso > 0:
            cor_destaque = self.tema_atual["base"]; icone = "⚠️"; titulo_texto = "CONCLUÍDO COM AVISOS"; msg_texto = "Algumas etapas falharam, verifique a lista."
        else:
            cor_destaque = COR_ERROR; icone = "❌"; titulo_texto = "FALHA CRÍTICA"; msg_texto = "Nenhuma etapa foi concluída com sucesso."

        header = ctk.CTkFrame(modal, fg_color=cor_destaque, corner_radius=0, height=80)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=icone, font=("Segoe UI", 36)).pack(side="left", padx=(20, 10))
        txt_frame = ctk.CTkFrame(header, fg_color="transparent")
        txt_frame.pack(side="left", pady=15)
        ctk.CTkLabel(txt_frame, text=titulo_texto, font=("Segoe UI", 18, "bold"), text_color="#FFF").pack(anchor="w")
        ctk.CTkLabel(txt_frame, text=msg_texto, font=("Segoe UI", 12), text_color="#FFF").pack(anchor="w")

        corpo = ctk.CTkFrame(modal, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=20, pady=20)

        stats_frame = ctk.CTkFrame(corpo, fg_color=COR_CARD, corner_radius=10, border_width=1, border_color=COR_BORDA)
        stats_frame.pack(fill="x", pady=(0, 15))
        
        col1 = ctk.CTkFrame(stats_frame, fg_color="transparent")
        col1.pack(side="left", expand=True, pady=10)
        ctk.CTkLabel(col1, text=f"{sucessos}", font=("Segoe UI", 24, "bold"), text_color=COR_SUCCESS).pack()
        ctk.CTkLabel(col1, text="Sucessos", font=("Segoe UI", 12), text_color=COR_MUTED).pack()

        col2 = ctk.CTkFrame(stats_frame, fg_color="transparent")
        col2.pack(side="left", expand=True, pady=10)
        ctk.CTkLabel(col2, text=f"{falhas}", font=("Segoe UI", 24, "bold"), text_color=COR_ERROR if falhas > 0 else COR_TEXTO).pack()
        ctk.CTkLabel(col2, text="Falhas", font=("Segoe UI", 12), text_color=COR_MUTED).pack()

        col3 = ctk.CTkFrame(stats_frame, fg_color="transparent")
        col3.pack(side="left", expand=True, pady=10)
        ctk.CTkLabel(col3, text=f"{total}", font=("Segoe UI", 24, "bold"), text_color=COR_TEXTO).pack()
        ctk.CTkLabel(col3, text="Total", font=("Segoe UI", 12), text_color=COR_MUTED).pack()

        if falhas > 0:
            falhas_txt = ", ".join(lista_falhas)
            aviso_frame = ctk.CTkFrame(corpo, fg_color="#FDECEA", corner_radius=8)
            aviso_frame.pack(fill="x", pady=(0, 15))
            ctk.CTkLabel(aviso_frame, text="Pendências:", font=("Segoe UI", 10, "bold"), text_color=COR_ERROR).pack(anchor="w", padx=10, pady=(8,0))
            ctk.CTkLabel(aviso_frame, text=falhas_txt, font=("Segoe UI", 11), text_color=COR_ERROR, wraplength=370, justify="left").pack(anchor="w", padx=10, pady=(0,8))

        btn_fechar = ctk.CTkButton(modal, text="Entendido 👍", height=40, fg_color=COR_TEXTO, hover_color="#333", command=modal.destroy)
        btn_fechar.pack(side="bottom", pady=0, padx=20, fill="x")

    def executar_robo(self, unidade, modo_especifico):
        is_descarga = modo_especifico == "Descarga"
        user_atual = self.ent_user.get().strip()
        pass_atual = self.ent_pass.get().strip()

        try:
            self.after(0, self.iconify)
            
            if unidade in ["PGUA 1", "PGUA 2"]:
                os.startfile(CAMINHO_ATLAS_EXE)
                
                if not self.clicar_img("assets/selectcenter.png", "Seletor de centro", timeout=40): return False
                if not self.clicar_img(CENTROS_IMAGENS["PGUA 1"], "PGUA 1 (Login)"): return False
                if not self.clicar_img("assets/atlas_cargo.png", "Botão Iniciar", timeout=15, click_type="force"): return False

                if self.clicar_img("assets/user.png", "Campo usuário", timeout=15):
                    pyautogui.write(user_atual)
                    if not self.clicar_img("assets/senha.png", "Campo senha"): return False
                    pyautogui.write(pass_atual)
                    pyautogui.press('enter')
                else:
                    return False
                
                time.sleep(2)
                
                if self.clicar_img("assets/abrir_botaopg2.png", "Botão Seletor Interno", timeout=15):
                    time.sleep(1) 
                    
                    if unidade == "PGUA 1":
                        pyautogui.press('down')
                        time.sleep(0.5)
                        pyautogui.press('enter')
                    else:
                        pyautogui.press('up')
                        pyautogui.press('up') 
                        time.sleep(0.5)
                        pyautogui.press('enter')
                else:
                    return False
            
            else:
                os.startfile(CAMINHO_ATLAS_EXE)
                
                if not self.clicar_img("assets/selectcenter.png", "Seletor de centro", timeout=40): return False
                if not self.clicar_img(CENTROS_IMAGENS[unidade], unidade): return False
                if not self.clicar_img("assets/atlas_cargo.png", "Botão Iniciar", timeout=15, click_type="force"): return False

                if self.clicar_img("assets/user.png", "Campo usuário", timeout=15):
                    pyautogui.write(user_atual)
                    if not self.clicar_img("assets/senha.png", "Campo senha"): return False
                    pyautogui.write(pass_atual)
                    pyautogui.press('enter')
                else:
                    return False

            time.sleep(2)
            
            if unidade in ["CATALÃO", "PALMEIRANTE"]:
                if not self.clicar_img("assets/impressao_catalao.png", "Menu Impressão", timeout=25): return False
                if not self.clicar_img("assets/relatorio_catalao.png", "Menu Relatórios"): return False
            else:
                if not self.clicar_img("assets/impressao.png", "Menu Impressão", timeout=25): return False
                if not self.clicar_img("assets/relatorios.png", "Menu Relatórios"): return False
            
            if unidade == "UBERABA":
                if not self.clicar_img("assets/relatorios_ubr.png", "Relatórios UBR"): return False
            else:
                if not self.clicar_img("assets/relatordiariobal.png", "Relatório Balança"): return False
            
            hoje = datetime.now()
            primeiro_dia = hoje.strftime("01/%m/%Y")
            
            if self.clicar_img("assets/secao_data_inicial.png", "Data inicial", double=True):
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')
                pyautogui.write(primeiro_dia)
                pyautogui.press('tab')
                for _ in range(3):
                    pyautogui.hotkey('ctrl', 'a')
                    pyautogui.write('0')
                    pyautogui.press('tab')
            else:
                return False
                    
            if unidade in ["UBERABA", "RONDONÓPOLIS"]:
                if self.clicar_img("assets/selectfluxo.png", "Fluxo"):
                    palavra_fluxo = "DESCARGA" if is_descarga else "CARREGAMENTO"
                    pyautogui.write(palavra_fluxo)
                    pyautogui.press('down')
                    pyautogui.press('enter')
                else:
                    return False
            else:
                if self.clicar_img("assets/selectrota.png", "Rota"):
                    if is_descarga:
                        achou_rota = False
                        for img, nome in [("assets/rota_descarga.png", "Recepção"), ("assets/rota_descarga2.png", "RECEPÇÃO")]:
                            if self.clicar_img(img, nome, timeout=2, max_tentativas=1):
                                achou_rota = True
                                break
                        if not achou_rota: return False
                    else:
                        if not self.clicar_img("assets/rota_exped.png", "Expedição"): return False
                else:
                    return False

            if not self.clicar_img("assets/selecttype.png", "Tipo de saída"): return False
            time.sleep(1) 
            
            if not self.clicar_img("assets/tipo_excel.png", "Excel"): return False
            time.sleep(1.5) 
            
            if not self.clicar_img("assets/gerar_relatorio.png", "Gerar relatório"): return False
            
            if not self.mover_arquivo(unidade, hoje.strftime("%m.%Y"), is_descarga): return False
            
            return True
            
        except Exception as e:
            self.adicionar_log(f"Erro Crítico: {str(e)}", "err")
            return False

    def mover_arquivo(self, unidade, mes_ano, is_descarga):
        tempo_inicio = time.time()
        
        nomes_carregamento = {
            "PGUA 1": "Paranagua 1", "PGUA 2": "Paranagua 2", "UBERABA": "Uberaba", 
            "SORRISO": "Sorriso", "RONDONÓPOLIS": "Rondonópolis", "RIO VERDE": "Rio Verde", 
            "RIO GRANDE": "Rio Grande", "CATALÃO": "Catalão", "CANDEIAS": "Candeias",
            "PALMEIRANTE": "Palmeirante"
        }
        
        numeros_descarga = {
            "PGUA 1": "4020", "CANDEIAS": "4040", "SORRISO": "4060", "RIO VERDE": "4070",
            "CATALÃO": "4100", "RONDONÓPOLIS": "4110", "UBERABA": "4120", "PGUA 2": "4130",
            "RIO GRANDE": "4140", "PALMEIRANTE": "4170"
        }
        
        for _ in range(60):
            if not self.executando: return False
            arquivos = [f for f in os.listdir(CAMINHO_DOWNLOADS) if f.lower().endswith(('.xls', '.xlsx'))]
            
            if arquivos:
                caminho_recente = max([os.path.join(CAMINHO_DOWNLOADS, f) for f in arquivos], key=os.path.getmtime)
                
                if os.path.getmtime(caminho_recente) < tempo_inicio:
                    time.sleep(1)
                    continue
                    
                nome_original = os.path.basename(caminho_recente)
                if not nome_original.endswith(('.tmp', '.crdownload')):
                    time.sleep(2) 
                    try:
                        extensao = os.path.splitext(nome_original)[1]
                        
                        if is_descarga:
                            num_centro = numeros_descarga.get(unidade, "0000")
                            novo_nome = f"{mes_ano} - {num_centro} RelPesagensDiarioBalancaRoo{extensao}"
                            pasta_destino = os.path.join(self.caminho_descarga, num_centro)
                            os.makedirs(pasta_destino, exist_ok=True) 
                            destino_final = os.path.join(pasta_destino, novo_nome)
                        else:
                            nome_exib = nomes_carregamento.get(unidade, unidade)
                            novo_nome = f"{nome_exib} {mes_ano}{extensao}"
                            destino_final = os.path.join(self.caminho_carregamento, novo_nome)
                        
                        if os.path.exists(destino_final):
                            os.remove(destino_final)
                        shutil.move(caminho_recente, destino_final)
                        self.adicionar_log(f"Salvo: {novo_nome}", "suc")
                        return True
                    except Exception as e:
                        self.adicionar_log(f"Falha ao mover arquivo: {str(e)}", "err")
            time.sleep(1)
            
        self.adicionar_log("Timeout: Excel não apareceu no Downloads.", "err")
        return False

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    try:
        App().mainloop()
    except Exception as e:
        print(f"Erro fatal ao abrir: {e}")