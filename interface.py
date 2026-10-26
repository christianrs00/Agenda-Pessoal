import json
import os
import sqlite3
import threading
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime, timedelta
from math import cos, pi, sin
from tkinter import messagebox, ttk
from urllib.request import urlopen


# ---------------------------------------------------------------- banco de dados
CAMINHO_BANCO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "banco.db")


def _conectar():
    return sqlite3.connect(CAMINHO_BANCO)


def criar_tabela():
    with _conectar() as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS compromissos (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   titulo TEXT NOT NULL,
                   descricao TEXT,
                   data TEXT NOT NULL,
                   horario TEXT NOT NULL,
                   urgencia TEXT NOT NULL DEFAULT 'Média',
                   alerta_minutos INTEGER NOT NULL DEFAULT 15,
                   mensagem_alerta TEXT NOT NULL DEFAULT 'A tarefa {titulo} vence em breve!',
                   notificacao_enviada INTEGER NOT NULL DEFAULT 0
               )"""
        )
        colunas = {linha[1] for linha in con.execute(
            "PRAGMA table_info(compromissos)")}
        migracoes = {
            "urgencia": "TEXT NOT NULL DEFAULT 'Média'",
            "alerta_minutos": "INTEGER NOT NULL DEFAULT -1",
            "mensagem_alerta": "TEXT NOT NULL DEFAULT 'A tarefa {titulo} vence em breve!'",
            "notificacao_enviada": "INTEGER NOT NULL DEFAULT 0",
        }
        for coluna, definicao in migracoes.items():
            if coluna not in colunas:
                con.execute(
                    f"ALTER TABLE compromissos ADD COLUMN {coluna} {definicao}")


def inserir_compromisso(titulo, descricao, data, horario, urgencia,
                        alerta_minutos, mensagem_alerta):
    with _conectar() as con:
        con.execute(
            "INSERT INTO compromissos (titulo, descricao, data, horario, "
            "urgencia, alerta_minutos, mensagem_alerta) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (titulo, descricao, data, horario, urgencia, alerta_minutos,
             mensagem_alerta),
        )


def listar_compromissos():
    with _conectar() as con:
        return con.execute(
            "SELECT id, titulo, descricao, data, horario, urgencia, "
            "alerta_minutos, mensagem_alerta, notificacao_enviada "
            "FROM compromissos ORDER BY data, horario"
        ).fetchall()


def atualizar_compromisso(id_, titulo, descricao, data, horario, urgencia,
                          alerta_minutos, mensagem_alerta):
    with _conectar() as con:
        con.execute(
            "UPDATE compromissos SET titulo=?, descricao=?, data=?, horario=?, "
            "urgencia=?, alerta_minutos=?, mensagem_alerta=?, "
            "notificacao_enviada=0 WHERE id=?",
            (titulo, descricao, data, horario, urgencia, alerta_minutos,
             mensagem_alerta, id_),
        )


def marcar_notificacao_enviada(id_):
    with _conectar() as con:
        con.execute(
            "UPDATE compromissos SET notificacao_enviada=1 WHERE id=?", (id_,))


def excluir_compromisso(id_):
    with _conectar() as con:
        con.execute("DELETE FROM compromissos WHERE id=?", (id_,))


# ---------------------------------------------------------------- configuração
LARGURA, ALTURA = 1280, 720

CIDADE = "Itajaí"
LATITUDE, LONGITUDE = -26.9078, -48.6619

COR_FUNDO = "#0b0b0b"
COR_PAINEL_ESCURO = "#262626"
COR_BORDA = "#6a6a6a"
COR_PAINEL_CLARO = "#a3a3a3"
COR_CARTAO_ESCURO = "#555555"
COR_TEXTO = "#f2f2f2"
COR_TEXTO_SUAVE = "#b5b5b5"

FONTE = "Segoe UI"

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def clima_por_codigo(codigo):
    """Converte o weather_code do Open-Meteo em (descrição, ícone)."""
    if codigo == 0:
        return "Céu limpo", "\u2600"
    if codigo in (1, 2):
        return "Parcialmente nublado", "\u26C5"
    if codigo in (3, 45, 48):
        return "Nublado", "\u2601"
    if 51 <= codigo <= 67 or 80 <= codigo <= 82:
        return "Chuva", "\u2602"
    if 71 <= codigo <= 77:
        return "Neve", "\u2744"
    if codigo >= 95:
        return "Tempestade", "\u26A1"
    return "Nublado", "\u2601"


def retangulo_arredondado(canvas, x1, y1, x2, y2, raio, **kw):
    pontos = [
        x1 + raio, y1, x2 - raio, y1, x2, y1, x2, y1 + raio,
        x2, y2 - raio, x2, y2, x2 - raio, y2, x1 + raio, y2,
        x1, y2, x1, y2 - raio, x1, y1 + raio, x1, y1,
    ]
    return canvas.create_polygon(pontos, smooth=True, **kw)


def para_datetime(data, horario):
    try:
        return datetime.strptime(f"{data} {horario}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None


# ---------------------------------------------------------------- botão
class BotaoArredondado(tk.Canvas):
    def __init__(self, parent, text, command, color, hover_color,
                 text_color="white"):
        font = (FONTE, 10, "bold")
        medida = tkfont.Font(parent, font=font)
        width = max(104, medida.measure(text) + 36)
        height = 40
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg"), highlightthickness=0,
                         takefocus=True, cursor="hand2")
        self.command = command
        self.color = color
        self.hover_color = hover_color
        self.shape = retangulo_arredondado(
            self, 1, 1, width - 1, height - 1, 12, fill=color, outline=color)
        self.create_text(width / 2, height / 2, text=text, font=font,
                         fill=text_color)
        self.bind("<Enter>", lambda e: self.itemconfigure(
            self.shape, fill=self.hover_color, outline=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfigure(
            self.shape, fill=self.color, outline=self.color))
        self.bind("<Button-1>", self._clique)
        self.bind("<Return>", lambda e: self.command())
        self.bind("<space>", lambda e: self.command())

    def _clique(self, event):
        self.focus_set()
        self.command()


# ---------------------------------------------------------------- diálogo
class DialogoTarefa(tk.Toplevel):
    """Janela para criar / editar / excluir um compromisso."""

    def __init__(self, app, registro=None):
        super().__init__(app.root)
        self.app = app
        self.registro = registro
        self.title("Editar tarefa" if registro else "Nova tarefa")
        self.configure(bg=COR_PAINEL_ESCURO, padx=24, pady=20)
        self.resizable(False, False)
        self.transient(app.root)

        campos = [("Título *", 40), ("Descrição", 40),
                  ("Data (AAAA-MM-DD) *", 16), ("Horário (HH:MM) *", 16)]
        self.entradas = []
        for i, (rotulo, largura) in enumerate(campos):
            tk.Label(self, text=rotulo, font=(FONTE, 10), bg=COR_PAINEL_ESCURO,
                     fg=COR_TEXTO).grid(row=i, column=0, sticky="w", pady=6)
            entrada = tk.Entry(self, font=(FONTE, 10), width=largura,
                               bg=COR_CARTAO_ESCURO, fg="white",
                               insertbackground="white", relief="flat")
            entrada.grid(row=i, column=1, sticky="w", padx=(12, 0), pady=6,
                         ipady=4)
            self.entradas.append(entrada)
        (self.e_titulo, self.e_desc, self.e_data, self.e_hora) = self.entradas

        tk.Label(self, text="Urgência", font=(FONTE, 10),
                 bg=COR_PAINEL_ESCURO, fg=COR_TEXTO).grid(
                     row=4, column=0, sticky="w", pady=6)
        self.var_urgencia = tk.StringVar(value="Média")
        self.combo_urgencia = ttk.Combobox(
            self, textvariable=self.var_urgencia,
            values=("Baixa", "Média", "Alta"), state="readonly", width=17)
        self.combo_urgencia.grid(row=4, column=1, sticky="w", padx=(12, 0),
                                 pady=6)

        tk.Label(self, text="Antecedência (minutos)", font=(FONTE, 10),
                 bg=COR_PAINEL_ESCURO, fg=COR_TEXTO).grid(
                     row=5, column=0, sticky="w", pady=6)
        self.e_antecedencia = tk.Spinbox(
            self, from_=0, to=10080, increment=5, width=18,
            font=(FONTE, 10), bg=COR_CARTAO_ESCURO, fg="white",
            insertbackground="white", relief="flat")
        self.e_antecedencia.grid(row=5, column=1, sticky="w", padx=(12, 0),
                                 pady=6, ipady=4)

        self.var_alerta_ativo = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self, text="Ativar notificação", variable=self.var_alerta_ativo,
            font=(FONTE, 9), bg=COR_PAINEL_ESCURO, fg=COR_TEXTO,
            activebackground=COR_PAINEL_ESCURO, activeforeground=COR_TEXTO,
            selectcolor=COR_CARTAO_ESCURO, relief="flat").grid(
                row=6, column=1, sticky="w", padx=(8, 0), pady=2)

        tk.Label(self, text="Mensagem personalizada", font=(FONTE, 10),
                 bg=COR_PAINEL_ESCURO, fg=COR_TEXTO).grid(
                     row=7, column=0, sticky="w", pady=6)
        self.e_mensagem = tk.Entry(
            self, font=(FONTE, 10), width=40, bg=COR_CARTAO_ESCURO,
            fg="white", insertbackground="white", relief="flat")
        self.e_mensagem.grid(row=7, column=1, sticky="w", padx=(12, 0),
                             pady=6, ipady=4)
        tk.Label(
            self, text="Tokens: {titulo}, {data}, {horario}, {urgencia}",
            font=(FONTE, 8), bg=COR_PAINEL_ESCURO, fg=COR_TEXTO_SUAVE).grid(
                row=8, column=1, sticky="w", padx=(12, 0))

        if registro:
            _, titulo, desc, data, hora, *extras = registro
            self.e_titulo.insert(0, titulo)
            self.e_desc.insert(0, desc or "")
            self.e_data.insert(0, data)
            self.e_hora.insert(0, hora)
            urgencia = extras[0] if len(extras) > 0 else "Média"
            alerta_minutos = extras[1] if len(extras) > 1 else -1
            mensagem_alerta = (extras[2] if len(extras) > 2 else
                               "A tarefa {titulo} vence em breve!")
            self.var_urgencia.set(urgencia)
            self.var_alerta_ativo.set(alerta_minutos >= 0)
            if alerta_minutos >= 0:
                self.e_antecedencia.delete(0, tk.END)
                self.e_antecedencia.insert(0, str(alerta_minutos))
            self.e_mensagem.insert(0, mensagem_alerta)
        else:
            agora = datetime.now()
            self.e_data.insert(0, agora.strftime("%Y-%m-%d"))
            self.e_hora.insert(0, agora.strftime("%H:%M"))
            self.e_antecedencia.delete(0, tk.END)
            self.e_antecedencia.insert(0, "15")
            self.e_mensagem.insert(0, "A tarefa {titulo} vence em breve!")

        botoes = tk.Frame(self, bg=COR_PAINEL_ESCURO)
        botoes.grid(row=9, column=0, columnspan=2, pady=(16, 0))
        BotaoArredondado(botoes, "Salvar", self.salvar,
                         "#3F9B5A", "#33814A").pack(side="left", padx=4)
        if registro:
            BotaoArredondado(botoes, "Excluir", self.excluir,
                             "#D94F52", "#BC3F43").pack(side="left", padx=4)
        BotaoArredondado(botoes, "Cancelar", self.destroy,
                         "#697586", "#536170").pack(side="left", padx=4)

        self.update_idletasks()
        x = app.root.winfo_x() + (LARGURA - self.winfo_width()) // 2
        y = app.root.winfo_y() + (ALTURA - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        self.grab_set()
        self.e_titulo.focus_set()

    def _ler(self):
        titulo = self.e_titulo.get().strip()
        desc = self.e_desc.get().strip()
        data = self.e_data.get().strip()
        hora = self.e_hora.get().strip()
        if not titulo or not data or not hora:
            messagebox.showerror(
                "Erro", "Os campos Título, Data e Horário são obrigatórios!",
                parent=self)
            return None
        if para_datetime(data, hora) is None:
            messagebox.showerror(
                "Erro", "Data ou horário inválido.\nUse AAAA-MM-DD e HH:MM.",
                parent=self)
            return None
        try:
            minutos = int(self.e_antecedencia.get())
        except ValueError:
            messagebox.showerror(
                "Erro", "A antecedência deve ser um número de minutos.",
                parent=self)
            return None
        if not 0 <= minutos <= 10080:
            messagebox.showerror(
                "Erro", "A antecedência deve estar entre 0 e 10080 minutos.",
                parent=self)
            return None
        mensagem = self.e_mensagem.get().strip()
        if len(mensagem) > 250:
            messagebox.showerror(
                "Erro", "A mensagem deve ter no máximo 250 caracteres.",
                parent=self)
            return None
        return (titulo, desc, data, hora, self.var_urgencia.get(),
                minutos if self.var_alerta_ativo.get() else -1,
                mensagem or "A tarefa {titulo} vence em breve!")

    def salvar(self):
        dados = self._ler()
        if not dados:
            return
        try:
            if self.registro:
                atualizar_compromisso(self.registro[0], *dados)
            else:
                inserir_compromisso(*dados)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar: {e}",
                                 parent=self)
            return
        self.app.atualizar_tudo()
        self.destroy()

    def excluir(self):
        if not messagebox.askyesno(
                "Confirmação", "Tem certeza de que deseja excluir esta tarefa?",
                parent=self):
            return
        try:
            excluir_compromisso(self.registro[0])
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao excluir: {e}",
                                 parent=self)
            return
        self.app.atualizar_tudo()
        self.destroy()


# ---------------------------------------------------------------- app
class AgendaApp:
    PLACEHOLDER = "Pesquisar tarefa"

    def __init__(self, root):
        self.root = root
        self.root.title("Agenda Pessoal")
        self.root.geometry(f"{LARGURA}x{ALTURA}")
        self.root.resizable(False, False)
        self.root.config(bg=COR_FUNDO)

        criar_tabela()

        self.clima = None
        self.cidade = CIDADE
        self.latitude = LATITUDE
        self.longitude = LONGITUDE
        self.canvas = tk.Canvas(root, width=LARGURA, height=ALTURA,
                                bg=COR_FUNDO, highlightthickness=0)
        self.canvas.pack()

        self.desenhar_fundo()
        self.desenhar_estrutura()
        self.criar_busca()

        self.atualizar_tudo()
        self.atualizar_relogio()
        self.iniciar_clima()
        self.root.after(1000, self.verificar_notificacoes)

    # ------------------------------------------------------------ estrutura
    def desenhar_fundo(self):
        c = self.canvas
        for y in range(ALTURA):
            t = y / ALTURA
            tom = int(30 - 24 * t)
            c.create_line(0, y, LARGURA, y, fill=f"#{tom:02x}{tom:02x}{tom:02x}")

    def desenhar_estrutura(self):
        c = self.canvas
        escuro = dict(fill=COR_PAINEL_ESCURO, outline=COR_BORDA, width=1.5)
        claro = dict(fill=COR_PAINEL_CLARO, outline=COR_PAINEL_CLARO)

        # Relógio e calendário compactos no topo esquerdo
        retangulo_arredondado(c, 66, 28, 430, 190, 24, **claro)
        # Clima compacto no topo direito
        retangulo_arredondado(c, 830, 28, 1214, 166, 24, **escuro)
        # Busca e tarefas recentes no topo direito
        retangulo_arredondado(c, 830, 178, 1214, 298, 22, **claro)
        retangulo_arredondado(c, 844, 190, 1200, 222, 14,
                              fill=COR_CARTAO_ESCURO, outline=COR_CARTAO_ESCURO)
        c.create_oval(857, 198, 871, 212, outline="white", width=2)
        c.create_line(869, 210, 877, 218, fill="white", width=2)
        # Tarefas urgentes no centro, ocupando quase toda a largura
        retangulo_arredondado(c, 66, 320, 1214, 532, 26, **escuro)
        c.create_text(640, 345, text="Tarefas urgentes", fill=COR_TEXTO_SUAVE,
                      font=(FONTE, 15))
        # Longo prazo na faixa inferior
        retangulo_arredondado(c, 66, 552, 1214, 707, 24, **escuro)
        c.create_text(640, 576, text="Tarefas a longo prazo",
                      fill=COR_TEXTO_SUAVE, font=(FONTE, 15))

        # Botão "+ Nova tarefa" (a pílula do mockup)
        self.btn_nova = retangulo_arredondado(
            c, 562, 265, 692, 295, 14, fill="#333333", outline="#333333",
            tags="btn_nova")
        c.create_text(627, 280, text="+ Nova tarefa", fill="white",
                      font=(FONTE, 10, "bold"), tags="btn_nova")
        c.tag_bind("btn_nova", "<Button-1>", lambda e: DialogoTarefa(self))
        c.tag_bind("btn_nova", "<Enter>",
                   lambda e: (c.itemconfigure(self.btn_nova, fill="#4a4a4a"),
                              c.config(cursor="hand2")))
        c.tag_bind("btn_nova", "<Leave>",
                   lambda e: (c.itemconfigure(self.btn_nova, fill="#333333"),
                              c.config(cursor="")))

    def criar_busca(self):
        self.entry_busca = tk.Entry(
            self.canvas, font=(FONTE, 10), bg=COR_CARTAO_ESCURO,
            fg=COR_TEXTO_SUAVE, insertbackground="white", relief="flat",
            highlightthickness=0, width=31)
        self.entry_busca.insert(0, self.PLACEHOLDER)
        self.entry_busca.bind("<FocusIn>", self._busca_foco)
        self.entry_busca.bind("<FocusOut>", self._busca_sem_foco)
        self.entry_busca.bind("<KeyRelease>", lambda e: self.desenhar_recentes())
        self.canvas.create_window(882, 206, window=self.entry_busca, anchor="w")

    def _busca_foco(self, _):
        if self.entry_busca.get() == self.PLACEHOLDER:
            self.entry_busca.delete(0, tk.END)
            self.entry_busca.config(fg="white")

    def _busca_sem_foco(self, _):
        if not self.entry_busca.get().strip():
            self.entry_busca.delete(0, tk.END)
            self.entry_busca.insert(0, self.PLACEHOLDER)
            self.entry_busca.config(fg=COR_TEXTO_SUAVE)

    # ------------------------------------------------------------ cartões
    def cartao(self, x1, y1, x2, y2, registro, fundo, cor_texto, tag,
               grupo="dyn"):
        c = self.canvas
        _, titulo, _, data, hora = registro[:5]
        urgencia = registro[5] if len(registro) > 5 else "Média"
        max_titulo = max(18, int((x2 - x1) / 8))
        if len(titulo) > max_titulo:
            titulo = titulo[:max_titulo - 2] + "…"
        dt = para_datetime(data, hora)
        sub = dt.strftime("%d/%m %H:%M") if dt else f"{data} {hora}"
        tags = ("dyn", grupo, tag)
        forma = retangulo_arredondado(c, x1, y1, x2, y2, 16, fill=fundo,
                                      outline=fundo, tags=tags)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        cor_urgencia = {"Alta": "#c94747", "Média": "#c48a32",
                "Baixa": "#3d9b73"}.get(urgencia, "#c48a32")
        c.create_oval(x1 + 9, y1 + 8, x1 + 17, y1 + 16,
                  fill=cor_urgencia, outline=cor_urgencia, tags=tags)
        c.create_text(x1 + 22, y1 + 12, text=urgencia, anchor="w",
                  fill=cor_texto, tags=tags, font=(FONTE, 8, "bold"))
        fonte_cartao = 10 if x2 - x1 < 150 else 11
        c.create_text(cx, cy - 5, text=titulo, fill=cor_texto, tags=tags,
                  font=(FONTE, fonte_cartao, "bold"), width=x2 - x1 - 14,
                      justify="center")
        c.create_text(cx, y2 - 16, text=sub, fill=cor_texto, tags=tags,
                      font=(FONTE, 9))
        c.tag_bind(tag, "<Button-1>",
                   lambda e, r=registro: DialogoTarefa(self, r))
        c.tag_bind(tag, "<Enter>", lambda e: c.config(cursor="hand2"))
        c.tag_bind(tag, "<Leave>", lambda e: c.config(cursor=""))

    def vazio(self, x, y, texto, grupo="dyn"):
        self.canvas.create_text(x, y, text=texto, fill=COR_TEXTO_SUAVE,
                                font=(FONTE, 11), tags=("dyn", grupo))

    # ------------------------------------------------------------ dados
    def atualizar_tudo(self):
        self.registros = list(listar_compromissos())
        self.canvas.delete("dyn")
        self.desenhar_recentes()
        self.desenhar_urgentes_e_longo()
        self.desenhar_clima()

    def desenhar_recentes(self):
        c = self.canvas
        c.delete("recentes")
        consulta = self.entry_busca.get().strip().lower()
        if consulta == self.PLACEHOLDER.lower():
            consulta = ""

        if consulta:
            lista = [r for r in self.registros
                     if consulta in str(r[1]).lower()
                     or consulta in str(r[2] or "").lower()]
        else:
            lista = sorted(self.registros, key=lambda r: r[0], reverse=True)

        xs = (850, 966, 1082)
        for i, reg in enumerate(lista[:3]):
            self.cartao(xs[i], 231, xs[i] + 106, 286, reg, COR_CARTAO_ESCURO,
                        "white", f"rec_{reg[0]}", grupo="recentes")
        if not lista:
            texto = "Nada encontrado" if consulta else "Sem tarefas ainda"
            self.vazio(1022, 260, texto, grupo="recentes")

    def desenhar_urgentes_e_longo(self):
        agora = datetime.now()
        limite = agora + timedelta(days=2)
        futuros = []
        for r in self.registros:
            dt = para_datetime(r[3], r[4])
            if dt and dt >= agora - timedelta(hours=1):
                futuros.append((dt, r))
        futuros.sort(key=lambda t: t[0])

        prioridade = {"Alta": 0, "Média": 1, "Baixa": 2}
        urgentes = [(dt, r) for dt, r in futuros
                    if r[5] == "Alta" or dt <= limite]
        urgentes.sort(key=lambda item: (
            prioridade.get(item[1][5], 1), item[0]))
        urgentes = [r for _, r in urgentes[:4]]
        longo = [(dt, r) for dt, r in futuros
                 if dt > limite and r[5] != "Alta"]
        longo.sort(key=lambda item: (
            prioridade.get(item[1][5], 1), item[0]))
        longo = [r for _, r in longo[:5]]

        xs_urgentes = (90, 370, 650, 930)
        for x, reg in zip(xs_urgentes, urgentes):
            self.cartao(x, 370, x + 260, 504, reg, COR_PAINEL_CLARO, "#111111",
                        f"urg_{reg[0]}")
        if not urgentes:
            self.vazio(640, 425, "Nenhuma tarefa urgente")

        for i, reg in enumerate(longo):
            x = 83 + i * 220
            self.cartao(x, 612, x + 190, 692, reg, COR_PAINEL_CLARO, "#111111",
                        f"lon_{reg[0]}")
        if not longo:
            self.vazio(640, 657, "Nenhuma tarefa a longo prazo")

    # ------------------------------------------------------------ relógio
    def atualizar_relogio(self):
        c = self.canvas
        agora = datetime.now()
        c.delete("relogio")
        fonte_num = (FONTE, 38)
        c.create_text(226, 99, text=agora.strftime("%H"), fill="white",
                      font=fonte_num, tags="relogio")
        c.create_text(293, 99, text=agora.strftime("%M"), fill="white",
                      font=fonte_num, tags="relogio")
        c.create_text(112, 86, text=str(agora.day), fill="white", anchor="w",
                  font=(FONTE, 30), tags="relogio")
        c.create_text(113, 122, anchor="w", fill="white", tags="relogio",
                      text=f"{MESES[agora.month - 1]}, {agora.year}",
                  font=(FONTE, 10))
        c.create_text(113, 147, anchor="w", fill="white", tags="relogio",
                  text=DIAS[agora.weekday()], font=(FONTE, 10))
        c.create_text(356, 99, text=agora.strftime("%S"), fill=COR_TEXTO_SUAVE,
                  font=(FONTE, 20), tags="relogio")
        c.create_text(260, 99, text=":", fill=COR_TEXTO_SUAVE,
                  font=(FONTE, 25), tags="relogio")
        c.create_text(329, 99, text=":", fill=COR_TEXTO_SUAVE,
                  font=(FONTE, 25), tags="relogio")
        # reavalia urgentes quando o minuto muda
        if agora.second == 0:
            self.atualizar_tudo()
        self.root.after(1000, self.atualizar_relogio)

    def verificar_notificacoes(self):
        agora = datetime.now()
        tolerancia = timedelta(seconds=60)
        for registro in self.registros:
            if len(registro) > 8 and registro[8]:
                continue
            minutos = registro[6] if len(registro) > 6 else -1
            if minutos < 0:
                continue
            prazo = para_datetime(registro[3], registro[4])
            if prazo is None:
                continue
            horario_alerta = prazo - timedelta(minutes=minutos)
            if horario_alerta <= agora <= prazo + tolerancia:
                marcar_notificacao_enviada(registro[0])
                self.registros = [
                    tarefa[:8] + (1,) if tarefa[0] == registro[0] else tarefa
                    for tarefa in self.registros
                ]
                mensagem = registro[7] if len(registro) > 7 else ""
                valores = {
                    "titulo": registro[1],
                    "data": registro[3],
                    "horario": registro[4],
                    "urgencia": registro[5] if len(registro) > 5 else "Média",
                }
                for chave, valor in valores.items():
                    mensagem = mensagem.replace("{" + chave + "}", str(valor))
                if not mensagem.strip():
                    mensagem = f"O prazo de {registro[1]} está chegando."
                messagebox.showinfo(
                    f"Lembrete: {valores['urgencia']}", mensagem,
                    parent=self.root)
        self.root.after(30_000, self.verificar_notificacoes)

    # ------------------------------------------------------------ clima
    def iniciar_clima(self):
        threading.Thread(target=self._buscar_clima, daemon=True).start()
        self.root.after(30 * 60 * 1000, self.iniciar_clima)

    def _buscar_clima(self):
        try:
            with urlopen("https://ipapi.co/json/", timeout=6) as resp:
                local = json.load(resp)
            self.cidade = local.get("city") or CIDADE
            self.latitude = float(local.get("latitude", LATITUDE))
            self.longitude = float(local.get("longitude", LONGITUDE))
        except Exception:
            self.cidade = CIDADE
            self.latitude, self.longitude = LATITUDE, LONGITUDE
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={self.latitude}&longitude={self.longitude}"
            "&current=temperature_2m,weather_code"
            "&hourly=temperature_2m,weather_code"
            "&timezone=auto&forecast_days=2"
        )
        try:
            with urlopen(url, timeout=10) as resp:
                dados = json.load(resp)
            atual = dados["current"]
            horas = dados["hourly"]
            idx = horas["time"].index(atual["time"][:13] + ":00")
            previsao = []
            for passo in (1, 3, 5, 7, 9):
                i = idx + passo
                previsao.append((
                    horas["time"][i][11:13] + "h",
                    horas["temperature_2m"][i],
                    horas["weather_code"][i],
                ))
            self.clima = {
                "temp": atual["temperature_2m"],
                "codigo": atual["weather_code"],
                "previsao": previsao,
            }
        except Exception:
            return  # sem internet: mantém o último dado (ou "--")
        self.root.after(0, self.desenhar_clima)

    def desenhar_clima(self):
        c = self.canvas
        c.delete("clima")
        c.create_text(850, 49, anchor="w", fill=COR_TEXTO, tags="clima",
                      text=f"{self.cidade}  \u27A4", font=(FONTE, 11, "bold"))
        if not self.clima:
            c.create_text(850, 102, anchor="w", text="--°", fill="white",
                          font=(FONTE, 34), tags="clima")
            c.create_text(1190, 110, anchor="e", text="Sem conexão",
                          fill=COR_TEXTO_SUAVE, font=(FONTE, 10), tags="clima")
            return
        desc, icone = clima_por_codigo(self.clima["codigo"])
        c.create_text(850, 105, anchor="w", fill="white", tags="clima",
                      text=f"{round(self.clima['temp'])}°", font=(FONTE, 34))
        c.create_text(1179, 77, anchor="e", text=icone, fill="white",
                      font=("Segoe UI Symbol", 20), tags="clima")
        c.create_text(1180, 110, anchor="e", text=desc, fill="white",
                      font=(FONTE, 10), tags="clima")
        for i, (hora, temp, codigo) in enumerate(self.clima["previsao"]):
            x = 872 + i * 65
            c.create_text(x, 128, text=hora, fill=COR_TEXTO, tags="clima",
                          font=(FONTE, 8))
            c.create_text(x, 144, text=clima_por_codigo(codigo)[1],
                          fill="white", font=("Segoe UI Symbol", 12),
                          tags="clima")
            c.create_text(x, 160, text=f"{round(temp)}°", fill=COR_TEXTO,
                          tags="clima", font=(FONTE, 8))
