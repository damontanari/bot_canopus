import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from bot_script import iniciar_reservas

class ReservaBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reserva Canopus Bot")
        self.root.geometry("700x520")
        self.root.resizable(False, False)

        # Estilo ttk
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 11))
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("TEntry", font=("Segoe UI", 11))
        style.configure("TProgressbar", thickness=20)

        # Frame grupos + botões
        frame_top = ttk.Frame(root, padding=10)
        frame_top.pack(fill=tk.X)

        ttk.Label(frame_top, text="Grupos (separados por vírgula):").pack(anchor=tk.W)

        entry_frame = ttk.Frame(frame_top)
        entry_frame.pack(fill=tk.X, pady=5)

        self.entry_grupos = ttk.Entry(entry_frame, font=("Segoe UI", 11))
        self.entry_grupos.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_carregar = ttk.Button(entry_frame, text="📂 Carregar arquivo", command=self.carregar_arquivo)
        btn_carregar.pack(side=tk.LEFT, padx=5)

        # Botão iniciar
        self.btn_iniciar = ttk.Button(frame_top, text="▶️ Iniciar Reservas", command=self.start_bot)
        self.btn_iniciar.pack(pady=(0,10), fill=tk.X)

        # Frame status/log
        frame_status = ttk.Frame(root, padding=(10,0))
        frame_status.pack(fill=tk.BOTH, expand=True)

        # Barra de progresso
        self.progress = ttk.Progressbar(frame_status, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0,5))

        # Log com scrolled text
        self.log_text = tk.Text(frame_status, height=20, font=("Consolas", 10), state=tk.DISABLED, bg="#1e1e1e", fg="#d4d4d4", wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Status label
        self.status_var = tk.StringVar(value="Aguardando início...")
        self.status_label = ttk.Label(root, textvariable=self.status_var, font=("Segoe UI", 10, "italic"))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=10)

    def log(self, msg):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def carregar_arquivo(self):
        tipos = [("Arquivos de texto", "*.txt"), ("CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        arquivo = filedialog.askopenfilename(title="Selecionar arquivo com grupos", filetypes=tipos)
        if not arquivo:
            return

        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                texto = f.read()
            grupos = [linha.strip() for linha in texto.replace(',', '\n').splitlines() if linha.strip()]
            self.entry_grupos.delete(0, tk.END)
            self.entry_grupos.insert(0, ", ".join(grupos))
            self.log(f"✅ Grupos carregados do arquivo: {arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar o arquivo:\n{e}")

    def start_bot(self):
        grupos_text = self.entry_grupos.get().strip()
        if not grupos_text:
            messagebox.showwarning("⚠️ Atenção", "Informe pelo menos um grupo separado por vírgula.")
            return

        grupos = [g.strip() for g in grupos_text.split(',') if g.strip()]
        if not grupos:
            messagebox.showwarning("⚠️ Atenção", "Nenhum grupo válido informado.")
            return

        self.log(f"🚀 Iniciando bot para grupos: {grupos}")
        self.status_var.set("Executando...")
        self.progress['value'] = 0
        self.btn_iniciar.config(state=tk.DISABLED)

        def update_progress(value):
            # value float 0.0 a 1.0
            self.progress['value'] = value * 100

        def run_bot():
            try:
                iniciar_reservas(grupos, self, progress_callback=update_progress)
            except Exception as e:
                self.log(f"❌ Erro geral: {e}")
            finally:
                self.status_var.set("Processo finalizado.")
                self.progress['value'] = 100
                self.btn_iniciar.config(state=tk.NORMAL)

        Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ReservaBotApp(root)
    root.mainloop()
