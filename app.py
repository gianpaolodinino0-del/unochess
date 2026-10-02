import tkinter as tk
from ui.game_view import GameView


def main() -> None:
    root = tk.Tk()
    GameView(root)
    root.mainloop()


if __name__ == "__main__":
    main()
