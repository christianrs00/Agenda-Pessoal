import tkinter as tk

from interface import AgendaApp


def main():
    raiz = tk.Tk()
    AgendaApp(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()