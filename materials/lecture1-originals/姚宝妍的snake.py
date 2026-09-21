# -*- coding: utf-8 -*-
"""贪吃蛇小游戏（Python 3.7+，仅使用标准库 tkinter）。"""

import random
import tkinter as tk


CELL_SIZE = 20
COLS = 30
ROWS = 22
SPEED = 110
WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("贪吃蛇")
        self.root.resizable(False, False)

        self.info = tk.Label(
            root,
            font=("Microsoft YaHei UI", 13, "bold"),
            bg="#101820",
            fg="white",
            pady=8,
        )
        self.info.pack(fill="x")

        self.canvas = tk.Canvas(
            root,
            width=WIDTH,
            height=HEIGHT,
            bg="#101820",
            highlightthickness=0,
        )
        self.canvas.pack()

        self.timer = None
        self.root.bind("<KeyPress>", self.on_key)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.restart()

    def restart(self):
        """开始新游戏。"""
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None

        middle_x = COLS // 2
        middle_y = ROWS // 2
        self.snake = [
            (middle_x, middle_y),
            (middle_x - 1, middle_y),
            (middle_x - 2, middle_y),
        ]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.paused = False
        self.game_over = False
        self.food = self.make_food()
        self.draw()
        self.schedule()

    def make_food(self):
        """把食物随机放到空格中。"""
        empty = [
            (x, y)
            for x in range(COLS)
            for y in range(ROWS)
            if (x, y) not in self.snake
        ]
        return random.choice(empty) if empty else None

    def on_key(self, event):
        """处理键盘操作。"""
        key = event.keysym.lower()

        if key == "r":
            self.restart()
            return

        if key in ("space", "p") and not self.game_over:
            self.paused = not self.paused
            self.draw()
            if not self.paused:
                self.schedule()
            return

        if self.paused or self.game_over:
            return

        key_directions = {
            "up": (0, -1),
            "w": (0, -1),
            "down": (0, 1),
            "s": (0, 1),
            "left": (-1, 0),
            "a": (-1, 0),
            "right": (1, 0),
            "d": (1, 0),
        }
        wanted = key_directions.get(key)
        if wanted is None:
            return

        opposite = (-self.direction[0], -self.direction[1])
        if wanted != opposite:
            self.next_direction = wanted

    def schedule(self):
        """安排下一次移动。"""
        if self.timer is None and not self.paused and not self.game_over:
            self.timer = self.root.after(SPEED, self.move)

    def move(self):
        """让蛇移动一格。"""
        self.timer = None
        if self.paused or self.game_over:
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        eating = new_head == self.food

        hit_wall = not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS)
        body_to_check = self.snake if eating else self.snake[:-1]
        hit_body = new_head in body_to_check

        if hit_wall or hit_body:
            self.game_over = True
            self.draw()
            return

        self.snake.insert(0, new_head)
        if eating:
            self.score += 10
            self.food = self.make_food()
            if self.food is None:
                self.game_over = True
        else:
            self.snake.pop()

        self.draw()
        self.schedule()

    def draw_cell(self, position, color, oval=False):
        """画出蛇的一节或食物。"""
        x, y = position
        margin = 3 if oval else 1
        x1 = x * CELL_SIZE + margin
        y1 = y * CELL_SIZE + margin
        x2 = (x + 1) * CELL_SIZE - margin
        y2 = (y + 1) * CELL_SIZE - margin

        if oval:
            self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline="")
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def draw_message(self, title, subtitle):
        """显示暂停或结束信息。"""
        self.canvas.create_rectangle(
            0,
            HEIGHT // 2 - 60,
            WIDTH,
            HEIGHT // 2 + 60,
            fill="black",
            outline="",
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 - 18,
            text=title,
            fill="white",
            font=("Microsoft YaHei UI", 24, "bold"),
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 + 25,
            text=subtitle,
            fill="white",
            font=("Microsoft YaHei UI", 13),
        )

    def draw(self):
        """重绘游戏画面。"""
        self.canvas.delete("all")
        self.info.config(
            text="得分：{}    方向键/WASD移动    空格/P暂停    R重开".format(
                self.score
            )
        )

        if self.food is not None:
            self.draw_cell(self.food, "#ff5252", oval=True)

        for index, part in enumerate(self.snake):
            color = "#76d275" if index == 0 else "#43a047"
            self.draw_cell(part, color)

        if self.game_over:
            title = "恭喜通关！" if self.food is None else "游戏结束"
            self.draw_message(title, "按 R 重新开始")
        elif self.paused:
            self.draw_message("游戏暂停", "按空格或 P 继续")

    def close(self):
        """关闭游戏窗口。"""
        if self.timer is not None:
            self.root.after_cancel(self.timer)
        self.root.destroy()


def main():
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
