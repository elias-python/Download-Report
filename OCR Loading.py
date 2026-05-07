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
from PIL import Image

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
ARQUIVO_CONFIG = "config_atlas.json"

# --- PALETA ---
COR_LARANJA     = "#FF8C00"
COR_LARANJA_H   = "#e67e00"
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
    "RONDONÓPOLIS": "assets/rondonopolis.png",
    "RIO VERDE": "assets/rioverde.png",
    "RIO GRANDE": "assets/riogrande.png"
}

STEPS = ["Abrir Atlas", "Login", "Relatório", "Configurar", "Exportar", "Mover arquivo"]

class StepBar(ctk.CTkFrame):
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
            dot = ctk.CTkLabel(self, text="●", font=("Consolas", 14), text_color=COR_BORDA, width=18)
            dot.grid(row=0, column=col, padx=(0, 0))
            self.dots.append(dot)
            lbl = ctk.CTkLabel(self, text=step, font=("Segoe UI", 10), text_color=COR_MUTED)
            lbl.grid(row=1, column=col, padx=(0, 0))
            self.labels.append(lbl)
            if i < len(self.steps) - 1:
                line = ctk.CTkLabel(self, text="──────", font=("Consolas", 10), text_color=COR_BORDA)
                line.grid(row=0, column=col + 1, padx=2)
                self.lines.append(line)
        for i in range(len(self.steps) * 2 - 1):
            self.columnconfigure(i, weight=1)

    def reset(self):
        for dot in self.dots: dot.configure(text_color=COR_BORDA)
        for lbl in self.labels: lbl.configure(text_color=COR_MUTED)
        for line in self.lines: line.configure(text_color=COR_BORDA)

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
        self.title("Mosaic Atlas Vision v1.1")
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
        caminho = filedialog.askdirectory(title="Selecione a pasta de destino final")
        if caminho:
            self.caminho_base = caminho
            self.salvar_config(caminho)
            self._atualizar_dest()
            self.adicionar_log(f"Destino salvo: {caminho}", "ok")

    def _atualizar_dest(self):
        if self.caminho_base:
            self.lbl_dest_path.configure(text=self.caminho_base, text_color=COR_TEXTO)
            self.lbl_dest_hint.configure(text="Caminho configurado")
            self.lbl_dest_badge.configure(text=" OK ", text_color=COR_SUCCESS, fg_color="#E6F4EC", corner_radius=6)
        else:
            self.lbl_dest_path.configure(text="Clique em ⚙  para configurar", text_color=COR_MUTED)
            self.lbl_dest_hint.configure(text="Nenhum caminho definido")
            self.lbl_dest_badge.configure(text="  —  ", text_color=COR_MUTED, fg_color=COR_FUNDO, corner_radius=6)

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
        ctk.CTkLabel(txt_frame, text="Mosaic Atlas OCR - Expedição", font=("Segoe UI Semibold", 16, "bold"), text_color=COR_TEXTO).pack(anchor="w")
        ctk.CTkLabel(txt_frame, text="Automação Multi-Monitor", font=("Segoe UI", 11), text_color=COR_MUTED).pack(anchor="w")
        ctk.CTkButton(header, text="⚙", width=36, height=36, corner_radius=8, fg_color=COR_CARD, hover_color=COR_FUNDO, border_width=1, border_color=COR_BORDA, text_color=COR_MUTED, font=("Segoe UI", 16), command=self.selecionar_caminho_base).pack(side="right")
        
        card_dest = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_dest.pack(fill="x", padx=PAD, pady=6)
        ctk.CTkLabel(card_dest, text="PASTA DE DESTINO", font=("Segoe UI", 10, "bold"), text_color=COR_MUTED).pack(anchor="w", padx=16, pady=(14, 6))
        dest_row = ctk.CTkFrame(card_dest, fg_color=COR_FUNDO, corner_radius=8, border_width=1, border_color=COR_BORDA)
        dest_row.pack(fill="x", padx=12, pady=(0, 14))
        ctk.CTkLabel(dest_row, text="📁", font=("Segoe UI", 18), width=40).grid(row=0, column=0, rowspan=2, padx=(10, 0), pady=10, sticky="w")
        self.lbl_dest_path = ctk.CTkLabel(dest_row, text=self.caminho_base if self.caminho_base else "Clique em ⚙ para configurar", font=("Consolas", 11), text_color=COR_TEXTO if self.caminho_base else COR_MUTED, anchor="w", justify="left", wraplength=310)
        self.lbl_dest_path.grid(row=0, column=1, sticky="w", padx=(8, 4), pady=(10, 0))
        self.lbl_dest_hint = ctk.CTkLabel(dest_row, text="Caminho configurado" if self.caminho_base else "Nenhum caminho definido", font=("Segoe UI", 10), text_color=COR_MUTED, anchor="w")
        self.lbl_dest_hint.grid(row=1, column=1, sticky="w", padx=(8, 4), pady=(0, 10))
        self.lbl_dest_badge = ctk.CTkLabel(dest_row, text=" OK " if self.caminho_base else "  —  ", font=("Segoe UI", 11, "bold"), text_color=COR_SUCCESS if self.caminho_base else COR_MUTED, fg_color="#E6F4EC" if self.caminho_base else COR_FUNDO, corner_radius=6, width=40, height=24)
        self.lbl_dest_badge.grid(row=0, column=2, rowspan=2, padx=10, sticky="e")
        dest_row.columnconfigure(1, weight=1)

        card_rota = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_rota.pack(fill="x", padx=PAD, pady=6)
        ctk.CTkLabel(card_rota, text="UNIDADE DE DISTRIBUIÇÃO", font=("Segoe UI", 10, "bold"), text_color=COR_MUTED).pack(anchor="w", padx=16, pady=(14, 6))
        self.lbl_unidade_status = ctk.CTkLabel(card_rota, text="Aguardando início...", font=("Segoe UI Semibold", 14), text_color=COR_TEXTO, anchor="w")
        self.lbl_unidade_status.pack(fill="x", padx=16, pady=(0, 10))
        self.btn_iniciar = ctk.CTkButton(card_rota, text="▶   Iniciar Automação Total", height=46, corner_radius=10, fg_color=COR_LARANJA, hover_color=COR_LARANJA_H, text_color="white", command=self.start_thread)
        self.btn_iniciar.pack(fill="x", padx=12, pady=(0, 14))

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

        card_log = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=12, border_width=1, border_color=COR_BORDA)
        card_log.pack(fill="both", expand=True, padx=PAD, pady=(6, 20))
        self.log_text = ctk.CTkTextbox(card_log, fg_color=COR_TERMINAL_BG, text_color=COR_TERMINAL_FG, font=("Consolas", 11), border_width=0, corner_radius=8, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=12, pady=12)
        self.log_text.tag_config("ok", foreground=COR_LARANJA)
        self.log_text.tag_config("err", foreground=COR_ERROR)
        self.log_text.tag_config("suc", foreground=COR_SUCCESS)
        self.adicionar_log("Sistema pronto. Resiliência multi-monitor ativada.")

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

    def _set_step(self, idx, state): self.after(0, lambda: self.step_bar.set_step(idx, state))
    def _set_progress(self, val): self.after(0, lambda: self.progressbar.set(val))
    def _set_pill(self, text, color=COR_MUTED, bg=COR_FUNDO): self.after(0, lambda: self.lbl_status_pill.configure(text=f" {text} ", text_color=color, fg_color=bg))
    def _set_unidade_status(self, text): self.after(0, lambda: self.lbl_unidade_status.configure(text=text))

    def clicar_img(self, img, desc, timeout=20, confidence=0.7, double=False, click_type="standard"):
        """Busca imagem com tolerância a escala e múltiplos monitores."""
        self.adicionar_log(f"Buscando: {desc}")
        inicio = time.time()
        
        # Se a imagem não existir, pula para evitar erro fatal
        if not os.path.exists(img):
            self.adicionar_log(f"Aviso: Arquivo {img} não encontrado.", "err")
            return False

        while time.time() - inicio < timeout:
            if not self.executando: return False
            try:
                # Tenta localizar em todos os monitores (comportamento padrão do pyautogui)
                pos = pyautogui.locateCenterOnScreen(img, confidence=confidence)
                
                if pos:
                    if click_type == "force":
                        pyautogui.moveTo(pos.x, pos.y, duration=0.2)
                        pyautogui.click()
                    elif double:
                        pyautogui.doubleClick(pos)
                    else:
                        pyautogui.click(pos)
                    self.adicionar_log(f"{desc} encontrado!", "ok")
                    return True
            except Exception: pass
            time.sleep(0.5)
        
        self.adicionar_log(f"Timeout: {desc} não encontrado.", "err")
        return False

    def fechar_atlas(self):
        self.adicionar_log("Fechando Atlas Browser...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "AtlasBrowser.exe"], capture_output=True, text=True, check=False)
            time.sleep(2)
        except: pass

    def start_thread(self):
        if not self.caminho_base or not os.path.exists(self.caminho_base):
            messagebox.showwarning("Atenção", "Configure a pasta de destino primeiro.")
            return
        self.executando = True
        self.btn_iniciar.configure(state="disabled", text="⏹ Executando...")
        self.step_bar.reset()
        self._set_progress(0)
        threading.Thread(target=self.executar_sequencial, daemon=True).start()

    def executar_sequencial(self):
        centros = list(CENTROS_IMAGENS.keys())
        for i, centro in enumerate(centros):
            if not self.executando: break
            self._set_unidade_status(f"[{i+1}/{len(centros)}] {centro}: Processando...")
            self.step_bar.reset()
            self._set_progress(0)
            if self.executar_robo(centro):
                self.adicionar_log(f"Sucesso: {centro}", "suc")
            else:
                self.adicionar_log(f"Falha: {centro}", "err")
            self.fechar_atlas()
            time.sleep(1)
        self.executando = False
        self._set_unidade_status("Concluído.")
        self.after(0, lambda: self.btn_iniciar.configure(state="normal", text="▶ Iniciar Automação Total"))

    def executar_robo(self, unidade):
        try:
            self.after(0, self.iconify)
            self._set_step(0, "active")
            os.startfile(CAMINHO_ATLAS_EXE)
            if not self.clicar_img("assets/selectcenter.png", "Seletor de centro", timeout=40):
                return False
            
            self.clicar_img(CENTROS_IMAGENS[unidade], unidade)
            self.clicar_img("assets/atlas_cargo.png", "Botão Iniciar", timeout=15, click_type="force")
            self._set_step(0, "done")
            self._set_progress(0.17)

            self._set_step(1, "active")
            if self.clicar_img("assets/user.png", "Campo usuário", timeout=15):
                pyautogui.write('ESANTAN3')
                self.clicar_img("assets/senha.png", "Campo senha")
            if unidade == "PGUA 1":
                pyautogui.write('Mosaic@2027')
            else:
                pyautogui.write('Mosaic@2026')

            pyautogui.press('enter')
            self._set_step(1, "done")
            self._set_progress(0.34)

            self._set_step(2, "active")
            if unidade == "CATALÃO":
                self.clicar_img("assets/impressao_catalao.png", "Menu Impressão", timeout=25)
                self.clicar_img("assets/relatorio_catalao.png", "Menu Relatórios")
            else:
                self.clicar_img("assets/impressao.png", "Menu Impressão", timeout=25)
                self.clicar_img("assets/relatorios.png", "Menu Relatórios")
            
            if unidade == "UBERABA":
                self.clicar_img("assets/relatorios_ubr.png", "Relatórios UBR")
            else:
                self.clicar_img("assets/relatordiariobal.png", "Relatório Balança")
            self._set_step(2, "done")
            self._set_progress(0.50)

            self._set_step(3, "active")
            hoje = datetime.now()
            if self.clicar_img("assets/secao_data_inicial.png", "Data inicial", double=True):
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')
                pyautogui.write(hoje.strftime("01/%m/%Y"))
                pyautogui.press('tab')
                for _ in range(3):
                    pyautogui.hotkey('ctrl', 'a')
                    pyautogui.write('0')
                    pyautogui.press('tab')
            if unidade in ["UBERABA", "RONDONÓPOLIS"]:
                if self.clicar_img("assets/selectfluxo.png", "Fluxo"):
                    pyautogui.write("CARREGAMENTO")
                    pyautogui.press('down')
                    pyautogui.press('enter')
            else:
                if self.clicar_img("assets/selectrota.png", "Rota"):
                    self.clicar_img("assets/rota_exped.png", "Expedição")
            self._set_step(3, "done")
            self._set_progress(0.67)

            self._set_step(4, "active")
            self.clicar_img("assets/selecttype.png", "Tipo de saída")
            self.clicar_img("assets/tipo_excel.png", "Excel")
            self.clicar_img("assets/gerar_relatorio.png", "Gerar relatório")
            self._set_step(4, "done")
            self._set_progress(0.83)

            self._set_step(5, "active")
            self.mover_arquivo(unidade, hoje.strftime("%m.%Y"))
            self._set_step(5, "done")
            self._set_progress(1.0)
            return True
        except Exception as e:
            self.adicionar_log(f"Erro: {str(e)}", "err")
            return False

    def mover_arquivo(self, unidade, mes_ano):
        nomes = {"PGUA 1": "Paranagua 1", "UBERABA": "Uberaba", "SORRISO": "Sorriso", "RONDONÓPOLIS": "Rondonópolis", "RIO VERDE": "Rio Verde", "RIO GRANDE": "Rio Grande", "CATALÃO": "Catalão", "CANDEIAS": "Candeias"}
        nome_exibicao = nomes.get(unidade, unidade)
        tempo_inicio = time.time()
        for _ in range(60):
            if not self.executando: return
            arquivos = [f for f in os.listdir(CAMINHO_DOWNLOADS) if f.lower().endswith(('.xls', '.xlsx'))]
            if arquivos:
                caminho_recente = max([os.path.join(CAMINHO_DOWNLOADS, f) for f in arquivos], key=os.path.getmtime)
                if os.path.getmtime(caminho_recente) < tempo_inicio:
                    time.sleep(1); continue
                if not os.path.basename(caminho_recente).endswith(('.tmp', '.crdownload')):
                    time.sleep(2)
                    try:
                        ext = os.path.splitext(caminho_recente)[1]
                        destino = os.path.join(self.caminho_base, f"{nome_exibicao} {mes_ano}{ext}")
                        if os.path.exists(destino): os.remove(destino)
                        shutil.move(caminho_recente, destino)
                        self.adicionar_log(f"Salvo: {nome_exibicao}", "suc")
                        return
                    except: pass
            time.sleep(1)

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    try:
        App().mainloop()
    except Exception as e:
        print(f"Erro fatal ao abrir: {e}")
