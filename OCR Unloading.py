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

CAMINHO_ATLAS_EXE = r"C:\Users\esantan3\OneDrive - The Mosaic Company\Atlas\Atlas_Browser_1.3.3\AtlasBrowser.exe"
CAMINHO_DOWNLOADS = r'C:\Users\esantan3\Downloads'
ARQUIVO_CONFIG = "config_atlas_recepcao.json" 

# --- PALETA ---
COR_LARANJA     = "#128BD1" 
COR_LARANJA_H   = "#1596c9"
COR_LARANJA_BG  = "#1C1C1B"
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

STEPS = ["Abrir Atlas", "Login", "Relatório", "Configurar", "Exportar", "Mover arquivo"]


class StepBar(ctk.CTkFrame):
    """Barra de progresso por etapas customizada."""
    def __init__(self, master, steps, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.steps = steps
        self.labels = []
        self.dots = []
        self.lines = []
        self._build()

    def _build(self):
        for i, step in enumerate(self.steps):
            col = i * 2
            dot = ctk.CTkLabel(
                self, text="●", font=("Consolas", 14),
                text_color=COR_BORDA, width=18
            )
            dot.grid(row=0, column=col, padx=(0, 0))
            self.dots.append(dot)

            lbl = ctk.CTkLabel(
                self, text=step, font=("Segoe UI", 10),
                text_color=COR_MUTED
            )
            lbl.grid(row=1, column=col, padx=(0, 0))
            self.labels.append(lbl)

            if i < len(self.steps) - 1:
                line = ctk.CTkLabel(
                    self, text="──────", font=("Consolas", 10),
                    text_color=COR_BORDA
                )
                line.grid(row=0, column=col + 1, padx=2)
                self.lines.append(line)

        for i in range(len(self.steps) * 2 - 1):
            self.columnconfigure(i, weight=1)

    def reset(self):
        for dot in self.dots:
            dot.configure(text_color=COR_BORDA)
        for lbl in self.labels:
            lbl.configure(text_color=COR_MUTED)
        for line in self.lines:
            line.configure(text_color=COR_BORDA)

    def set_step(self, idx, state="active"):
        color_map = {"active": COR_LARANJA, "done": COR_SUCCESS, "idle": COR_BORDA}
        text_map  = {"active": COR_TEXTO,   "done": COR_MUTED,   "idle": COR_MUTED}
        self.dots[idx].configure(text_color=color_map[state])
        self.labels[idx].configure(text_color=text_map[state])
        if state == "done" and idx < len(self.lines):
            self.lines[idx].configure(text_color=COR_SUCCESS)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mosaic Atlas Vision v2.6 - Recepção")
        self.geometry("500x820")
        self.resizable(False, False)
        self.configure(fg_color=COR_FUNDO)

        self.executando = False
        self.caminho_base = self.carregar_config()

        self._build_ui()

    def carregar_config(self):
        if os.path.exists(ARQUIVO_CONFIG):
            try:
                with open(ARQUIVO_CONFIG, 'r') as f:
                    return json.load(f).get("caminho_base", "")
            except: pass
        return ""

    def salvar_config(self, caminho):
        with open(ARQUIVO_CONFIG, 'w') as f:
            json.dump({"caminho_base": caminho}, f)

    def selecionar_caminho_base(self):
        caminho = filedialog.askdirectory(title="Selecione a pasta de destino final (onde ficam as pastas dos centros)")
        if caminho:
            self.caminho_base = caminho
            self.salvar_config(caminho)
            self._atualizar_dest()
            self.adicionar_log(f"Destino raiz salvo: {caminho}", "ok")

    def _atualizar_dest(self):
        if self.caminho_base:
            self.lbl_dest_path.configure(text=self.caminho_base, text_color=COR_TEXTO)
            self.lbl_dest_hint.configure(text="Caminho raiz configurado")
            self.lbl_dest_badge.configure(text=" OK ", text_color=COR_SUCCESS, fg_color="#E6F4EC", corner_radius=6)
        else:
            self.lbl_dest_path.configure(text="Clique em ⚙  para configurar", text_color=COR_MUTED)
            self.lbl_dest_hint.configure(text="Nenhum caminho definido")
            self.lbl_dest_badge.configure(text="  —  ", text_color=COR_MUTED, fg_color=COR_FUNDO, corner_radius=6)

    def toggle_all(self):
        algum_desmarcado = any(chk.get() == 0 for chk in self.checkboxes.values())
        if algum_desmarcado:
            for chk in self.checkboxes.values(): chk.select()
            self.btn_toggle_all.configure(text="Desmarcar Todos")
        else:
            for chk in self.checkboxes.values(): chk.deselect()
            self.btn_toggle_all.configure(text="Marcar Todos")

    def _build_ui(self):
        PAD = 20
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD, pady=(20, 10))
        
        logo_box = ctk.CTkFrame(header, fg_color=COR_LARANJA, width=42, height=42, corner_radius=10)
        logo_box.pack(side="left")
        logo_box.pack_propagate(False)
        ctk.CTkLabel(logo_box, text="⊞", font=("Segoe UI", 20, "bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")
        
        txt_frame = ctk.CTkFrame(header, fg_color="transparent")
        txt_frame.pack(side="left", padx=10)
        ctk.CTkLabel(txt_frame, text="Mosaic Atlas OCR - Recepção", font=("Segoe UI Semibold", 16, "bold"), text_color=COR_TEXTO).pack(anchor="w")
        ctk.CTkLabel(txt_frame, text="Automação Inteligente", font=("Segoe UI", 11), text_color=COR_MUTED).pack(anchor="w")
        
        ctk.CTkButton(header, text="⚙", width=36, height=36, corner_radius=8, fg_color=COR_CARD, hover_color=COR_FUNDO, border_width=1, border_color=COR_BORDA, text_color=COR_MUTED, font=("Segoe UI", 16), command=self.selecionar_caminho_base).pack(side="right")
        
        card_dest = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_dest.pack(fill="x", padx=PAD, pady=6)
        ctk.CTkLabel(card_dest, text="PASTA DE DESTINO (RAIZ)", font=("Segoe UI", 10, "bold"), text_color=COR_MUTED).pack(anchor="w", padx=16, pady=(14, 6))
        
        dest_row = ctk.CTkFrame(card_dest, fg_color=COR_FUNDO, corner_radius=8, border_width=1, border_color=COR_BORDA)
        dest_row.pack(fill="x", padx=12, pady=(0, 14))
        ctk.CTkLabel(dest_row, text="📁", font=("Segoe UI", 18), width=40).grid(row=0, column=0, rowspan=2, padx=(10, 0), pady=10, sticky="w")
        
        self.lbl_dest_path = ctk.CTkLabel(dest_row, text=self.caminho_base if self.caminho_base else "Clique em ⚙ para configurar", font=("Consolas", 11), text_color=COR_TEXTO if self.caminho_base else COR_MUTED, anchor="w", justify="left", wraplength=310)
        self.lbl_dest_path.grid(row=0, column=1, sticky="w", padx=(8, 4), pady=(10, 0))
        self.lbl_dest_hint = ctk.CTkLabel(dest_row, text="Caminho raiz configurado" if self.caminho_base else "Nenhum caminho definido", font=("Segoe UI", 10), text_color=COR_MUTED, anchor="w")
        self.lbl_dest_hint.grid(row=1, column=1, sticky="w", padx=(8, 4), pady=(0, 10))
        self.lbl_dest_badge = ctk.CTkLabel(dest_row, text=" OK " if self.caminho_base else "  —  ", font=("Segoe UI", 11, "bold"), text_color=COR_SUCCESS if self.caminho_base else COR_MUTED, fg_color="#E6F4EC" if self.caminho_base else COR_FUNDO, corner_radius=6, width=40, height=24)
        self.lbl_dest_badge.grid(row=0, column=2, rowspan=2, padx=10, sticky="e")
        dest_row.columnconfigure(1, weight=1)

        # ── CARD: CONFIGURAÇÃO DE ROTA ───────────
        card_rota = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_rota.pack(fill="x", padx=PAD, pady=6)
        
        topo_rota = ctk.CTkFrame(card_rota, fg_color="transparent")
        topo_rota.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkLabel(topo_rota, text="UNIDADES DE RECEPÇÃO", font=("Segoe UI", 10, "bold"), text_color=COR_MUTED).pack(side="left")
        
        self.btn_toggle_all = ctk.CTkButton(topo_rota, text="Desmarcar Todos", width=100, height=22, fg_color=COR_FUNDO, text_color=COR_TEXTO, hover_color=COR_BORDA, command=self.toggle_all)
        self.btn_toggle_all.pack(side="right")

        self.frame_checks = ctk.CTkScrollableFrame(card_rota, height=120, fg_color="transparent")
        self.frame_checks.pack(fill="x", padx=12, pady=(0, 5))

        self.checkboxes = {}
        for centro in CENTROS_IMAGENS.keys():
            chk = ctk.CTkCheckBox(
                self.frame_checks, text=centro, 
                fg_color=COR_LARANJA, hover_color=COR_LARANJA_H, 
                font=("Segoe UI", 12), text_color=COR_TEXTO
            )
            chk.pack(anchor="w", pady=4, padx=5)
            chk.select()
            self.checkboxes[centro] = chk

        self.lbl_unidade_status = ctk.CTkLabel(card_rota, text="Selecione as unidades acima.", font=("Segoe UI", 12), text_color=COR_MUTED, anchor="w")
        self.lbl_unidade_status.pack(fill="x", padx=16, pady=(0, 10))
        
        self.btn_iniciar = ctk.CTkButton(card_rota, text="▶   Iniciar Automação", height=46, corner_radius=10, fg_color=COR_LARANJA, hover_color=COR_LARANJA_H, text_color="white", font=("Segoe UI Semibold", 14, "bold"), command=self.start_thread)
        self.btn_iniciar.pack(fill="x", padx=12, pady=(0, 14))

        # ── CARD: PROGRESSO ──────────────────────
        card_prog = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_prog.pack(fill="x", padx=PAD, pady=6)
        prog_header = ctk.CTkFrame(card_prog, fg_color="transparent")
        prog_header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(prog_header, text="PROGRESSO", font=("Segoe UI", 10, "bold"), text_color=COR_MUTED).pack(side="left")
        self.lbl_status_pill = ctk.CTkLabel(prog_header, text=" Aguardando ", font=("Segoe UI", 10), text_color=COR_MUTED, fg_color=COR_FUNDO, corner_radius=8, height=22)
        self.lbl_status_pill.pack(side="right")
        self.progressbar = ctk.CTkProgressBar(card_prog, height=5, progress_color=COR_LARANJA, fg_color=COR_FUNDO, corner_radius=3)
        self.progressbar.pack(fill="x", padx=16, pady=(0, 10))
        self.progressbar.set(0)
        self.step_bar = StepBar(card_prog, STEPS)
        self.step_bar.pack(fill="x", padx=16, pady=(0, 14))

        # ── CARD: TERMINAL ───────────────────────
        card_log = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_log.pack(fill="both", expand=True, padx=PAD, pady=(6, 20))
        
        log_header = ctk.CTkFrame(card_log, fg_color="transparent")
        log_header.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkLabel(log_header, text="TERMINAL DE LOG", font=("Segoe UI", 10, "bold"), text_color=COR_MUTED).pack(side="left")
        ctk.CTkButton(log_header, text="Limpar", width=54, height=22, corner_radius=6, fg_color="transparent", hover_color=COR_FUNDO, border_width=0, text_color=COR_MUTED, font=("Segoe UI", 10), command=self.limpar_log).pack(side="right")
        
        self.log_text = ctk.CTkTextbox(card_log, fg_color=COR_TERMINAL_BG, text_color=COR_TERMINAL_FG, font=("Consolas", 11), border_width=0, corner_radius=8, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 14))
        self.log_text.tag_config("ok",  foreground=COR_LARANJA)
        self.log_text.tag_config("err", foreground=COR_ERROR)
        self.log_text.tag_config("suc", foreground=COR_SUCCESS)
        self.adicionar_log("Sistema pronto para seleção de unidades.")

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

    def _set_step(self, idx, state): self.after(0, lambda: self.step_bar.set_step(idx, state))
    def _set_progress(self, val): self.after(0, lambda: self.progressbar.set(val))
    def _set_pill(self, text, color=COR_MUTED, bg=COR_FUNDO): self.after(0, lambda: self.lbl_status_pill.configure(text=f" {text} ", text_color=color, fg_color=bg))
    def _set_unidade_status(self, text): self.after(0, lambda: self.lbl_unidade_status.configure(text=text))

    def clicar_img(self, img, desc, timeout=15, max_tentativas=4, confidence=0.7, double=False, click_type="standard"):
        for tentativa in range(1, max_tentativas + 1):
            self.adicionar_log(f"Buscando: {desc} (Tentativa {tentativa}/{max_tentativas})")
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
            
            self.adicionar_log(f"Falha na tentativa {tentativa} de achar '{desc}'.", "err")
            
            if tentativa < max_tentativas:
                self.adicionar_log("Tentando fechar possível alerta com [ESC] e repetindo...", "ok")
                pyautogui.press('esc') 
                time.sleep(2)
        
        self.adicionar_log(f"ERRO CRÍTICO: '{desc}' não encontrado após {max_tentativas} tentativas. Pulando unidade.", "err")
        return False

    def fechar_atlas(self):
        self.adicionar_log("Fechando Atlas Browser...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "AtlasBrowser.exe"], capture_output=True, text=True, check=False)
            time.sleep(2)
        except: pass

    def start_thread(self):
        if not self.caminho_base or not os.path.exists(self.caminho_base):
            messagebox.showwarning("Atenção", "Configure a pasta de destino na engrenagem ⚙ primeiro.")
            return
        
        self.executando = True
        self.btn_iniciar.configure(state="disabled", text="⏹   Executando...")
        self.step_bar.reset()
        self._set_progress(0)
        self._set_pill("Executando", COR_LARANJA, COR_LARANJA_BG)
        threading.Thread(target=self.executar_sequencial, daemon=True).start()

    def executar_sequencial(self):
        centros_selecionados = [centro for centro, chk in self.checkboxes.items() if chk.get() == 1]

        if not centros_selecionados:
            self.adicionar_log("Nenhuma unidade selecionada para execução.", "err")
            self.executando = False
            self.after(0, lambda: self.btn_iniciar.configure(state="normal", text="▶   Iniciar Automação"))
            self._set_pill("Parado", COR_MUTED, COR_FUNDO)
            return

        total_centros = len(centros_selecionados)
        sucessos = 0
        falhas = 0
        lista_falhas = []

        for i, centro in enumerate(centros_selecionados):
            if not self.executando: break
            self._set_unidade_status(f"[{i+1}/{total_centros}] {centro}: Processando...")
            self.step_bar.reset()
            self._set_progress(0)
            
            if self.executar_robo(centro):
                self.adicionar_log(f"Sucesso: {centro}", "suc")
                sucessos += 1
            else:
                self.adicionar_log(f"Falha ao processar {centro}. O processo seguirá para a próxima unidade.", "err")
                falhas += 1
                lista_falhas.append(centro)
            
            self.fechar_atlas()
            time.sleep(1)
            
        self.executando = False
        self._set_unidade_status("Processo Finalizado.")
        self._set_pill("Concluído", COR_SUCCESS, "#E6F4EC")
        
        self.after(0, lambda: self.mostrar_resumo(total_centros, sucessos, falhas, lista_falhas))
        self.after(0, lambda: self.btn_iniciar.configure(state="normal", text="▶   Iniciar Automação", fg_color=COR_LARANJA, hover_color=COR_LARANJA_H))

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
            cor_destaque = COR_SUCCESS
            icone = "✅"
            titulo_texto = "100% CONCLUÍDO!"
            msg_texto = "Todos os centros foram processados com perfeição."
        elif taxa_sucesso > 0:
            cor_destaque = COR_LARANJA
            icone = "⚠️"
            titulo_texto = "CONCLUÍDO COM PENDÊNCIAS"
            msg_texto = "A maior parte foi feita, mas alguns centros falharam."
        else:
            cor_destaque = COR_ERROR
            icone = "❌"
            titulo_texto = "FALHA CRÍTICA"
            msg_texto = "Nenhum centro foi processado com sucesso."

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
            ctk.CTkLabel(aviso_frame, text="Ficaram para trás:", font=("Segoe UI", 10, "bold"), text_color=COR_ERROR).pack(anchor="w", padx=10, pady=(8,0))
            ctk.CTkLabel(aviso_frame, text=falhas_txt, font=("Segoe UI", 11), text_color=COR_ERROR, wraplength=370, justify="left").pack(anchor="w", padx=10, pady=(0,8))

        dest_frame = ctk.CTkFrame(corpo, fg_color=COR_CARD, corner_radius=10, border_width=1, border_color=COR_BORDA)
        dest_frame.pack(fill="x")
        ctk.CTkLabel(dest_frame, text="Arquivos e pastas salvos em:", font=("Segoe UI", 10, "bold"), text_color=COR_MUTED).pack(anchor="w", padx=10, pady=(8,0))
        
        path_lbl = ctk.CTkTextbox(dest_frame, fg_color="transparent", text_color=COR_TEXTO, font=("Consolas", 10), height=45, wrap="word")
        path_lbl.pack(fill="x", padx=5, pady=5)
        path_lbl.insert("1.0", self.caminho_base)
        path_lbl.configure(state="disabled")

        btn_fechar = ctk.CTkButton(modal, text="Entendido 👍", height=40, fg_color=COR_TEXTO, hover_color="#333", command=modal.destroy)
        btn_fechar.pack(pady=(0, 20), padx=20, fill="x")

    def executar_robo(self, unidade):
        try:
            self.after(0, self.iconify)
            
            if unidade in ["PGUA 1", "PGUA 2"]:
                self._set_step(0, "active")
                os.startfile(CAMINHO_ATLAS_EXE)
                
                if not self.clicar_img("assets/selectcenter.png", "Seletor de centro", timeout=40): return False
                if not self.clicar_img(CENTROS_IMAGENS["PGUA 1"], "PGUA 1 (Login)"): return False
                if not self.clicar_img("assets/atlas_cargo.png", "Botão Iniciar", timeout=15, click_type="force"): return False
                
                self._set_step(0, "done")
                self._set_progress(0.17)

                self._set_step(1, "active")
                if self.clicar_img("assets/user.png", "Campo usuário", timeout=15):
                    pyautogui.write('ESANTAN3')
                    if not self.clicar_img("assets/senha.png", "Campo senha"): return False
                    pyautogui.write('Mosaic@2027')
                    pyautogui.press('enter')
                else:
                    return False
                
                self.adicionar_log(f"Selecionando {unidade} internamente via teclado...", "ok")
                time.sleep(2)
                
                if self.clicar_img("assets/abrir_botaopg2.png", "Botão Seletor Interno", timeout=15):
                    time.sleep(1) 
                    
                    if unidade == "PGUA 1":
                        pyautogui.press('up')
                        pyautogui.press('up')
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
                
                self._set_step(1, "done")
                self._set_progress(0.34)
            
            else:
                self._set_step(0, "active")
                os.startfile(CAMINHO_ATLAS_EXE)
                
                if not self.clicar_img("assets/selectcenter.png", "Seletor de centro", timeout=40): return False
                if not self.clicar_img(CENTROS_IMAGENS[unidade], unidade): return False
                if not self.clicar_img("assets/atlas_cargo.png", "Botão Iniciar", timeout=15, click_type="force"): return False
                
                self._set_step(0, "done")
                self._set_progress(0.17)

                self._set_step(1, "active")
                if self.clicar_img("assets/user.png", "Campo usuário", timeout=15):
                    pyautogui.write('ESANTAN3')
                    if not self.clicar_img("assets/senha.png", "Campo senha"): return False
                    pyautogui.write('Mosaic@2026')
                    pyautogui.press('enter')
                else:
                    return False

                self._set_step(1, "done")
                self._set_progress(0.34)

            self._set_step(2, "active")
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
            
            self._set_step(2, "done")
            self._set_progress(0.50)

            self._set_step(3, "active")
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
                    pyautogui.write("DESCARGA")
                    pyautogui.press('down')
                    pyautogui.press('enter')
                else:
                    return False
            else:
                if self.clicar_img("assets/selectrota.png", "Rota"):
                    achou_rota = False
                    for img, nome in [
                        ("assets/rota_descarga.png", "Recepção"),
                        ("assets/rota_descarga2.png", "RECEPÇÃO")
                    ]:
                        if self.clicar_img(img, nome, timeout=2, max_tentativas=1):
                            achou_rota = True
                            break
                    if not achou_rota: return False
                else:
                    return False

            self._set_step(3, "done")
            self._set_progress(0.67)

            # --- ETAPA 4: EXPORTAR (COM PAUSAS PARA EVITAR ANSIEDADE DO ROBÔ) ---
            self._set_step(4, "active")
            
            if not self.clicar_img("assets/selecttype.png", "Tipo de saída"): return False
            time.sleep(1) # PAUSA: Espera o menu suspenso abrir completamente
            
            if not self.clicar_img("assets/tipo_excel.png", "Excel"): return False
            time.sleep(1.5) # PAUSA VITAL: Deixa o Atlas registrar que mudou de PDF para Excel
            
            if not self.clicar_img("assets/gerar_relatorio.png", "Gerar relatório"): return False
            
            self._set_step(4, "done")
            self._set_progress(0.83)

            self._set_step(5, "active")
            if not self.mover_arquivo(unidade, hoje.strftime("%m.%Y")): return False
            
            self._set_step(5, "done")
            self._set_progress(1.0)
            return True
            
        except Exception as e:
            self.adicionar_log(f"Erro inesperado em {unidade}: {str(e)}", "err")
            return False

    def mover_arquivo(self, unidade, mes_ano):
        numeros_centro = {
            "PGUA 1": "4020",
            "CANDEIAS": "4040",
            "SORRISO": "4060",
            "RIO VERDE": "4070",
            "CATALÃO": "4100",
            "RONDONÓPOLIS": "4110",
            "UBERABA": "4120",
            "PGUA 2": "4130",
            "RIO GRANDE": "4140",
            "PALMEIRANTE": "4170"
        }
        
        num_centro = numeros_centro.get(unidade, "0000")
        tempo_inicio = time.time()
        
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
                        novo_nome = f"{mes_ano} - {num_centro} RelPesagensDiarioBalancaRoo{extensao}"
                        
                        pasta_centro = os.path.join(self.caminho_base, num_centro)
                        os.makedirs(pasta_centro, exist_ok=True) 
                        
                        destino_final = os.path.join(pasta_centro, novo_nome)
                        
                        if os.path.exists(destino_final):
                            os.remove(destino_final)
                        shutil.move(caminho_recente, destino_final)
                        self.adicionar_log(f"Salvo na pasta [{num_centro}]: {novo_nome}", "suc")
                        return True
                    except Exception as e:
                        self.adicionar_log(f"Tentando mover... {str(e)}", "err")
            time.sleep(1)
            
        self.adicionar_log("Tempo esgotado: arquivo não encontrado no Downloads.", "err")
        return False

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    try:
        App().mainloop()
    except Exception as e:
        print(f"Erro fatal ao abrir: {e}")