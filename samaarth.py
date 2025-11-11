

import tkinter as tk
import random
import time
from functools import partial

CELL_SIZE = 28
PADDING = 4
FONT = ("Helvetica", 12, "bold")

COLORS = {
    1: "blue",
    2: "green",
    3: "red",
    4: "dark blue",
    5: "dark red",
    6: "teal",
    7: "black",
    8: "gray",
}


class Cell:
    def _init_(self, row, col):
        self.row = row
        self.col = col
        self.is_mine = False
        self.revealed = False
        self.flagged = False
        self.adjacent = 0


class MinesweeperGame:
    def _init_(self, rows=10, cols=14, mines=20):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.first_click = True
        self.start_time = None
        self.end_time = None
        self._create_board()

    def _create_board(self):
        self.grid = [[Cell(r, c) for c in range(self.cols)] for r in range(self.rows)]
        self.placed_mines = 0
        self.game_over = False
        self.victory = False

    def place_mines(self, safe_r, safe_c):
        # Place mines randomly but avoid the first clicked cell and its neighbors
        positions = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        # exclude the 3x3 around safe cell
        excluded = set()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr = safe_r + dr
                cc = safe_c + dc
                if 0 <= rr < self.rows and 0 <= cc < self.cols:
                    excluded.add((rr, cc))
        candidates = [p for p in positions if p not in excluded]
        random.shuffle(candidates)
        for i in range(self.mines):
            r, c = candidates[i]
            self.grid[r][c].is_mine = True
        self._calc_adjacency()

    def _calc_adjacency(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c].is_mine:
                    self.grid[r][c].adjacent = -1
                    continue
                count = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        rr = r + dr
                        cc = c + dc
                        if 0 <= rr < self.rows and 0 <= cc < self.cols:
                            if self.grid[rr][cc].is_mine:
                                count += 1
                self.grid[r][c].adjacent = count

    def reveal(self, r, c):
        if self.game_over:
            return
        cell = self.grid[r][c]
        if cell.flagged or cell.revealed:
            return
        if self.first_click:
            # ensure first click is never a mine and its neighbors safe
            self.place_mines(r, c)
            self.first_click = False
            self.start_time = time.time()

        cell.revealed = True
        if cell.is_mine:
            self.game_over = True
            self.end_time = time.time()
            return

        # If zero adjacent mines, flood fill neighbors recursively
        if cell.adjacent == 0:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr = r + dr
                    cc = c + dc
                    if 0 <= rr < self.rows and 0 <= cc < self.cols:
                        if not self.grid[rr][cc].revealed:
                            self.reveal(rr, cc)

        self._check_victory()

    def toggle_flag(self, r, c):
        if self.game_over or self.grid[r][c].revealed:
            return
        self.grid[r][c].flagged = not self.grid[r][c].flagged
        self._check_victory()

    def _check_victory(self):
        # Victory if all non-mine cells are revealed
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if not cell.is_mine and not cell.revealed:
                    return
        # All safe cells revealed
        self.victory = True
        self.game_over = True
        self.end_time = time.time()

    def reveal_all_mines(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c].is_mine:
                    self.grid[r][c].revealed = True


class MinesweeperUI(tk.Frame):
    def _init_(self, master, rows=10, cols=14, mines=20):
        super()._init_(master)
        self.master = master
        self.game = MinesweeperGame(rows, cols, mines)
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.flags_left = mines
        self._build_ui()
        self._draw_board()
        self._update_clock()

    def _build_ui(self):
        self.master.title("Cellular Grid Hazard Simulation — Minesweeper")
        top_frame = tk.Frame(self.master)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=6, pady=6)

        self.mine_label = tk.Label(top_frame, text=f"Mines: {self.mines}", font=FONT)
        self.mine_label.pack(side=tk.LEFT, padx=8)

        self.reset_btn = tk.Button(top_frame, text="New Game", command=self.reset_game)
        self.reset_btn.pack(side=tk.LEFT, padx=8)

        self.timer_label = tk.Label(top_frame, text="Time: 0", font=FONT)
        self.timer_label.pack(side=tk.RIGHT, padx=8)

        self.canvas = tk.Canvas(self.master,
                                width=self.cols * CELL_SIZE + PADDING * 2,
                                height=self.rows * CELL_SIZE + PADDING * 2,
                                bg="#ddd")
        self.canvas.pack(padx=6, pady=6)

        # Bind events
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        # For Mac trackpad right-click
        self.canvas.bind("<Button-2>", self._on_right_click)

    def _draw_board(self):
        self.canvas.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                x1 = PADDING + c * CELL_SIZE
                y1 = PADDING + r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#bbb", outline="#888", tags=self._tag(r, c))
        self._render_cells()

    def _render_cells(self):
        # Remove previous text/icons
        self.canvas.delete("cell_text")
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.game.grid[r][c]
                x = PADDING + c * CELL_SIZE + CELL_SIZE/2
                y = PADDING + r * CELL_SIZE + CELL_SIZE/2
                tag = self._tag(r, c)
                if cell.revealed:
                    # Replace rectangle look
                    x1 = PADDING + c * CELL_SIZE
                    y1 = PADDING + r * CELL_SIZE
                    x2 = x1 + CELL_SIZE
                    y2 = y1 + CELL_SIZE
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#eee", outline="#999", tags=tag)
                    if cell.is_mine:
                        # mine symbol
                        self.canvas.create_oval(x1+6, y1+6, x2-6, y2-6, fill="black", tags=("cell_text", tag))
                    elif cell.adjacent > 0:
                        color = COLORS.get(cell.adjacent, "black")
                        self.canvas.create_text(x, y, text=str(cell.adjacent), font=FONT, fill=color, tags=("cell_text", tag))
                else:
                    # Concealed cell
                    if cell.flagged:
                        self.canvas.create_text(x, y, text="⚑", font=("Helvetica", 14), tags=("cell_text", tag))

        # Update mine counter
        self.flags_left = self.mines - self._count_flags()
        self.mine_label.config(text=f"Mines: {self.flags_left}")

        # If game over, reveal mines and show message
        if self.game.game_over:
            if self.game.victory:
                self._show_end_message("You Win!")
            else:
                self.game.reveal_all_mines()
                self._render_cells()
                self._show_end_message("Game Over")

    def _tag(self, r, c):
        return f"cell_{r}_{c}"

    def _on_left_click(self, event):
        c = int((event.x - PADDING) // CELL_SIZE)
        r = int((event.y - PADDING) // CELL_SIZE)
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        self.game.reveal(r, c)
        self._render_cells()

    def _on_right_click(self, event):
        c = int((event.x - PADDING) // CELL_SIZE)
        r = int((event.y - PADDING) // CELL_SIZE)
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        self.game.toggle_flag(r, c)
        self._render_cells()

    def _count_flags(self):
        count = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if self.game.grid[r][c].flagged:
                    count += 1
        return count

    def reset_game(self):
        self.game = MinesweeperGame(self.rows, self.cols, self.mines)
        self.flags_left = self.mines
        self._draw_board()

    def _show_end_message(self, text):
        # Overlay message
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        self.canvas.create_rectangle(10, h//2 - 30, w - 10, h//2 + 30, fill="#222", stipple="gray25", outline="")
        self.canvas.create_text(w//2, h//2, text=text, fill="white", font=("Helvetica", 20, "bold"))

    def _update_clock(self):
        if self.game.start_time and not self.game.game_over:
            elapsed = int(time.time() - self.game.start_time)
            self.timer_label.config(text=f"Time: {elapsed}")
        elif self.game.game_over and self.game.end_time and self.game.start_time:
            elapsed = int(self.game.end_time - self.game.start_time)
            self.timer_label.config(text=f"Time: {elapsed}")
        else:
            self.timer_label.config(text="Time: 0")
        self.after(250, self._update_clock)


def main():
    root = tk.Tk()

    # Easy to change board parameters
    rows = 12
    cols = 16
    mines = 30

    app = MinesweeperUI(root, rows=rows, cols=cols, mines=mines)
    app.pack()
    root.resizable(False, False)
    root.mainloop()


if _name_ == "_main_":
    main()