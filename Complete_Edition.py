import customtkinter as ctk
import pyautogui
import time
import os
import shutil
import json
import subprocess
from datetime import datetime, timedelta
import threading
from tkinter import messagebox, filedialog
import sys
import pystray
from PIL import Image, ImageDraw
import win32com.client
import pythoncom

# --- CONFIGURAÇÕES DE PERFORMANCE ---
pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = True

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# --- CAMINHOS DINÂMICOS ---
pasta_usuario = os.environ.get("USERPROFILE")
CAMINHO_ATLAS_EXE = os.path.join(
    pasta_usuario,
    "OneDrive - The Mosaic Company",
    "Atlas",
    "Atlas_Browser_1.3.3",
    "AtlasBrowser.exe",
)
CAMINHO_DOWNLOADS = os.path.join(pasta_usuario, "Downloads")
ARQUIVO_CONFIG = "config_atlas_unified.json"

# --- PALETA DE CORES ---
TEMA_DESCARGA = {"base": "#3B82F6", "hover": "#2563EB"}
TEMA_CARREGAMENTO = {"base": "#10B981", "hover": "#059669"}
TEMA_RECEPCAO = {"base": "#F97316", "hover": "#EA580C"}
TEMA_AMBOS = {"base": "#8B5CF6", "hover": "#7C3AED"}
COR_SAP = "#0EA5E9"

COR_FUNDO = "#0F0F17"
COR_CARD = "#1A1A26"
COR_BORDA = "#2E2E42"
COR_TEXTO = "#EEEEF8"
COR_MUTED = "#6B6B85"
COR_TERMINAL_BG = "#090910"
COR_TERMINAL_FG = "#7070A0"
COR_SUCCESS = "#34D399"
COR_ERROR = "#F87171"

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
    "PALMEIRANTE": "assets/palmeirante.png",
}

RECEPCAO_ASSETS = {
    "PGUA 1": "relatorio_recepcao_1.png",
    "PGUA 2": "relatorio_recepcao.png",
    "UBERABA": "relatorio_recepcao.png",
    "CANDEIAS": "relatorio_recepcao_1.png",
    "CATALÃO": "relatorio_recepcao.png",
    "SORRISO": "relatorio_recepcao_1.png",
    "PALMEIRANTE": "relatorio_recepcao.png",
    "RONDONÓPOLIS": "relatorio_recepcao_1.png",
    "RIO VERDE": "recep_rioverde.png",
    "RIO GRANDE": "relatorio_recepcao.png",
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mosaic RDE RPA v2.1")
        self.geometry("680x880")
        self.resizable(False, False)
        self.configure(fg_color=COR_FUNDO)

        self.executando = False
        self.senha_incorreta = False
        self.auto_mode = (
            "atlas"
            if "--auto-atlas" in sys.argv
            else "sap" if "--auto-sap" in sys.argv else None
        )

        config_data = self.carregar_config()
        self.caminho_descarga = config_data.get("caminho_descarga", "")
        self.caminho_carregamento = config_data.get("caminho_carregamento", "")
        self.caminho_recepcao = config_data.get("caminho_recepcao", "")
        self.caminho_sap1 = config_data.get("caminho_sap1", "")
        self.caminho_sap2 = config_data.get("caminho_sap2", "")
        self.caminho_sap3 = config_data.get("caminho_sap3", "")
        self.user_atlas = config_data.get("user_atlas", "")
        self.pass_atlas = config_data.get("pass_atlas", "")
        self.ultima_att = config_data.get("ultima_att", "Nunca")
        self.horario_atlas = config_data.get("horario_atlas", "07:30")
        self.horario_sap_inicio = config_data.get("horario_sap_inicio", "07:00")
        self.intervalo_sap_h = config_data.get("intervalo_sap_h", "2")

        self.auto_close = self.auto_mode is not None

        self.modo_var = ctk.StringVar(value="📥 Descarga")
        self.tema_atual = TEMA_DESCARGA

        self._build_ui()
        self.atualizar_relogio()
        self.ao_mudar_modo(self.modo_var.get())
        self._setup_tray()
        self._keepalive_stop = threading.Event()
        threading.Thread(target=self._keepalive_sap, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self._minimizar_para_tray)
        self.after(2000, self._verificar_agendamento)
        if self.auto_mode:
            self.withdraw()
            self.after(1500, self._auto_iniciar)
        else:
            self.after(350, self.mostrar_aviso_resolucao)

    def abrir_configuracoes_tela(self):
        try:
            subprocess.run("start ms-settings:display", shell=True, check=False)
        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Não foi possível abrir as configurações de tela automaticamente.\n\nDetalhe: {str(e)}",
            )

    def mostrar_aviso_resolucao(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Ajuste de Tela Recomendado")
        modal.geometry("520x280")
        modal.resizable(False, False)
        modal.configure(fg_color=COR_FUNDO)
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(
            modal,
            text="Antes de iniciar, confira a tela em 100%",
            font=("Segoe UI", 18, "bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            modal,
            text=(
                "Para evitar erros de clique no OCR, ajuste a Escala do Windows para 100% "
                "(e, se necessário, revise também a resolução)."
            ),
            font=("Segoe UI", 12),
            text_color=COR_MUTED,
            justify="left",
            wraplength=475,
        ).pack(anchor="w", padx=20, pady=(0, 14))

        dica = ctk.CTkFrame(
            modal,
            fg_color=COR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=COR_BORDA,
        )
        dica.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            dica,
            text="Caminho rápido: Configurações > Sistema > Tela > Escala = 100%",
            font=("Consolas", 11),
            text_color=COR_TEXTO,
            justify="left",
            wraplength=455,
        ).pack(anchor="w", padx=12, pady=12)

        botoes = ctk.CTkFrame(modal, fg_color="transparent")
        botoes.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(
            botoes,
            text="Abrir Configurações de Tela",
            height=38,
            fg_color=COR_SAP,
            hover_color="#0284C7",
            command=self.abrir_configuracoes_tela,
        ).pack(side="left")

        ctk.CTkButton(
            botoes,
            text="Continuar",
            height=38,
            fg_color=COR_TEXTO,
            hover_color="#000000",
            command=modal.destroy,
        ).pack(side="right")

        modal.protocol("WM_DELETE_WINDOW", modal.destroy)

    def carregar_config(self):
        if os.path.exists(ARQUIVO_CONFIG):
            try:
                with open(ARQUIVO_CONFIG, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def salvar_config(
        self,
        caminho_desc=None,
        caminho_carr=None,
        caminho_rec=None,
        ultima_att=None,
        user=None,
        senha=None,
        csap1=None,
        csap2=None,
        csap3=None,
        horario_atlas=None,
        horario_sap_inicio=None,
        intervalo_sap_h=None,
    ):
        dados = self.carregar_config()
        if caminho_desc is not None:
            dados["caminho_descarga"] = caminho_desc
        if caminho_carr is not None:
            dados["caminho_carregamento"] = caminho_carr
        if caminho_rec is not None:
            dados["caminho_recepcao"] = caminho_rec
        if ultima_att is not None:
            dados["ultima_att"] = ultima_att
        if user is not None:
            dados["user_atlas"] = user
        if senha is not None:
            dados["pass_atlas"] = senha
        if csap1 is not None:
            dados["caminho_sap1"] = csap1
        if csap2 is not None:
            dados["caminho_sap2"] = csap2
        if csap3 is not None:
            dados["caminho_sap3"] = csap3
        if horario_atlas is not None:
            dados["horario_atlas"] = horario_atlas
        if horario_sap_inicio is not None:
            dados["horario_sap_inicio"] = horario_sap_inicio
        if intervalo_sap_h is not None:
            dados["intervalo_sap_h"] = intervalo_sap_h
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump(dados, f)

    def salvar_credenciais(self):
        self.salvar_config(user=self.ent_user.get(), senha=self.ent_pass.get())
        self.adicionar_log("Credenciais do Atlas salvas com sucesso!", "suc")

    def selecionar_caminho_base(self):
        modo_atual = self.modo_var.get()
        if "Ambos" in modo_atual:
            messagebox.showinfo(
                "Atenção",
                "Selecione a aba 'Descarga', 'Carregamento' ou 'Recepção' individualmente para configurar.",
            )
            return

        is_descarga = "Descarga" in modo_atual
        is_recepcao = "Recepção" in modo_atual

        caminho = filedialog.askdirectory(title=f"Selecione a pasta para {modo_atual}")
        if caminho:
            if is_descarga:
                self.caminho_descarga = caminho
                self.salvar_config(caminho_desc=caminho)
            elif is_recepcao:
                self.caminho_recepcao = caminho
                self.salvar_config(caminho_rec=caminho)
            else:
                self.caminho_carregamento = caminho
                self.salvar_config(caminho_carr=caminho)
            self._atualizar_dest()
            self.adicionar_log(f"Destino para {modo_atual} salvo: {caminho}", "ok")

    def selecionar_caminho_sap(self, passo):
        caminho = filedialog.askdirectory(
            title=f"Selecione a pasta destino para o Passo {passo} do SAP"
        )
        if caminho:
            if passo == 1:
                self.caminho_sap1 = caminho
                self.salvar_config(csap1=caminho)
                self.lbl_sap1_path.configure(text=caminho, text_color=COR_TEXTO)
            elif passo == 2:
                self.caminho_sap2 = caminho
                self.salvar_config(csap2=caminho)
                self.lbl_sap2_path.configure(text=caminho, text_color=COR_TEXTO)
            elif passo == 3:
                self.caminho_sap3 = caminho
                self.salvar_config(csap3=caminho)
                self.lbl_sap3_path.configure(text=caminho, text_color=COR_TEXTO)
            self.adicionar_log(f"Destino para SAP Passo {passo} salvo.", "ok")

    def _atualizar_dest(self):
        modo_atual = self.modo_var.get()
        if "Ambos" in modo_atual:
            if (
                self.caminho_descarga
                and self.caminho_carregamento
                and self.caminho_recepcao
            ):
                self.lbl_dest_path.configure(
                    text="✔️ Todas as pastas configuradas.", text_color=COR_SUCCESS
                )
                self.lbl_dest_badge.configure(
                    text=" OK ", text_color=COR_SUCCESS, fg_color="#0D2B1A"
                )
            else:
                self.lbl_dest_path.configure(
                    text="⚠️ Falta configurar caminhos.", text_color=COR_ERROR
                )
                self.lbl_dest_badge.configure(
                    text=" ERRO ", text_color=COR_ERROR, fg_color="#2D0D0D"
                )
            return

        if "Descarga" in modo_atual:
            caminho_exibido = self.caminho_descarga
        elif "Recepção" in modo_atual:
            caminho_exibido = self.caminho_recepcao
        else:
            caminho_exibido = self.caminho_carregamento

        if caminho_exibido:
            self.lbl_dest_path.configure(text=caminho_exibido, text_color=COR_TEXTO)
            self.lbl_dest_badge.configure(
                text=" OK ", text_color=COR_SUCCESS, fg_color="#E6F4EC"
            )
        else:
            self.lbl_dest_path.configure(
                text=f"Clique em ⚙ para configurar a pasta", text_color=COR_MUTED
            )
            self.lbl_dest_badge.configure(
                text="  —  ", text_color=COR_MUTED, fg_color=COR_FUNDO
            )

    def ao_mudar_modo(self, valor_selecionado):
        if "Descarga" in valor_selecionado:
            self.tema_atual = TEMA_DESCARGA
        elif "Recepção" in valor_selecionado:
            self.tema_atual = TEMA_RECEPCAO
        elif "Carregamento" in valor_selecionado:
            self.tema_atual = TEMA_CARREGAMENTO
        else:
            self.tema_atual = TEMA_AMBOS

        cor_base = self.tema_atual["base"]
        self.logo_box.configure(fg_color=cor_base)
        self.seg_button.configure(
            selected_color=cor_base, selected_hover_color=self.tema_atual["hover"]
        )
        self.btn_iniciar.configure(
            fg_color=cor_base, hover_color=self.tema_atual["hover"]
        )
        self.log_text.tag_config("ok", foreground=cor_base)

        for chk in self.checkboxes.values():
            chk.configure(fg_color=cor_base, hover_color=self.tema_atual["hover"])
        self._atualizar_dest()

    def toggle_all_atlas(self):
        algum_desmarcado = any(chk.get() == 0 for chk in self.checkboxes.values())
        if algum_desmarcado:
            for chk in self.checkboxes.values():
                chk.select()
        else:
            for chk in self.checkboxes.values():
                chk.deselect()

    def atualizar_relogio(self):
        agora = datetime.now()
        self.lbl_data.configure(text=agora.strftime("%d/%m/%Y"))
        self.lbl_hora.configure(text=agora.strftime("%H:%M:%S"))
        self.after(1000, self.atualizar_relogio)

    def _build_ui(self):
        PAD = 20

        # --- HEADER ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD, pady=(15, 5))

        self.logo_box = ctk.CTkFrame(header, width=42, height=42, corner_radius=10)
        self.logo_box.pack(side="left")
        self.logo_box.pack_propagate(False)
        ctk.CTkLabel(
            self.logo_box, text="⊞", font=("Segoe UI", 20, "bold"), text_color="white"
        ).place(relx=0.5, rely=0.5, anchor="center")

        txt_frame = ctk.CTkFrame(header, fg_color="transparent")
        txt_frame.pack(side="left", padx=10)
        ctk.CTkLabel(
            txt_frame,
            text="Mosaic RDE - RPA Central",
            font=("Segoe UI Semibold", 18, "bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w")
        self.lbl_last_run = ctk.CTkLabel(
            txt_frame,
            text=f"Última atualização: {self.ultima_att}",
            font=("Segoe UI", 12),
            text_color=COR_MUTED,
        )
        self.lbl_last_run.pack(anchor="w")

        relogio_frame = ctk.CTkFrame(header, fg_color="transparent")
        relogio_frame.pack(side="right", anchor="e")
        self.lbl_hora = ctk.CTkLabel(
            relogio_frame,
            text="00:00:00",
            font=("Consolas", 18, "bold"),
            text_color=COR_TEXTO,
        )
        self.lbl_hora.pack(anchor="e")
        self.lbl_data = ctk.CTkLabel(
            relogio_frame,
            text="00/00/0000",
            font=("Segoe UI", 11),
            text_color=COR_MUTED,
        )
        self.lbl_data.pack(anchor="e", pady=(0, 0))

        # --- ABAS (TABS) ---
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COR_CARD,
            segmented_button_selected_color=COR_SAP,
            segmented_button_selected_hover_color="#007BB5",
        )
        self.tabview.pack(fill="x", padx=PAD, pady=5)
        self.tabview.add("🌐 Módulo ATLAS")
        self.tabview.add("⚙️ Módulo SAP")

        # ==========================================
        # CONSTRUÇÃO DA ABA ATLAS
        # ==========================================
        tab_atlas = self.tabview.tab("🌐 Módulo ATLAS")

        inputs_frame = ctk.CTkFrame(tab_atlas, fg_color="transparent")
        inputs_frame.pack(fill="x", padx=5, pady=(10, 5))
        self.ent_user = ctk.CTkEntry(
            inputs_frame, placeholder_text="Usuário Atlas", width=180, height=32
        )
        self.ent_user.pack(side="left", padx=(0, 5))
        self.ent_user.insert(0, self.user_atlas)
        self.ent_pass = ctk.CTkEntry(
            inputs_frame, placeholder_text="Senha", width=180, height=32, show="*"
        )
        self.ent_pass.pack(side="left", padx=5)
        self.ent_pass.insert(0, self.pass_atlas)
        self.btn_save_creds = ctk.CTkButton(
            inputs_frame,
            text="Salvar",
            width=70,
            height=32,
            fg_color=COR_FUNDO,
            text_color=COR_TEXTO,
            hover_color=COR_BORDA,
            command=self.salvar_credenciais,
        )
        self.btn_save_creds.pack(side="left", padx=5)

        self.seg_button = ctk.CTkSegmentedButton(
            tab_atlas,
            values=["📥 Descarga", "📤 Carregamento", "📬 Recepção", "🔄 Ambos"],
            variable=self.modo_var,
            command=self.ao_mudar_modo,
            font=("Segoe UI", 13, "bold"),
            height=35,
        )
        self.seg_button.pack(fill="x", padx=5, pady=10)

        dest_frame = ctk.CTkFrame(tab_atlas, fg_color=COR_FUNDO, corner_radius=8)
        dest_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(
            dest_frame,
            text="⚙ Config. Pasta",
            width=100,
            height=28,
            fg_color=COR_CARD,
            text_color=COR_TEXTO,
            command=self.selecionar_caminho_base,
        ).pack(side="right", padx=10, pady=10)
        self.lbl_dest_path = ctk.CTkLabel(
            dest_frame,
            text="",
            font=("Consolas", 11),
            text_color=COR_TEXTO,
            anchor="w",
            justify="left",
        )
        self.lbl_dest_path.pack(side="left", fill="x", expand=True, padx=10)
        self.lbl_dest_badge = ctk.CTkLabel(
            dest_frame,
            text="  —  ",
            font=("Segoe UI", 10, "bold"),
            fg_color=COR_CARD,
            corner_radius=6,
        )
        self.lbl_dest_badge.pack(side="right", padx=5)

        ctk.CTkButton(
            tab_atlas,
            text="Marcar/Desmarcar Todos",
            width=150,
            height=24,
            fg_color="transparent",
            text_color=COR_MUTED,
            hover_color=COR_FUNDO,
            command=self.toggle_all_atlas,
        ).pack(anchor="e", padx=5, pady=(10, 0))
        self.frame_checks = ctk.CTkScrollableFrame(
            tab_atlas, height=130, fg_color="transparent"
        )
        self.frame_checks.pack(fill="x", padx=5, pady=(0, 5))
        self.checkboxes = {}
        for centro in CENTROS_IMAGENS.keys():
            chk = ctk.CTkCheckBox(self.frame_checks, text=centro, font=("Segoe UI", 12))
            chk.pack(anchor="w", pady=4, padx=5)
            self.checkboxes[centro] = chk

        # ==========================================
        # CONSTRUÇÃO DA ABA SAP
        # ==========================================
        tab_sap = self.tabview.tab("⚙️ Módulo SAP")

        # --- PAINEL DE PASTAS SAP ---
        card_sap_dest = ctk.CTkFrame(tab_sap, fg_color=COR_FUNDO, corner_radius=8)
        card_sap_dest.pack(fill="x", padx=5, pady=(10, 10))
        ctk.CTkLabel(
            card_sap_dest,
            text="PASTAS DE DESTINO DOS RELATÓRIOS SAP",
            font=("Segoe UI", 10, "bold"),
            text_color=COR_MUTED,
        ).pack(anchor="w", padx=10, pady=(8, 2))

        row1 = ctk.CTkFrame(card_sap_dest, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(
            row1, text="Passo 1:", font=("Segoe UI", 11, "bold"), width=55, anchor="w"
        ).pack(side="left")
        self.lbl_sap1_path = ctk.CTkLabel(
            row1,
            text=self.caminho_sap1 or "Pasta não configurada",
            font=("Consolas", 10),
            text_color=COR_TEXTO if self.caminho_sap1 else COR_MUTED,
            anchor="w",
        )
        self.lbl_sap1_path.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(
            row1,
            text="⚙",
            width=30,
            height=20,
            fg_color=COR_CARD,
            text_color=COR_TEXTO,
            command=lambda: self.selecionar_caminho_sap(1),
        ).pack(side="right")

        row2 = ctk.CTkFrame(card_sap_dest, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(
            row2, text="Passo 2:", font=("Segoe UI", 11, "bold"), width=55, anchor="w"
        ).pack(side="left")
        self.lbl_sap2_path = ctk.CTkLabel(
            row2,
            text=self.caminho_sap2 or "Pasta não configurada",
            font=("Consolas", 10),
            text_color=COR_TEXTO if self.caminho_sap2 else COR_MUTED,
            anchor="w",
        )
        self.lbl_sap2_path.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(
            row2,
            text="⚙",
            width=30,
            height=20,
            fg_color=COR_CARD,
            text_color=COR_TEXTO,
            command=lambda: self.selecionar_caminho_sap(2),
        ).pack(side="right")

        row3 = ctk.CTkFrame(card_sap_dest, fg_color="transparent")
        row3.pack(fill="x", padx=10, pady=(4, 8))
        ctk.CTkLabel(
            row3, text="Passo 3:", font=("Segoe UI", 11, "bold"), width=55, anchor="w"
        ).pack(side="left")
        self.lbl_sap3_path = ctk.CTkLabel(
            row3,
            text=self.caminho_sap3 or "Pasta não configurada",
            font=("Consolas", 10),
            text_color=COR_TEXTO if self.caminho_sap3 else COR_MUTED,
            anchor="w",
        )
        self.lbl_sap3_path.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(
            row3,
            text="⚙",
            width=30,
            height=20,
            fg_color=COR_CARD,
            text_color=COR_TEXTO,
            command=lambda: self.selecionar_caminho_sap(3),
        ).pack(side="right")

        # --- TAREFAS SAP ---
        self.sap_tasks = {}

        chk_sap1 = ctk.CTkCheckBox(
            tab_sap,
            text="Passo 1: Centros (4020 + Múltiplos) - Layout /analisetmac",
            font=("Segoe UI", 12, "bold"),
            fg_color=COR_SAP,
        )
        chk_sap1.pack(anchor="w", padx=15, pady=(5, 5))
        self.sap_tasks["Passo 1"] = chk_sap1

        chk_sap2 = ctk.CTkCheckBox(
            tab_sap,
            text="Passo 2: Base Faturamento (4000 a 4199) - Layout /analisetmac",
            font=("Segoe UI", 12, "bold"),
            fg_color=COR_SAP,
        )
        chk_sap2.pack(anchor="w", padx=15, pady=5)
        self.sap_tasks["Passo 2"] = chk_sap2

        chk_sap3 = ctk.CTkCheckBox(
            tab_sap,
            text="Passo 3: Venda EXT (4000 a 4199) - Layout /VENDAEXT",
            font=("Segoe UI", 12, "bold"),
            fg_color=COR_SAP,
        )
        chk_sap3.pack(anchor="w", padx=15, pady=(5, 10))
        self.sap_tasks["Passo 3"] = chk_sap3

        # --- AGENDAMENTO AUTOMÁTICO ---
        card_agenda = ctk.CTkFrame(tab_sap, fg_color=COR_FUNDO, corner_radius=8)
        card_agenda.pack(fill="x", padx=5, pady=(8, 5))

        ctk.CTkLabel(
            card_agenda,
            text="AGENDAMENTO AUTOMÁTICO",
            font=("Segoe UI", 10, "bold"),
            text_color=COR_MUTED,
        ).pack(anchor="w", padx=10, pady=(8, 4))

        row_atlas = ctk.CTkFrame(card_agenda, fg_color="transparent")
        row_atlas.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(
            row_atlas,
            text="⏰ Atlas diário",
            font=("Segoe UI", 11),
            width=120,
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            row_atlas, text="Horário:", font=("Segoe UI", 11), text_color=COR_MUTED
        ).pack(side="left", padx=(0, 5))
        self.ent_horario_atlas = ctk.CTkEntry(
            row_atlas, width=58, height=26, placeholder_text="07:30"
        )
        self.ent_horario_atlas.insert(0, self.horario_atlas)
        self.ent_horario_atlas.pack(side="left")
        ctk.CTkLabel(
            row_atlas, text="  Seg–Sex", font=("Segoe UI", 10), text_color=COR_MUTED
        ).pack(side="left")

        row_sap = ctk.CTkFrame(card_agenda, fg_color="transparent")
        row_sap.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(
            row_sap,
            text="🔄 SAP downloads",
            font=("Segoe UI", 11),
            width=120,
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            row_sap, text="A cada", font=("Segoe UI", 11), text_color=COR_MUTED
        ).pack(side="left", padx=(0, 4))
        self.ent_intervalo_sap = ctk.CTkEntry(
            row_sap, width=32, height=26, placeholder_text="2"
        )
        self.ent_intervalo_sap.insert(0, self.intervalo_sap_h)
        self.ent_intervalo_sap.pack(side="left")
        ctk.CTkLabel(
            row_sap, text="h  início", font=("Segoe UI", 11), text_color=COR_MUTED
        ).pack(side="left", padx=(3, 4))
        self.ent_horario_sap = ctk.CTkEntry(
            row_sap, width=58, height=26, placeholder_text="07:00"
        )
        self.ent_horario_sap.insert(0, self.horario_sap_inicio)
        self.ent_horario_sap.pack(side="left")
        ctk.CTkLabel(
            row_sap, text="  Seg–Sex", font=("Segoe UI", 10), text_color=COR_MUTED
        ).pack(side="left")

        row_status = ctk.CTkFrame(card_agenda, fg_color="transparent")
        row_status.pack(fill="x", padx=10, pady=(4, 8))
        self.lbl_agenda_status = ctk.CTkLabel(
            row_status,
            text="○ Verificando...",
            font=("Segoe UI", 11),
            text_color=COR_MUTED,
        )
        self.lbl_agenda_status.pack(side="left")
        ctk.CTkButton(
            row_status,
            text="⚙ Configurar Agendamento",
            width=175,
            height=28,
            fg_color=COR_SAP,
            hover_color="#0284C7",
            command=self.configurar_agendamento,
        ).pack(side="right")
        # ==========================================
        self.lbl_unidade_status = ctk.CTkLabel(
            self,
            text="Pronto para iniciar.",
            font=("Segoe UI", 12),
            text_color=COR_MUTED,
            anchor="w",
        )
        self.lbl_unidade_status.pack(fill="x", padx=PAD, pady=(10, 5))

        self.btn_iniciar = ctk.CTkButton(
            self,
            text="▶   Iniciar Automação Global",
            height=50,
            corner_radius=10,
            text_color="white",
            font=("Segoe UI Semibold", 15, "bold"),
            command=self.start_thread,
        )
        self.btn_iniciar.pack(fill="x", padx=PAD, pady=(0, 10))

        # Terminal
        card_log = ctk.CTkFrame(
            self,
            fg_color=COR_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COR_BORDA,
        )
        card_log.pack(fill="both", expand=True, padx=PAD, pady=(0, 15))

        log_header = ctk.CTkFrame(card_log, fg_color="transparent")
        log_header.pack(fill="x", padx=16, pady=(10, 2))
        ctk.CTkLabel(
            log_header,
            text="TERMINAL DE EXECUÇÃO",
            font=("Segoe UI", 11, "bold"),
            text_color=COR_MUTED,
        ).pack(side="left")
        ctk.CTkButton(
            log_header,
            text="Limpar",
            width=60,
            height=24,
            fg_color="transparent",
            text_color=COR_MUTED,
            command=self.limpar_log,
        ).pack(side="right")

        self.log_text = ctk.CTkTextbox(
            card_log,
            fg_color=COR_TERMINAL_BG,
            text_color=COR_TERMINAL_FG,
            font=("Consolas", 11),
            border_width=0,
            corner_radius=8,
            state="disabled",
        )
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

    # --- FUNÇÕES AUXILIARES DE DATA (SAP) ---
    def get_data_hoje(self):
        return datetime.now().strftime("%d%m%Y")

    def get_primeiro_dia_mes_passado(self):
        hoje = datetime.now()
        primeiro_este_mes = hoje.replace(day=1)
        ultimo_mes_passado = primeiro_este_mes - timedelta(days=1)
        primeiro_mes_passado = ultimo_mes_passado.replace(day=1)
        return primeiro_mes_passado.strftime("%d%m%Y")

    # ==========================================
    # LÓGICA DO MÓDULO SAP
    # ==========================================
    def _keepalive_sap(self):
        """Ping leve ao SAP a cada 12 min para evitar expiração de sessão."""
        pythoncom.CoInitialize()
        while not self._keepalive_stop.wait(timeout=12 * 60):
            if getattr(self, "executando", False):
                continue  # Não interferir durante execução
            try:
                session = self.conectar_sap()
                if session:
                    _ = session.Info.SystemName  # leitura leve — reseta timeout
                else:
                    try:
                        if self.tray_icon:
                            self.tray_icon.notify(
                                "SAP não detectado — abra o SAP GUI antes da próxima execução",
                                "Mosaic RDE RPA",
                            )
                    except Exception:
                        pass
            except Exception:
                pass

    def conectar_sap(self):
        try:
            SapGuiAuto = win32com.client.GetObject("SAPGUI")
            Application = SapGuiAuto.GetScriptingEngine
            Connection = Application.Children(0)
            Session = Connection.Children(0)
            return Session
        except Exception:
            return None

    def exportar_alv_sap(self, Session, nome_arquivo, pasta_destino):
        """Função que extrai do SAP e usa o Python para mover para a pasta correta"""
        Session.findById("wnd[0]/tbar[1]/btn[43]").press()

        # MANDAMOS APENAS O NOME CURTO
        Session.findById(
            "wnd[1]/usr/subSUB_CONFIGURATION:SAPLSALV_GUI_CUL_EXPORT_AS:0512/txtGS_EXPORT-FILE_NAME"
        ).Text = nome_arquivo

        Session.findById("wnd[1]/tbar[0]/btn[20]").press()

        try:
            Session.findById(
                "wnd[1]/tbar[0]/btn[11]"
            ).press()  # Confirma sobrescrever se aparecer
        except:
            pass

        # Chama o cão de guarda
        self.mover_arquivo_sap(nome_arquivo, pasta_destino)

    def fechar_excel_silencioso(self, nome_arquivo_base):
        """Tenta encontrar e fechar apenas a planilha que o SAP abriu, sem fechar outras"""
        try:
            excel = win32com.client.GetObject(None, "Excel.Application")
            for wb in excel.Workbooks:
                if nome_arquivo_base in wb.Name:
                    wb.Close(SaveChanges=False)
                    self.adicionar_log("Excel fechado automaticamente.", "ok")
                    break
        except Exception:
            pass

    def mover_arquivo_sap(self, nome_arquivo_base, pasta_destino):
        self.adicionar_log("Localizando e movendo arquivo gerado pelo SAP...", "ok")

        # Adicionamos a pasta_destino na lista para o caso do SAP salvar direto nela
        pastas_alvo = [
            r"C:\TEMP",
            pasta_destino,
            os.path.join(os.environ.get("USERPROFILE"), "Documents", "SAP", "SAP GUI"),
            os.path.join(
                os.environ.get("USERPROFILE"),
                "OneDrive - The Mosaic Company",
                "Documents",
                "SAP",
                "SAP GUI",
            ),
            os.path.join(os.environ.get("USERPROFILE"), "Documents"),
            os.path.join(os.environ.get("USERPROFILE"), "Downloads"),
        ]

        tempo_inicio = time.time()
        for _ in range(40):
            if not self.executando:
                return

            for pasta in pastas_alvo:
                if not os.path.exists(pasta):
                    continue

                try:
                    arquivos = [
                        f
                        for f in os.listdir(pasta)
                        if f.startswith(nome_arquivo_base)
                        and f.lower().endswith((".xls", ".xlsx", ".mhtml"))
                    ]
                    if arquivos:
                        caminho_recente = max(
                            [os.path.join(pasta, f) for f in arquivos],
                            key=os.path.getmtime,
                        )

                        if os.path.getmtime(caminho_recente) > (tempo_inicio - 120):
                            time.sleep(2)  # Aguarda o SAP terminar de escrever

                            # 1. FECHA O EXCEL PRIMEIRO (Quebra o bloqueio do Windows)
                            self.fechar_excel_silencioso(nome_arquivo_base)
                            time.sleep(
                                1
                            )  # Dá 1 segundo para o Windows liberar o arquivo de vez

                            # 2. SE JÁ ESTIVER NA PASTA CERTA, SÓ AVISA E SAI
                            if os.path.normpath(pasta) == os.path.normpath(
                                pasta_destino
                            ):
                                self.adicionar_log(
                                    f"Arquivo SAP guardado na pasta correta!", "suc"
                                )
                                return True

                            # 3. SE ESTIVER NO TEMP (OU OUTRO LUGAR), MOVE PARA O DESTINO
                            nome_final = os.path.basename(caminho_recente)
                            destino_completo = os.path.join(pasta_destino, nome_final)

                            if os.path.exists(destino_completo):
                                os.remove(destino_completo)

                            shutil.move(caminho_recente, destino_completo)
                            self.adicionar_log(
                                f"Arquivo SAP guardado na pasta correta!", "suc"
                            )

                            return True
                except Exception:
                    pass
            time.sleep(1)

        self.adicionar_log(
            "Aviso: O SAP gerou o arquivo, mas o robô não o encontrou ou não conseguiu mover.",
            "err",
        )
        return False

    # ==========================================
    # AGENDAMENTO DO WINDOWS TASK SCHEDULER
    # ==========================================
    def _verificar_agendamento(self):
        """Verifica se as tarefas já estão registradas e atualiza o status."""
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-ScheduledTask -TaskName 'Mosaic RPA - Atlas Diario'"
                    " -ErrorAction SilentlyContinue"
                    " | Select-Object -ExpandProperty State",
                ],
                capture_output=True,
                text=True,
                timeout=6,
            )
            if result.returncode == 0 and result.stdout.strip():
                self.lbl_agenda_status.configure(
                    text="● Agendamento ativo", text_color=COR_SUCCESS
                )
            else:
                self.lbl_agenda_status.configure(
                    text="○ Não configurado", text_color=COR_MUTED
                )
        except Exception:
            self.lbl_agenda_status.configure(
                text="○ Status desconhecido", text_color=COR_MUTED
            )

    def configurar_agendamento(self):
        """Cria/atualiza as tarefas no Agendador de Tarefas do Windows."""
        import re
        import tempfile

        horario_atlas = self.ent_horario_atlas.get().strip() or "07:30"
        horario_sap = self.ent_horario_sap.get().strip() or "07:00"
        intervalo = self.ent_intervalo_sap.get().strip() or "2"

        if not re.match(r"^\d{1,2}:\d{2}$", horario_atlas) or not re.match(
            r"^\d{1,2}:\d{2}$", horario_sap
        ):
            messagebox.showerror(
                "Erro", "Formato de horário inválido. Use HH:MM (ex: 07:30)"
            )
            return

        try:
            intervalo_int = int(intervalo)
            if not 1 <= intervalo_int <= 12:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Erro", "Intervalo SAP deve ser um número entre 1 e 12."
            )
            return

        self.salvar_config(
            horario_atlas=horario_atlas,
            horario_sap_inicio=horario_sap,
            intervalo_sap_h=intervalo,
        )

        # Monta o comando de launch (script ou exe)
        if getattr(sys, "frozen", False):
            exe = sys.executable
            arg_a = f"{exe} --auto-atlas"
            arg_s = f"{exe} --auto-sap"
            wd = os.path.dirname(exe)
        else:
            exe = sys.executable
            scr = os.path.abspath(sys.argv[0])
            arg_a = f'{exe} "{scr}" --auto-atlas'
            arg_s = f'{exe} "{scr}" --auto-sap'
            wd = os.path.dirname(scr)

        h_start = int(horario_sap.split(":")[0])
        duration_h = max(1, 20 - h_start)

        # Gera o Configurar_Agendamento.ps1 com as configurações atuais
        if getattr(sys, "frozen", False):
            proj_dir = os.path.dirname(sys.executable)
        else:
            proj_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        ps_path = os.path.join(proj_dir, "Configurar_Agendamento.ps1")

        # Argumentos que o Python vai receber (sem incluir o próprio executável)
        arg_a_clean = arg_a.replace(exe, "").strip()
        arg_s_clean = arg_s.replace(exe, "").strip()

        ps_lines = [
            "# =========================================================",
            "# Mosaic RDE RPA - Configurador de Agendamento",
            "# Execute com: clique direito > 'Executar com PowerShell'",
            "# (Administrador necessario para registrar as tarefas)",
            "# =========================================================",
            "",
            f"$Exe     = '{exe}'",
            f"$ArgA    = '{arg_a_clean}'",
            f"$ArgS    = '{arg_s_clean}'",
            f"$WorkDir = '{wd}'",
            "",
            "if (-not (Test-Path $Exe)) { Write-Host 'ERRO: Python nao encontrado.' -ForegroundColor Red; pause; exit 1 }",
            "",
            f"# --- TAREFA 1: Atlas Diario (Seg-Sex {horario_atlas}) ---",
            "$a1 = New-ScheduledTaskAction -Execute $Exe -Argument $ArgA -WorkingDirectory $WorkDir",
            f"$t1 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At '{horario_atlas}'",
            "$s1 = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew -StartWhenAvailable",
            "Register-ScheduledTask -TaskName 'Mosaic RPA - Atlas Diario' -Action $a1 -Trigger $t1 -Settings $s1 -Force | Out-Null",
            f"Write-Host '  [OK] Atlas Diario : Seg-Sex as {horario_atlas}' -ForegroundColor Green",
            "",
            f"# --- TAREFA 2: SAP a cada {intervalo_int}h (inicio {horario_sap}) ---",
            "$a2 = New-ScheduledTaskAction -Execute $Exe -Argument $ArgS -WorkingDirectory $WorkDir",
            f"$t2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At '{horario_sap}'",
            f"$rep = New-ScheduledTaskTrigger -Once -At '{horario_sap}' -RepetitionInterval (New-TimeSpan -Hours {intervalo_int}) -RepetitionDuration (New-TimeSpan -Hours {duration_h})",
            "$t2.Repetition = $rep.Repetition",
            "$s2 = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew -StartWhenAvailable",
            "Register-ScheduledTask -TaskName 'Mosaic RPA - SAP 2h' -Action $a2 -Trigger $t2 -Settings $s2 -Force | Out-Null",
            f"Write-Host '  [OK] SAP a cada {intervalo_int}h : Seg-Sex, {horario_sap} ate 20:00' -ForegroundColor Green",
            "",
            "Write-Host ''",
            "Write-Host 'Agendamento configurado com sucesso!' -ForegroundColor Cyan",
            "pause",
        ]

        try:
            with open(ps_path, "w", encoding="utf-8-sig") as f:
                f.write("\n".join(ps_lines))

            # Abre o Explorer selecionando o arquivo gerado
            subprocess.Popen(["explorer", f"/select,{ps_path}"])

            self.adicionar_log(
                "📁 'Configurar_Agendamento.ps1' atualizado com os horários definidos.",
                "suc",
            )
            self.adicionar_log(
                "➡ Solicite à TI para executar o arquivo como Administrador.", "ok"
            )
            self.adicionar_log(
                f"   Atlas: {horario_atlas} | SAP: a cada {intervalo_int}h a partir de {horario_sap}",
                "ok",
            )
        except Exception as e:
            self.adicionar_log(f"Erro ao gerar arquivo: {str(e)}", "err")

    def executar_sap_passo1(self, Session):
        self.adicionar_log("SAP: Iniciando Passo 1 (Centros Relatório)...", "ok")
        Session.findById("wnd[0]").maximize()
        Session.findById("wnd[0]/tbar[0]/okcd").Text = "/n zotc_bill_prod_order"
        Session.findById("wnd[0]").sendVKey(0)

        Session.findById("wnd[0]/usr/ctxtS_WERKS-LOW").Text = "4020"
        Session.findById("wnd[0]/usr/ctxtS_ERDAT-LOW").Text = "01012026"
        Session.findById("wnd[0]/usr/ctxtS_ERDAT-HIGH").Text = self.get_data_hoje()

        Session.findById("wnd[0]/usr/btn%_S_WERKS_%_APP_%-VALU_PUSH").press()

        tbl = Session.findById(
            "wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE"
        )
        centros = ["4040", "4060", "4070", "4100", "4110", "4120", "4130", "4084"]
        for i, c in enumerate(centros):
            tbl.findById(f"ctxtRSCSEL_255-SLOW_I[1,{i+1}]").Text = c

        Session.findById("wnd[1]").sendVKey(0)

        tbl2 = Session.findById(
            "wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE"
        )
        tbl2.findById("ctxtRSCSEL_255-SLOW_I[1,9]").Text = "4140"

        Session.findById("wnd[1]/tbar[0]/btn[8]").press()
        Session.findById("wnd[0]/usr/ctxtP_LAYOUT").Text = "/analisetmac"
        Session.findById("wnd[0]/tbar[1]/btn[8]").press()

        nome_arq = f"Carregamento Bill {datetime.now().year}"
        self.exportar_alv_sap(Session, nome_arq, self.caminho_sap1)

        self.adicionar_log(f"✅ SAP Passo 1 Concluído! ({nome_arq})", "suc")
        return True

    def executar_sap_passo2(self, Session):
        self.adicionar_log("SAP: Iniciando Passo 2 (Base Faturamento)...", "ok")
        data_ini = self.get_primeiro_dia_mes_passado()
        data_fim = self.get_data_hoje()

        Session.findById("wnd[0]").maximize()
        Session.findById("wnd[0]/tbar[0]/okcd").Text = "/n zotc_bill_prod_order"
        Session.findById("wnd[0]").sendVKey(0)

        Session.findById("wnd[0]/usr/ctxtS_WERKS-LOW").Text = "4000"
        Session.findById("wnd[0]/usr/ctxtS_WERKS-HIGH").Text = "4199"
        Session.findById("wnd[0]/usr/ctxtS_ERDAT-LOW").Text = data_ini
        Session.findById("wnd[0]/usr/ctxtS_ERDAT-HIGH").Text = data_fim
        Session.findById("wnd[0]/usr/ctxtP_LAYOUT").Text = "/analisetmac"

        Session.findById("wnd[0]/tbar[1]/btn[8]").press()

        nome_arq = "Base Faturamento"
        self.exportar_alv_sap(Session, nome_arq, self.caminho_sap2)

        self.adicionar_log(
            f"✅ SAP Passo 2 Concluído! ({data_ini} a {data_fim})", "suc"
        )
        return True

    def executar_sap_passo3(self, Session):
        self.adicionar_log("SAP: Iniciando Passo 3 (Venda EXT)...", "ok")
        data_ini = self.get_primeiro_dia_mes_passado()
        data_fim = self.get_data_hoje()

        Session.findById("wnd[0]").maximize()
        Session.findById("wnd[0]/tbar[0]/okcd").Text = "/n zotc_bill_prod_order"
        Session.findById("wnd[0]").sendVKey(0)

        Session.findById("wnd[0]/usr/ctxtS_WERKS-LOW").Text = "4000"
        Session.findById("wnd[0]/usr/ctxtS_WERKS-HIGH").Text = "4199"
        Session.findById("wnd[0]/usr/ctxtS_ERDAT-LOW").Text = data_ini
        Session.findById("wnd[0]/usr/ctxtS_ERDAT-HIGH").Text = data_fim
        Session.findById("wnd[0]/usr/ctxtP_LAYOUT").Text = "/VENDAEXT"

        Session.findById("wnd[0]/tbar[1]/btn[8]").press()

        nome_arq = "Base Venda EXT ( VCO, Biosciente & Armazém )"
        self.exportar_alv_sap(Session, nome_arq, self.caminho_sap3)

        self.adicionar_log(
            f"✅ SAP Passo 3 Concluído! ({data_ini} a {data_fim})", "suc"
        )
        return True

    # ==========================================
    # LÓGICA DO MÓDULO ATLAS (COM SUPORTE A RECEPÇÃO)
    # ==========================================
    def verificar_senha_incorreta(self):
        """Verifica silenciosamente se apareceu o aviso de senha incorreta."""
        try:
            pos = pyautogui.locateCenterOnScreen(
                "assets/aviso_senha_incorreta.png", confidence=0.7, minSearchTime=3
            )
            if pos:
                self.adicionar_log(
                    "⚠️ AVISO: Senha incorreta! Clicando em OK...", "err"
                )
                self.senha_incorreta = True
                try:
                    pos_ok = pyautogui.locateCenterOnScreen(
                        "assets/ok_senha_incorreta.png",
                        confidence=0.7,
                        minSearchTime=2,
                    )
                    if pos_ok:
                        pyautogui.click(pos_ok)
                        time.sleep(1)
                except Exception:
                    pass
                return True
        except Exception:
            pass
        return False

    def clicar_img(
        self,
        img,
        desc,
        timeout=15,
        max_tentativas=4,
        confidence=0.7,
        double=False,
        click_type="standard",
    ):
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
                        pos = pyautogui.locateCenterOnScreen(
                            img, confidence=confidence, region=search_region
                        )
                    else:
                        pos = pyautogui.locateCenterOnScreen(img, confidence=confidence)

                    if pos:
                        if click_type == "force":
                            pyautogui.moveTo(pos.x, pos.y, duration=0.1)
                            pyautogui.mouseDown()
                            time.sleep(0.05)
                            pyautogui.mouseUp()
                            time.sleep(0.15)
                        elif double:
                            pyautogui.doubleClick(pos)
                        else:
                            pyautogui.click(pos)
                        self.adicionar_log(f"{desc} encontrado!", "ok")
                        return True
                except:
                    pass
                time.sleep(0.2)
            if tentativa < max_tentativas:
                self.adicionar_log("Timeout: Fechando possível pop-up...", "err")
                pyautogui.press("esc")
                time.sleep(1.5)
        self.adicionar_log(f"ERRO: '{desc}' não encontrado.", "err")
        return False

    def fechar_atlas(self):
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "AtlasBrowser.exe"],
                capture_output=True,
                text=True,
                check=False,
            )
            time.sleep(2)
        except:
            pass

    def iniciar_sessao_atlas(self, unidade, user_atual, pass_atual):
        self.senha_incorreta = False

        try:
            self.after(0, self.iconify)

            if unidade in ["PGUA 1", "PGUA 2"]:
                os.startfile(CAMINHO_ATLAS_EXE)
                if not self.clicar_img(
                    "assets/selectcenter.png", "Seletor de centro", timeout=40
                ):
                    return False
                if not self.clicar_img(CENTROS_IMAGENS["PGUA 1"], "PGUA 1 (Login)"):
                    return False
                if not self.clicar_img(
                    "assets/atlas_cargo.png",
                    "Botão Iniciar",
                    timeout=15,
                    click_type="force",
                ):
                    return False

                if self.clicar_img("assets/user.png", "Campo usuário", timeout=15):
                    pyautogui.write(user_atual)
                    if not self.clicar_img("assets/senha.png", "Campo senha"):
                        return False
                    pyautogui.write(pass_atual)
                    pyautogui.press("enter")
                else:
                    return False

                if self.verificar_senha_incorreta():
                    return False

                time.sleep(2)
                if self.clicar_img(
                    "assets/abrir_botaopg2.png", "Botão Seletor Interno", timeout=15
                ):
                    time.sleep(1)
                    if unidade == "PGUA 1":
                        pyautogui.press("down")
                        time.sleep(0.5)
                        pyautogui.press("enter")
                    else:
                        pyautogui.press("up")
                        pyautogui.press("up")
                        time.sleep(0.5)
                        pyautogui.press("enter")
                else:
                    return False
            else:
                os.startfile(CAMINHO_ATLAS_EXE)
                if not self.clicar_img(
                    "assets/selectcenter.png", "Seletor", timeout=40
                ):
                    return False
                if not self.clicar_img(CENTROS_IMAGENS[unidade], unidade):
                    return False
                if not self.clicar_img(
                    "assets/atlas_cargo.png", "Iniciar", timeout=15, click_type="force"
                ):
                    return False

                if self.clicar_img("assets/user.png", "Usuário", timeout=15):
                    pyautogui.write(user_atual)
                    if not self.clicar_img("assets/senha.png", "Senha"):
                        return False
                    pyautogui.write(pass_atual)
                    pyautogui.press("enter")
                else:
                    return False

                if self.verificar_senha_incorreta():
                    return False

            time.sleep(1.5)
            return True
        except Exception as e:
            self.adicionar_log(f"Erro ao iniciar sessão Atlas: {str(e)}", "err")
            return False

    def _abrir_menu_relatorios(self, unidade):
        """Abre o menu Impressão → Relatórios com re-tentativa completa do ciclo"""
        if unidade in ["CATALÃO", "PALMEIRANTE"]:
            img_impressao = "assets/impressao_catalao.png"
            img_relatorios = "assets/relatorio_catalao.png"
        else:
            img_impressao = "assets/impressao.png"
            img_relatorios = "assets/relatorios.png"

        for _ in range(4):
            # Clica em Impressão (1 tentativa por ciclo — se não aparecer, problema maior)
            if not self.clicar_img(
                img_impressao,
                "Impressão",
                timeout=25,
                click_type="force",
                max_tentativas=1,
            ):
                return False
            time.sleep(0.5)
            # Procura Relatórios com 1 tentativa; se falhar, re-abre o menu
            if self.clicar_img(
                img_relatorios,
                "Relatórios",
                click_type="force",
                timeout=15,
                max_tentativas=1,
            ):
                return True
            # Menu fechou antes de encontrar Relatórios — pressiona esc e recomeça
            pyautogui.press("esc")
            time.sleep(2)

        return False

    def _preencher_data_inicial(self):
        """Preenche a data inicial com o primeiro dia do mês"""
        hoje = datetime.now()
        primeiro_dia = hoje.strftime("01/%m/%Y")

        if self.clicar_img(
            "assets/secao_data_inicial.png", "Data inicial", double=True
        ):
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")
            pyautogui.write(primeiro_dia)
            pyautogui.press("tab")
            for _ in range(3):
                pyautogui.hotkey("ctrl", "a")
                pyautogui.write("0")
                pyautogui.press("tab")
            return True
        return False

    def _selecionar_relatorio_tipo(self, unidade, modo):
        """Seleciona o tipo de relatório (UBR, Balança, Recepção)"""
        if modo == "Recepção":
            recepcao_asset = RECEPCAO_ASSETS.get(unidade, "relatorio_recepcao.png")
            return self.clicar_img(f"assets/{recepcao_asset}", "Relatório Recepção")
        elif unidade == "UBERABA":
            return self.clicar_img("assets/relatorios_ubr.png", "Relatórios UBR")
        else:
            return self.clicar_img("assets/relatordiariobal.png", "Relatório Balança")

    def _selecionar_rota_ou_fluxo(self, unidade, modo_rota):
        """Seleciona Rota ou Fluxo com fallback para RECEPÇÃO em maiúscula"""
        if unidade in ["UBERABA", "RONDONÓPOLIS"]:
            if self.clicar_img("assets/selectfluxo.png", "Fluxo"):
                pyautogui.write(modo_rota)
                pyautogui.press("down")
                pyautogui.press("tab")
                time.sleep(0.5)
                return True
            return False
        else:
            if self.clicar_img("assets/selectrota.png", "Rota"):
                if modo_rota == "DESCARGA":
                    # Para descarga, tenta Recepção ou RECEPÇÃO
                    for img, nome in [
                        ("assets/rota_descarga.png", "Recepção"),
                        ("assets/rota_descarga2.png", "RECEPÇÃO"),
                    ]:
                        if self.clicar_img(img, nome, timeout=2, max_tentativas=1):
                            return True
                    return False
                else:
                    # Para carregamento, usa Expedição
                    return self.clicar_img("assets/rota_exped.png", "Expedição")
            return False

    def _finalizar_relatorio(self):
        """Finaliza gerando o relatório (Tipo saída, Excel, Gerar)"""
        if not self.clicar_img("assets/selecttype.png", "Tipo saída"):
            return False
        time.sleep(0.5)
        if not self.clicar_img("assets/tipo_excel.png", "Excel"):
            return False
        time.sleep(0.8)
        return self.clicar_img("assets/gerar_relatorio.png", "Gerar")

    def executar_relatorio_atlas(self, unidade, modo_especifico):
        is_descarga = modo_especifico == "Descarga"
        is_recepcao = modo_especifico == "Recepção"
        is_carregamento = modo_especifico == "Carregamento"

        try:
            # Garante estado limpo antes de navegar pelo menu
            pyautogui.press("esc")
            time.sleep(0.5)

            hoje = datetime.now()

            # --- BLOCO DE DESCARGA ---
            if is_descarga:
                if not self._abrir_menu_relatorios(unidade):
                    return False
                if not self._selecionar_relatorio_tipo(unidade, "Descarga"):
                    return False
                if not self._preencher_data_inicial():
                    return False
                if not self._selecionar_rota_ou_fluxo(unidade, "DESCARGA"):
                    return False
                if not self._finalizar_relatorio():
                    return False
                if not self.mover_arquivo_atlas(
                    unidade, hoje.strftime("%m.%Y"), is_descarga
                ):
                    return False

            # --- BLOCO DE RECEPÇÃO ---
            elif is_recepcao:
                if not self._abrir_menu_relatorios(unidade):
                    return False
                if not self._selecionar_relatorio_tipo(unidade, "Recepção"):
                    return False
                if not self._preencher_data_inicial():
                    return False
                if not self._finalizar_relatorio():
                    return False
                if not self.mover_arquivo_recepcao(unidade, hoje.strftime("%m.%Y")):
                    return False

            # --- BLOCO DE CARREGAMENTO ---
            elif is_carregamento:
                if unidade in ["UBERABA", "RONDONÓPOLIS"]:
                    pos_seta = pyautogui.locateCenterOnScreen(
                        "assets/seta_key.png", confidence=0.7
                    )
                    if not pos_seta:
                        return False
                    pyautogui.click(pos_seta)
                    time.sleep(0.3)
                    pyautogui.click(pos_seta)
                    time.sleep(0.3)
                    pyautogui.press("esc")
                    time.sleep(0.2)
                    pyautogui.write("CARREGAMENTO")
                    pyautogui.press("down")
                    if not self.clicar_img("assets/gerar_relatorio.png", "Gerar"):
                        return False
                    time.sleep(0.5)
                else:
                    # Para as demais unidades, usa o fluxo novo com seta_keymax
                    pos_seta = pyautogui.locateCenterOnScreen(
                        "assets/seta_keymax.png", confidence=0.7
                    )
                    if not pos_seta:
                        return False
                    pyautogui.click(pos_seta)
                    time.sleep(0.3)
                    if not self.clicar_img(
                        "assets/click_setamax.png", "Click Seta Max"
                    ):
                        return False
                    if not self.clicar_img("assets/gerar_relatorio.png", "Gerar"):
                        return False
                    time.sleep(0.5)

                if not self.mover_arquivo_atlas(unidade, hoje.strftime("%m.%Y"), False):
                    return False

            return True
        except Exception as e:
            self.adicionar_log(
                f"Erro ao gerar relatório ({modo_especifico}): {str(e)}", "err"
            )
            return False

    def executar_robo_atlas(self, unidade, modo_especifico):
        user_atual = self.ent_user.get().strip()
        pass_atual = self.ent_pass.get().strip()
        if not self.iniciar_sessao_atlas(unidade, user_atual, pass_atual):
            return False
        return self.executar_relatorio_atlas(unidade, modo_especifico)

    def mover_arquivo_atlas(self, unidade, mes_ano, is_descarga):
        tempo_inicio = time.time()
        nomes_carr = {
            "PGUA 1": "Paranagua 1",
            "PGUA 2": "Paranagua 2",
            "UBERABA": "Uberaba",
            "SORRISO": "Sorriso",
            "RONDONÓPOLIS": "Rondonópolis",
            "RIO VERDE": "Rio Verde",
            "RIO GRANDE": "Rio Grande",
            "CATALÃO": "Catalão",
            "CANDEIAS": "Candeias",
            "PALMEIRANTE": "Palmeirante",
        }
        nums_desc = {
            "PGUA 1": "4020",
            "CANDEIAS": "4040",
            "SORRISO": "4060",
            "RIO VERDE": "4070",
            "CATALÃO": "4100",
            "RONDONÓPOLIS": "4110",
            "UBERABA": "4120",
            "PGUA 2": "4130",
            "RIO GRANDE": "4140",
            "PALMEIRANTE": "4170",
        }

        for _ in range(60):
            if not self.executando:
                return False
            arquivos = [
                f
                for f in os.listdir(CAMINHO_DOWNLOADS)
                if f.lower().endswith((".xls", ".xlsx"))
            ]
            if arquivos:
                caminho_recente = max(
                    [os.path.join(CAMINHO_DOWNLOADS, f) for f in arquivos],
                    key=os.path.getmtime,
                )
                if os.path.getmtime(caminho_recente) < tempo_inicio:
                    time.sleep(1)
                    continue

                nome_original = os.path.basename(caminho_recente)
                if not nome_original.endswith((".tmp", ".crdownload")):
                    time.sleep(2)
                    try:
                        ext = os.path.splitext(nome_original)[1]
                        if is_descarga:
                            num = nums_desc.get(unidade, "0000")
                            novo_nome = (
                                f"{mes_ano} - {num} RelPesagensDiarioBalancaRoo{ext}"
                            )
                            pasta_dest = os.path.join(self.caminho_descarga, num)
                            os.makedirs(pasta_dest, exist_ok=True)
                            destino = os.path.join(pasta_dest, novo_nome)
                        else:
                            nome_exib = nomes_carr.get(unidade, unidade)
                            novo_nome = f"{nome_exib} {mes_ano}{ext}"
                            destino = os.path.join(self.caminho_carregamento, novo_nome)

                        if os.path.exists(destino):
                            os.remove(destino)
                        shutil.move(caminho_recente, destino)
                        self.adicionar_log(f"Salvo: {novo_nome}", "suc")
                        return True
                    except Exception as e:
                        self.adicionar_log(f"Falha ao mover: {str(e)}", "err")
            time.sleep(1)
        self.adicionar_log("Timeout: Excel não baixou.", "err")
        return False

    def mover_arquivo_recepcao(self, unidade, mes_ano):
        """Move arquivo de Recepção para a pasta correta com nomenclatura padrão"""
        tempo_inicio = time.time()
        nums_recepcao = {
            "PGUA 1": "4020",
            "CANDEIAS": "4040",
            "SORRISO": "4060",
            "RIO VERDE": "4070",
            "CATALÃO": "4100",
            "RONDONÓPOLIS": "4110",
            "UBERABA": "4120",
            "PGUA 2": "4130",
            "RIO GRANDE": "4140",
            "PALMEIRANTE": "4170",
        }

        for _ in range(60):
            if not self.executando:
                return False
            arquivos = [
                f
                for f in os.listdir(CAMINHO_DOWNLOADS)
                if f.lower().endswith((".xls", ".xlsx"))
            ]
            if arquivos:
                caminho_recente = max(
                    [os.path.join(CAMINHO_DOWNLOADS, f) for f in arquivos],
                    key=os.path.getmtime,
                )
                if os.path.getmtime(caminho_recente) < tempo_inicio:
                    time.sleep(1)
                    continue

                nome_original = os.path.basename(caminho_recente)
                if not nome_original.endswith((".tmp", ".crdownload")):
                    time.sleep(2)
                    try:
                        ext = os.path.splitext(nome_original)[1]
                        num = nums_recepcao.get(unidade, "0000")
                        novo_nome = f"{mes_ano} - {num} RelRecepcao{ext}"
                        pasta_dest = os.path.join(self.caminho_recepcao, num)
                        os.makedirs(pasta_dest, exist_ok=True)
                        destino = os.path.join(pasta_dest, novo_nome)

                        if os.path.exists(destino):
                            os.remove(destino)
                        shutil.move(caminho_recente, destino)
                        self.adicionar_log(f"Salvo: {novo_nome}", "suc")
                        return True
                    except Exception as e:
                        self.adicionar_log(f"Falha ao mover: {str(e)}", "err")
            time.sleep(1)

        self.adicionar_log("Timeout: Excel não baixou.", "err")
        return False

    # ==========================================
    # BANDEJA DO SISTEMA (SYSTEM TRAY)
    # ==========================================
    def _criar_icone_tray(self):
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            [0, 0, size - 1, size - 1], radius=14, fill=(59, 130, 246, 255)
        )
        w = (255, 255, 255, 255)
        draw.rectangle([10, 12, 18, 52], fill=w)
        draw.rectangle([46, 12, 54, 52], fill=w)
        draw.polygon([(10, 12), (18, 12), (32, 33), (24, 33)], fill=w)
        draw.polygon([(54, 12), (46, 12), (32, 33), (40, 33)], fill=w)
        return img

    def _setup_tray(self):
        try:
            icone = self._criar_icone_tray()
            menu = pystray.Menu(
                pystray.MenuItem("Abrir painel", self._tray_mostrar, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("▶ Executar Atlas agora", self._tray_run_atlas),
                pystray.MenuItem("▶ Executar SAP agora", self._tray_run_sap),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Fechar", self._tray_sair),
            )
            self.tray_icon = pystray.Icon(
                "MosaicRPA", icone, "Mosaic RDE RPA v2.1", menu
            )
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception:
            self.tray_icon = None

    def _minimizar_para_tray(self):
        self.withdraw()

    def _tray_mostrar(self, icon=None, item=None):
        self.after(0, self.deiconify)
        self.after(0, self.lift)
        self.after(0, self.focus_force)

    def _tray_run_atlas(self, icon=None, item=None):
        self._tray_mostrar()

        def _run():
            self.auto_mode = "atlas"
            self.auto_close = False
            self._auto_iniciar()

        self.after(600, _run)

    def _tray_run_sap(self, icon=None, item=None):
        self._tray_mostrar()

        def _run():
            self.auto_mode = "sap"
            self.auto_close = False
            self._auto_iniciar()

        self.after(600, _run)

    def _tray_sair(self, icon=None, item=None):
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        self.after(0, self.destroy)

    # ==========================================
    # GERENCIAMENTO DE EXECUÇÃO
    # ==========================================
    def _auto_iniciar(self):
        """Disparado automaticamente via --auto-atlas ou --auto-sap."""
        if self.auto_mode == "atlas":
            for chk in self.checkboxes.values():
                chk.select()
            self.modo_var.set("🔄 Ambos")
            self.ao_mudar_modo("🔄 Ambos")
        elif self.auto_mode == "sap":
            for chk in self.sap_tasks.values():
                chk.select()
        self.start_thread()

    def start_thread(self):
        centros_atlas = [c for c, chk in self.checkboxes.items() if chk.get() == 1]
        passos_sap = [p for p, chk in self.sap_tasks.items() if chk.get() == 1]

        if not centros_atlas and not passos_sap:
            messagebox.showwarning(
                "Atenção", "Selecione pelo menos um Centro no Atlas ou um Passo no SAP."
            )
            return

        # Validações Atlas
        if centros_atlas:
            if not self.ent_user.get().strip() or not self.ent_pass.get().strip():
                messagebox.showwarning(
                    "Atenção", "Preencha as credenciais na aba Módulo ATLAS."
                )
                return
            modo_atual = self.modo_var.get()
            if "Ambos" in modo_atual and (
                not self.caminho_descarga
                or not self.caminho_carregamento
                or not self.caminho_recepcao
            ):
                messagebox.showwarning(
                    "Atenção",
                    "Configure as pastas de Descarga, Carregamento e Recepção.",
                )
                return
            elif "Ambos" not in modo_atual:
                if "Descarga" in modo_atual:
                    req = self.caminho_descarga
                elif "Recepção" in modo_atual:
                    req = self.caminho_recepcao
                else:
                    req = self.caminho_carregamento
                if not req or not os.path.exists(req):
                    messagebox.showwarning(
                        "Atenção", "Configure a pasta de destino no Atlas."
                    )
                    return

        # Validações SAP
        if "Passo 1" in passos_sap and not self.caminho_sap1:
            messagebox.showwarning(
                "Atenção", "Configure a Pasta de Destino para o Passo 1 do SAP."
            )
            return
        if "Passo 2" in passos_sap and not self.caminho_sap2:
            messagebox.showwarning(
                "Atenção", "Configure a Pasta de Destino para o Passo 2 do SAP."
            )
            return
        if "Passo 3" in passos_sap and not self.caminho_sap3:
            messagebox.showwarning(
                "Atenção", "Configure a Pasta de Destino para o Passo 3 do SAP."
            )
            return

        self.executando = True
        self.btn_iniciar.configure(state="disabled", text="⏹   Executando...")
        self.ent_user.configure(state="disabled")
        self.ent_pass.configure(state="disabled")
        threading.Thread(target=self.executar_sequencial, daemon=True).start()

    def executar_sequencial(self):
        pythoncom.CoInitialize()

        centros_atlas = [c for c, chk in self.checkboxes.items() if chk.get() == 1]
        passos_sap = [p for p, chk in self.sap_tasks.items() if chk.get() == 1]

        modo_geral = self.modo_var.get()
        if "Ambos" in modo_geral:
            modos_a_rodar = ["Descarga", "Carregamento", "Recepção"]
        elif "Descarga" in modo_geral:
            modos_a_rodar = ["Descarga"]
        elif "Recepção" in modo_geral:
            modos_a_rodar = ["Recepção"]
        else:
            modos_a_rodar = ["Carregamento"]

        total_tarefas = (len(centros_atlas) * len(modos_a_rodar)) + len(passos_sap)
        sucessos, falhas, contador = 0, 0, 0
        lista_falhas = []

        # --- ROTINA ATLAS ---
        if centros_atlas:
            self.adicionar_log("--- INICIANDO ROTINA ATLAS ---", "ok")
            for centro in centros_atlas:
                if "Ambos" in modo_geral:
                    user_atual = self.ent_user.get().strip()
                    pass_atual = self.ent_pass.get().strip()

                    self.adicionar_log(
                        f"\n--- Atlas: {centro} | Login único para 3 relatórios ---"
                    )

                    if self.iniciar_sessao_atlas(centro, user_atual, pass_atual):
                        for modo in modos_a_rodar:
                            if not self.executando:
                                break

                            contador += 1
                            self._set_unidade_status(
                                f"[{contador}/{total_tarefas}] Atlas: {centro} ({modo})"
                            )
                            self.adicionar_log(f"--- Atlas: {centro} | {modo} ---")

                            if self.executar_relatorio_atlas(centro, modo):
                                sucessos += 1
                            else:
                                falhas += 1
                                lista_falhas.append(f"Atlas: {centro} ({modo})")
                    else:
                        for modo in modos_a_rodar:
                            contador += 1
                            self._set_unidade_status(
                                f"[{contador}/{total_tarefas}] Atlas: {centro} ({modo})"
                            )
                            falhas += 1
                            lista_falhas.append(f"Atlas: {centro} ({modo})")

                    self.fechar_atlas()
                    time.sleep(1)
                else:
                    for modo in modos_a_rodar:
                        if not self.executando:
                            break
                        contador += 1
                        self._set_unidade_status(
                            f"[{contador}/{total_tarefas}] Atlas: {centro} ({modo})"
                        )
                        self.adicionar_log(f"\n--- Atlas: {centro} | {modo} ---")

                        if self.executar_robo_atlas(centro, modo):
                            sucessos += 1
                        else:
                            falhas += 1
                            lista_falhas.append(f"Atlas: {centro} ({modo})")
                        self.fechar_atlas()
                        time.sleep(1)

        # --- ROTINA SAP ---
        if passos_sap and self.executando:
            self.adicionar_log("\n--- INICIANDO ROTINA SAP ---", "ok")
            session = self.conectar_sap()
            if session is None:
                self.adicionar_log("FALHA: O SAP não está aberto ou não logado.", "err")
                falhas += len(passos_sap)
                lista_falhas.append("SAP Não Conectado")
            else:
                for passo in passos_sap:
                    if not self.executando:
                        break
                    contador += 1
                    self._set_unidade_status(
                        f"[{contador}/{total_tarefas}] SAP: Executando {passo}..."
                    )

                    try:
                        if passo == "Passo 1":
                            res = self.executar_sap_passo1(session)
                        elif passo == "Passo 2":
                            res = self.executar_sap_passo2(session)
                        elif passo == "Passo 3":
                            res = self.executar_sap_passo3(session)

                        if res:
                            sucessos += 1
                        else:
                            falhas += 1
                            lista_falhas.append(f"SAP: {passo}")
                    except Exception as e:
                        self.adicionar_log(f"Erro no {passo}: {str(e)}", "err")
                        falhas += 1
                        lista_falhas.append(f"SAP: {passo}")
                    time.sleep(1)

        pythoncom.CoUninitialize()
        self.finalizar_execucao(
            total=total_tarefas, suc=sucessos, fal=falhas, lista_fal=lista_falhas
        )

    def finalizar_execucao(self, total, suc, fal, lista_fal):
        self.executando = False
        self._set_unidade_status("Processo Finalizado.")
        if total > 0:
            agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
            self.salvar_config(ultima_att=agora_str)
            self.after(
                0,
                lambda: self.lbl_last_run.configure(
                    text=f"Última atualização: {agora_str}"
                ),
            )

        self.after(0, lambda: self.ent_user.configure(state="normal"))
        self.after(0, lambda: self.ent_pass.configure(state="normal"))
        self.after(
            0,
            lambda: self.btn_iniciar.configure(
                state="normal", text="▶   Iniciar Automação Global"
            ),
        )

        if total > 0:
            if self.auto_close:
                try:
                    if self.tray_icon:
                        msg = "Concluído" if fal == 0 else f"{fal} falha(s)"
                        self.tray_icon.notify(
                            f"{msg} — {suc}/{total} tarefas OK", "Mosaic RDE RPA"
                        )
                except Exception:
                    pass
                self.after(5000, self.destroy)
            else:
                self.after(0, lambda: self.mostrar_resumo(total, suc, fal, lista_fal))

    def mostrar_resumo(self, total, sucessos, falhas, lista_falhas):
        modal = ctk.CTkToplevel(self)
        modal.title("Resumo da Automação")
        modal.geometry("450x420")
        modal.resizable(False, False)
        modal.configure(fg_color=COR_FUNDO)
        modal.transient(self)
        modal.grab_set()

        taxa = (sucessos / total) * 100 if total > 0 else 0
        if taxa == 100:
            cor = COR_SUCCESS
            icone = "✅"
            tit = "100% CONCLUÍDO!"
            msg = "Relatórios extraídos."
        elif taxa > 0:
            cor = COR_SAP
            icone = "⚠️"
            tit = "CONCLUÍDO COM AVISOS"
            msg = "Verifique a lista de falhas."
        else:
            cor = COR_ERROR
            icone = "❌"
            tit = "FALHA CRÍTICA"
            msg = "Nenhuma etapa concluída."

        header = ctk.CTkFrame(modal, fg_color=cor, corner_radius=0, height=80)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=icone, font=("Segoe UI", 36)).pack(
            side="left", padx=(20, 10)
        )
        txt = ctk.CTkFrame(header, fg_color="transparent")
        txt.pack(side="left", pady=15)
        ctk.CTkLabel(
            txt, text=tit, font=("Segoe UI", 18, "bold"), text_color="#FFF"
        ).pack(anchor="w")
        ctk.CTkLabel(txt, text=msg, font=("Segoe UI", 12), text_color="#FFF").pack(
            anchor="w"
        )

        corpo = ctk.CTkFrame(modal, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=20, pady=20)

        stats = ctk.CTkFrame(
            corpo,
            fg_color=COR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=COR_BORDA,
        )
        stats.pack(fill="x", pady=(0, 15))
        for val, lbl, clr in [
            (sucessos, "Sucessos", COR_SUCCESS),
            (falhas, "Falhas", COR_ERROR if falhas > 0 else COR_TEXTO),
            (total, "Total", COR_TEXTO),
        ]:
            c = ctk.CTkFrame(stats, fg_color="transparent")
            c.pack(side="left", expand=True, pady=10)
            ctk.CTkLabel(
                c, text=str(val), font=("Segoe UI", 24, "bold"), text_color=clr
            ).pack()
            ctk.CTkLabel(
                c, text=lbl, font=("Segoe UI", 12), text_color=COR_MUTED
            ).pack()

        if falhas > 0:
            aviso = ctk.CTkFrame(corpo, fg_color="#2D0D0D", corner_radius=8)
            aviso.pack(fill="x", pady=(0, 15))
            ctk.CTkLabel(
                aviso,
                text="Pendências:",
                font=("Segoe UI", 10, "bold"),
                text_color=COR_ERROR,
            ).pack(anchor="w", padx=10, pady=(8, 0))
            ctk.CTkLabel(
                aviso,
                text=", ".join(lista_falhas),
                font=("Segoe UI", 11),
                text_color=COR_ERROR,
                wraplength=370,
                justify="left",
            ).pack(anchor="w", padx=10, pady=(0, 8))

        ctk.CTkButton(
            modal,
            text="Entendido 👍",
            height=40,
            fg_color=COR_TEXTO,
            hover_color="#C8C8D8",
            command=modal.destroy,
        ).pack(side="bottom", pady=0, padx=20, fill="x")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    try:
        App().mainloop()
    except Exception as e:
        print(f"Erro: {e}")
