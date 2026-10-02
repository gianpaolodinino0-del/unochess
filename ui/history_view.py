import tkinter as tk


def format_history(cells: list[dict]) -> list[str]:
    rows: list[list] = []
    for cell in cells:
        text = " ".join(cell["tokens"])
        if cell["player"] == 0:
            rows.append([text, None])
        elif rows and rows[-1][0] is not None and rows[-1][1] is None:
            rows[-1][1] = text
        else:
            rows.append([None, text])

    lines = []
    for number, (white, black) in enumerate(rows, start=1):
        if white is None:
            lines.append(f"{number:2d}... {black}")
        elif black is None:
            lines.append(f"{number:2d}. {white}")
        else:
            # Spaziatura ridotta tra Bianco e Nero (8 caratteri invece di 14)
            lines.append(f"{number:2d}. {white:<8} {black}")
    return lines


class HistoryView(tk.Frame):
    def __init__(self, parent, width: int = 24, height: int = 22):
        super().__init__(parent)
        self.cells: list[dict] = []
        self.header = ""
        self.footer = ""

        tk.Label(self, text="Storico partita", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 4))

        body = tk.Frame(self)
        body.pack(fill="both", expand=True)

        self.text = tk.Text(
            body,
            width=width,
            height=height,
            wrap="none",
            state="disabled",
            font=("Consolas", 10),
        )
        self.text.pack(fill="both", expand=True)

    def clear(self) -> None:
        self.cells = []
        self.header = ""
        self.footer = ""
        self._render()

    def set_header(self, text: str) -> None:
        self.header = text
        self._render()

    def set_footer(self, text: str) -> None:
        self.footer = text
        self._render()

    def add_token(self, player: int, token: str) -> None:
        last = self.cells[-1] if self.cells else None
        if last is not None and not last.get("closed", False) and last["player"] == player:
            last["tokens"].append(token)
        else:
            if last is not None:
                last["closed"] = True
            self.cells.append({"player": player, "tokens": [token], "closed": False})
        self._render()

    def end_turn(self) -> None:
        if self.cells:
            self.cells[-1]["closed"] = True

    def sync_turn(self, current_player: int) -> None:
        pass

    def _render(self) -> None:
        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)

        if self.header:
            self.text.insert(tk.END, f"{self.header}\n" + "-" * 22 + "\n")

        lines = format_history(self.cells)
        for line in lines:
            self.text.insert(tk.END, f"{line}\n")

        if self.footer:
            self.text.insert(tk.END, "-" * 22 + f"\n{self.footer}\n")

        self.text.see(tk.END)
        self.text.config(state="disabled")
