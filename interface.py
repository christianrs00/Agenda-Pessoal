from tkinter import messagebox, ttk
import tkinter as tk
import tkinter.font as tkfont
from math import cos, pi, sin
import database


class BotaoArredondado(tk.Canvas):
  def __init__(self, parent, text, command, color, hover_color, text_color="white"):
    font = ("Arial", 10, "bold")
    self.font = tkfont.Font(parent, font=font)
    width = max(104, self.font.measure(text) + 36)
    height = 40
    super().__init__(
        parent,
        width=width,
        height=height,
        bg=parent.cget("bg"),
        highlightthickness=0,
        takefocus=True,
        cursor="hand2",
    )
    self.command = command
    self.color = color
    self.hover_color = hover_color
    self.shape = self.create_polygon(
        self._rounded_rectangle(width, height, 12),
        smooth=True,
        splinesteps=24,
        fill=color,
        outline=color,
    )
    self.create_text(
        width / 2,
        height / 2,
        text=text,
        font=font,
        fill=text_color,
    )
    self.bind("<Enter>", self._on_enter)
    self.bind("<Leave>", self._on_leave)
    self.bind("<Button-1>", self._on_click)
    self.bind("<Return>", self._on_activate)
    self.bind("<space>", self._on_activate)

  @staticmethod
  def _rounded_rectangle(width, height, radius):
    points = []
    for center_x, center_y, start_angle in (
        (width - radius, radius, -pi / 2),
        (width - radius, height - radius, 0),
        (radius, height - radius, pi / 2),
        (radius, radius, pi),
    ):
      for step in range(7):
        angle = start_angle + step * pi / 12
        points.extend(
            (center_x + radius * cos(angle), center_y + radius * sin(angle))
        )
    return points

  def _on_enter(self, event):
    self.itemconfigure(self.shape, fill=self.hover_color, outline=self.hover_color)

  def _on_leave(self, event):
    self.itemconfigure(self.shape, fill=self.color, outline=self.color)

  def _on_click(self, event):
    self.focus_set()
    self.command()

  def _on_activate(self, event):
    self.command()


class AgendaApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Agenda Pessoal")
    self.root.geometry("600x600")
    self.root.config(bg="#f0f2f5")

    # Garantir que a tabela existe
    database.criar_tabela()

    self.id_selecionado = None

    self.criar_widgets()
    self.atualizar_tabela()

  def criar_widgets(self):
    # Título principal
    titulo_label = tk.Label(
        self.root,
        text="Agenda Pessoal",
        font=("Arial", 18, "bold"),
        bg="#f0f2f5",
        fg="#333333",
    )
    titulo_label.pack(pady=10)

    # Frame do Formulário
    form_frame = tk.LabelFrame(
        self.root,
        text=" Novo / Editar Compromisso ",
        font=("Arial", 11, "bold"),
        bg="#f0f2f5",
        padx=15,
        pady=15,
    )
    form_frame.pack(fill="x", padx=20, pady=10)

    # Campos
    tk.Label(
        form_frame, text="Título *:", font=("Arial", 10), bg="#f0f2f5"
    ).grid(row=0, column=0, sticky="w", pady=5)
    self.entry_titulo = tk.Entry(form_frame, font=("Arial", 10), width=45)
    self.entry_titulo.grid(row=0, column=1, sticky="w", pady=5, padx=5)

    tk.Label(
        form_frame, text="Descrição:", font=("Arial", 10), bg="#f0f2f5"
    ).grid(row=1, column=0, sticky="w", pady=5)
    self.entry_descricao = tk.Entry(form_frame, font=("Arial", 10), width=45)
    self.entry_descricao.grid(row=1, column=1, sticky="w", pady=5, padx=5)

    tk.Label(
        form_frame,
        text="Data (AAAA-MM-DD) *:",
        font=("Arial", 10),
        bg="#f0f2f5",
    ).grid(row=2, column=0, sticky="w", pady=5)
    self.entry_data = tk.Entry(form_frame, font=("Arial", 10), width=15)
    self.entry_data.grid(row=2, column=1, sticky="w", pady=5, padx=5)

    tk.Label(
        form_frame,
        text="Horário (HH:MM) *:",
        font=("Arial", 10),
        bg="#f0f2f5",
    ).grid(row=3, column=0, sticky="w", pady=5)
    self.entry_horario = tk.Entry(form_frame, font=("Arial", 10), width=15)
    self.entry_horario.grid(row=3, column=1, sticky="w", pady=5, padx=5)

    # Botões de Ação
    btn_frame = tk.Frame(form_frame, bg="#f0f2f5")
    btn_frame.grid(row=4, column=0, columnspan=2, pady=15)

    tk.Button(
        btn_frame,
        text="Salvar",
        command=self.salvar_compromisso,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 10, "bold"),
        width=10,
    ).pack(side="left", padx=5)
    tk.Button(
        btn_frame,
      "Atualizar",
      self.atualizar_registro,
      "#3977C5",
      "#2D64AA",
    ).pack(side="left", padx=5)
    BotaoArredondado(
        btn_frame,
      "Excluir",
      self.excluir_registro,
      "#D94F52",
      "#BC3F43",
    ).pack(side="left", padx=5)
    BotaoArredondado(
        btn_frame,
      "Limpar",
      self.limpar_campos,
      "#697586",
      "#536170",
    ).pack(side="left", padx=5)

    # Frame de Listagem e Filtro
    lista_frame = tk.LabelFrame(
        self.root,
        text=" Compromissos Cadastrados ",
        font=("Arial", 11, "bold"),
        bg="#f0f2f5",
        padx=15,
        pady=15,
    )
    lista_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # Barra de Filtro
    filtro_frame = tk.Frame(lista_frame, bg="#f0f2f5")
    filtro_frame.pack(fill="x", pady=5)

    tk.Label(
        filtro_frame,
        text="Filtrar Data (AAAA-MM-DD):",
        font=("Arial", 9),
        bg="#f0f2f5",
    ).pack(side="left", padx=5)
    self.entry_filtro = tk.Entry(filtro_frame, font=("Arial", 9), width=15)
    self.entry_filtro.pack(side="left", padx=5)
    BotaoArredondado(
        filtro_frame,
      "Filtrar",
      self.filtrar_data,
      "#168A72",
      "#11745F",
    ).pack(side="left", padx=5)
    BotaoArredondado(
        filtro_frame,
      "Mostrar Todos",
      self.atualizar_tabela,
      "#697586",
      "#536170",
    ).pack(side="left", padx=5)

    # Tabela (Treeview)
    colunas = ("ID", "Título", "Descrição", "Data", "Horário")
    self.tree = ttk.Treeview(
        lista_frame, columns=colunas, show="headings", height=7
    )

    for col in colunas:
      self.tree.heading(col, text=col)
      if col == "ID":
        self.tree.column(col, width=40, anchor="center")
      elif col in ("Data", "Horário"):
        self.tree.column(col, width=90, anchor="center")
      else:
        self.tree.column(col, width=190, anchor="w")

    scrollbar = ttk.Scrollbar(
        lista_frame, orient="vertical", command=self.tree.yview
    )
    self.tree.configure(yscrollcommand=scrollbar.set)

    self.tree.pack(side="left", fill="both", expand=True, pady=5)
    scrollbar.pack(side="right", fill="y", pady=5)

    self.tree.bind("<<TreeviewSelect>>", self.preencher_formulario)

  def salvar_compromisso(self):
    titulo = self.entry_titulo.get().strip()
    descricao = self.entry_descricao.get().strip()
    data = self.entry_data.get().strip()
    horario = self.entry_horario.get().strip()

    if not titulo or not data or not horario:
      messagebox.showerror(
          "Erro", "Os campos Título, Data e Horário são obrigatórios!"
      )
      return

    try:
      database.inserir_compromisso(titulo, descricao, data, horario)
      messagebox.showinfo("Sucesso", "Compromisso cadastrado com sucesso!")
      self.limpar_campos()
      self.atualizar_tabela()
    except Exception as e:
      messagebox.showerror("Erro", f"Ocorreu um erro ao salvar: {e}")

  def atualizar_tabela(self):
    for item in self.tree.get_children():
      self.tree.delete(item)
    for linha in database.listar_compromissos():
      self.tree.insert("", "end", values=linha)

  def preencher_formulario(self, event):
    selecionado = self.tree.selection()
    if selecionado:
      item = self.tree.item(selecionado)
      valores = item["values"]
      self.id_selecionado = valores[0]

      self.entry_titulo.delete(0, tk.END)
      self.entry_titulo.insert(0, valores[1])

      self.entry_descricao.delete(0, tk.END)
      self.entry_descricao.insert(0, valores[2] if valores[2] else "")

      self.entry_data.delete(0, tk.END)
      self.entry_data.insert(0, valores[3])

      self.entry_horario.delete(0, tk.END)
      self.entry_horario.insert(0, valores[4])

  def atualizar_registro(self):
    if not self.id_selecionado:
      messagebox.showwarning(
          "Aviso", "Selecione um compromisso na tabela para atualizar!"
      )
      return

    titulo = self.entry_titulo.get().strip()
    descricao = self.entry_descricao.get().strip()
    data = self.entry_data.get().strip()
    horario = self.entry_horario.get().strip()

    if not titulo or not data or not horario:
      messagebox.showerror(
          "Erro", "Os campos Título, Data e Horário são obrigatórios!"
      )
      return

    try:
      database.atualizar_compromisso(
          self.id_selecionado, titulo, descricao, data, horario
      )
      messagebox.showinfo("Sucesso", "Compromisso atualizado com sucesso!")
      self.limpar_campos()
      self.atualizar_tabela()
    except Exception as e:
      messagebox.showerror("Erro", f"Ocorreu um erro ao atualizar: {e}")

  def excluir_registro(self):
    if not self.id_selecionado:
      messagebox.showwarning(
          "Aviso", "Selecione um compromisso na tabela para excluir!"
      )
      return

    resposta = messagebox.askyesno(
        "Confirmação", "Tem certeza de que pretende eliminar este compromisso?"
    )
    if resposta:
      try:
        database.excluir_compromisso(self.id_selecionado)
        messagebox.showinfo("Sucesso", "Compromisso excluído com sucesso!")
        self.limpar_campos()
        self.atualizar_tabela()
      except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao excluir: {e}")

  def filtrar_data(self):
    data = self.entry_filtro.get().strip()
    if not data:
      messagebox.showwarning("Aviso", "Introduza uma data para filtrar!")
      return

    for item in self.tree.get_children():
      self.tree.delete(item)

    dados = database.consultar_por_data(data)
    for linha in dados:
      self.tree.insert("", "end", values=linha)

  def limpar_campos(self):
    self.entry_titulo.delete(0, tk.END)
    self.entry_descricao.delete(0, tk.END)
    self.entry_data.delete(0, tk.END)
    self.entry_horario.delete(0, tk.END)
    self.id_selecionado = None
    if self.tree.selection():
      self.tree.selection_remove(self.tree.selection())