import tkinter as tk
from math import ceil
from game.cards import Card
from game.card_images import card_image_path


CARD_W, CARD_H = 64, 96
MAX_COLUMNS = 14

COLOR_FILL = {
    "red": "#d72600",
    "yellow": "#ecb800",
    "green": "#379711",
    "blue": "#0063b3",
}

COLOR_TEXT = {
    "red": "#d72600",
    "yellow": "#b38600",
    "green": "#379711",
    "blue": "#0063b3",
}

WILD_FILL = "#222222"

COLOR_ORDER = {"red": 0, "yellow": 1, "green": 2, "blue": 3}
SPECIAL_RANK = {"+2": 9, "stop": 10, "wild": 11, "+4": 12}
DISPLAY_TEXT = {"stop": "STOP", "wild": "WILD"}


def _rank_key(card: Card) -> int:
    value = str(card.value)

    if value.isdigit():
        return int(value)

    return SPECIAL_RANK.get(value, 99)


def _color_key(card: Card) -> int:
    return COLOR_ORDER.get(card.color, len(COLOR_ORDER))


class CardWidget(tk.Canvas):
    _image_cache: dict[tuple[str, int, int], tk.PhotoImage] = {}
    def __init__(
        self,
        parent,
        card: Card,
        on_click=None,
        scale: float = 1.0,
    ):
        self.k = scale
        self.w = max(1, int(CARD_W * scale))
        self.h = max(1, int(CARD_H * scale))

        super().__init__(
            parent,
            width=self.w,
            height=self.h,
            highlightthickness=0,
            bg=parent.cget("bg"),
            cursor="hand2" if on_click else "",
        )

        self.card = card
        self.image = self._load_image(card, self.w, self.h)
        if self.image is not None:
            self.create_image(0, 0, image=self.image, anchor="nw")
        else:
            self._draw()

        if on_click:
            self.bind(
                "<ButtonRelease-1>",
                lambda e: (
                    on_click(card)
                    if 0 <= e.x < self.w and 0 <= e.y < self.h
                    else None
                ),
            )

    @classmethod
    def _load_image(cls, card: Card, width: int, height: int):
        path = card_image_path(card.color, card.value)
        if path is None:
            return None
        key = (str(path), width, height)
        if key not in cls._image_cache:
            image = tk.PhotoImage(file=str(path))
            factor = max(1, ceil(image.width() / width), ceil(image.height() / height))
            if factor > 1:
                image = image.subsample(factor, factor)
            cls._image_cache[key] = image
        return cls._image_cache[key]

    def _round_rect(self, x0, y0, x1, y1, r, **kw):
        pts = [
            x0 + r, y0,
            x1 - r, y0,
            x1, y0,
            x1, y0 + r,
            x1, y1 - r,
            x1, y1,
            x1 - r, y1,
            x0 + r, y1,
            x0, y1,
            x0, y1 - r,
            x0, y0 + r,
            x0, y0,
        ]
        return self.create_polygon(pts, smooth=True, **kw)

    def _draw(self) -> None:
        card, k, w, h = self.card, self.k, self.w, self.h
        value = str(card.value)
        is_wild = value in ("wild", "+4")

        fill = WILD_FILL if is_wild else COLOR_FILL.get(
            card.color,
            WILD_FILL,
        )
        text = DISPLAY_TEXT.get(value, value)
        big = len(text) <= 2
        corner = text if len(text) <= 2 else (
            "S" if value == "stop" else "W"
        )

        self._round_rect(
            1, 1, w - 1, h - 1,
            8 * k,
            fill="white",
            outline="#111111",
        )
        self._round_rect(
            5 * k, 5 * k,
            w - 5 * k, h - 5 * k,
            6 * k,
            fill=fill,
            outline="",
        )

        ox0, oy0 = 11 * k, 20 * k
        ox1, oy1 = w - 11 * k, h - 20 * k

        if is_wild:
            for i, color in enumerate(
                ("red", "yellow", "green", "blue")
            ):
                self.create_arc(
                    ox0,
                    oy0,
                    ox1,
                    oy1,
                    start=90 - 90 * i,
                    extent=-90,
                    fill=COLOR_FILL[color],
                    outline="",
                )
        else:
            self.create_oval(
                ox0,
                oy0,
                ox1,
                oy1,
                fill="white",
                outline="",
            )

        font = (
            ("Arial", max(1, int(22 * k)), "bold")
            if big
            else ("Arial", max(1, int(11 * k)), "bold")
        )

        cx, cy = w / 2, h / 2

        if is_wild:
            self.create_text(
                cx + 1,
                cy + 1,
                text=text,
                font=font,
                fill="#000000",
            )
            self.create_text(
                cx,
                cy,
                text=text,
                font=font,
                fill="#ffffff",
            )
        else:
            self.create_text(
                cx,
                cy,
                text=text,
                font=font,
                fill=COLOR_TEXT.get(card.color, "#000000"),
            )

        small = ("Arial", max(1, int(9 * k)), "bold")
        self.create_text(
            11 * k,
            12 * k,
            text=corner,
            font=small,
            fill="white",
        )
        self.create_text(
            w - 11 * k,
            h - 12 * k,
            text=corner,
            font=small,
            fill="white",
        )


class LastCardView(tk.Frame):
    def __init__(self, parent, scale=1.3):
        super().__init__(parent)

        self.scale = scale

        self.title_label = tk.Label(
            self,
            text="Carta sul tavolo",
            font=("Arial", 11, "bold"),
        )
        self.title_label.pack()

        self.holder = tk.Frame(self)
        self.holder.pack(pady=4)

        self.note = tk.Label(self, text="", font=("Arial", 10))
        self.note.pack()

        self.show(None)

    def show(self, card: Card | None, note: str = "") -> None:
        for child in self.holder.winfo_children():
            child.destroy()

        if card is None:
            tk.Label(
                self.holder,
                text="Nessuna carta",
                font=("Arial", 10),
            ).pack()
        else:
            CardWidget(
                self.holder,
                card,
                scale=self.scale,
            ).pack()

        self.note.config(text=note)


class CardsView(tk.Frame):
    def __init__(self, parent, on_card_selected):
        super().__init__(parent)

        self.on_card_selected = on_card_selected
        self._cards: list[Card] = []
        self.scale = 1.05

        self.cards_frame = tk.Frame(self)
        self.cards_frame.pack(anchor="center")

    def show(self, cards: list[Card]) -> None:
        self._cards = list(cards)
        self._render()

    def _sorted_cards(self) -> list[Card]:
        cards = list(self._cards)
        cards.sort(key=lambda c: (_rank_key(c), _color_key(c)))
        return cards

    def _render(self) -> None:
        for child in self.cards_frame.winfo_children():
            child.destroy()

        sorted_cards = self._sorted_cards()

        for index, card in enumerate(sorted_cards):
            widget = CardWidget(
                self.cards_frame,
                card,
                self.on_card_selected,
                scale=self.scale,
            )
            widget.grid(
                row=index // MAX_COLUMNS,
                column=index % MAX_COLUMNS,
                padx=3,
                pady=3,
            )
