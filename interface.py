from tkinter import messagebox, ttk
import tkinter as tk
import database


class AgendaApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Agenda Pessoal")
    self.root.geometry("780x620")
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
        text="Atualizar",
        command=self.atualizar_registro,
        bg="#2196F3",
        fg="white",
        font=("Arial", 10, "bold"),
        width=10,
    ).pack(side="left", padx=5)
    tk.Button(
        btn_frame,
        text="Excluir",
        command=self.excluir_registro,
        bg="#f44336",
        fg="white",
        font=("Arial", 10, "bold"),
        width=10,
    ).pack(side="left", padx=5)
    tk.Button(
        btn_frame,
        text="Limpar",
        command=self.limpar_campos,
        bg="#9e9e9e",
        fg="white",
        font=("Arial", 10, "bold"),
        width=10,
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
    tk.Button(
        filtro_frame,
        text="Filtrar",
        command=self.filtrar_data,
        font=("Arial", 9),
    ).pack(side="left", padx=5)
    tk.Button(
        filtro_frame,
        text="Mostrar Todos",
        command=self.atualizar_tabela,
        font=("Arial", 9),
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