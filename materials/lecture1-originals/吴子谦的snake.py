#!/usr/bin/env python3
"""一个仅使用 Python 标准库的终端贪吃蛇小游戏。"""

import curses
import random
import time


TICK_SECONDS = 0.10
MIN_HEIGHT = 12
MIN_WIDTH = 28


def new_food(snake, height, width):
    """在不与蛇重叠的位置生成食物。"""
    empty_cells = [
        (y, x)
        for y in range(1, height - 1)
        for x in range(1, width - 1)
        if (y, x) not in snake
    ]
    return random.choice(empty_cells) if empty_cells else None


def draw_game(screen, snake, food, score):
    height, width = screen.getmaxyx()
    screen.erase()
    screen.border()
    title = " Snake  |  方向键 / WASD 移动  |  Q 退出 "
    screen.addnstr(0, max(1, (width - len(title)) // 2), title, width - 2)
    screen.addnstr(0, 2, f" 分数: {score} ", width - 4)

    if food:
        screen.addch(food[0], food[1], "●")
    for index, (y, x) in enumerate(snake):
        screen.addch(y, x, "■" if index == 0 else "□")
    screen.refresh()


def play(screen):
    curses.curs_set(0)
    screen.nodelay(True)
    screen.keypad(True)

    height, width = screen.getmaxyx()
    if height < MIN_HEIGHT or width < MIN_WIDTH:
        screen.nodelay(False)
        screen.erase()
        screen.addstr(0, 0, f"终端窗口至少需要 {MIN_WIDTH}×{MIN_HEIGHT} 个字符。请放大后重试。")
        screen.getch()
        return

    center_y, center_x = height // 2, width // 2
    snake = [(center_y, center_x), (center_y, center_x - 1), (center_y, center_x - 2)]
    direction = (0, 1)
    food = new_food(snake, height, width)
    score = 0
    key_to_direction = {
        curses.KEY_UP: (-1, 0), ord("w"): (-1, 0), ord("W"): (-1, 0),
        curses.KEY_DOWN: (1, 0), ord("s"): (1, 0), ord("S"): (1, 0),
        curses.KEY_LEFT: (0, -1), ord("a"): (0, -1), ord("A"): (0, -1),
        curses.KEY_RIGHT: (0, 1), ord("d"): (0, 1), ord("D"): (0, 1),
    }

    while True:
        height, width = screen.getmaxyx()
        if height < MIN_HEIGHT or width < MIN_WIDTH:
            screen.erase()
            screen.addstr(0, 0, "窗口过小：请放大终端窗口，或按 Q 退出。")
            screen.refresh()
            while True:
                key = screen.getch()
                if key in (ord("q"), ord("Q")):
                    return
                height, width = screen.getmaxyx()
                if height >= MIN_HEIGHT and width >= MIN_WIDTH:
                    break
                time.sleep(0.05)

        key = screen.getch()
        if key in (ord("q"), ord("Q")):
            return
        next_direction = key_to_direction.get(key)
        # 禁止立即掉头，以免蛇撞到自己。
        if next_direction and next_direction != (-direction[0], -direction[1]):
            direction = next_direction

        head_y, head_x = snake[0]
        new_head = (head_y + direction[0], head_x + direction[1])
        hits_wall = new_head[0] in (0, height - 1) or new_head[1] in (0, width - 1)
        hits_self = new_head in snake[:-1]
        if hits_wall or hits_self:
            break

        snake.insert(0, new_head)
        if new_head == food:
            score += 1
            food = new_food(snake, height, width)
            if food is None:
                break
        else:
            snake.pop()

        draw_game(screen, snake, food, score)
        time.sleep(TICK_SECONDS)

    screen.nodelay(False)
    message = f"游戏结束！最终分数：{score}。按 R 再来一局，按其他键退出。"
    screen.addnstr(height // 2, max(1, (width - len(message)) // 2), message, width - 2)
    screen.refresh()
    if screen.getch() in (ord("r"), ord("R")):
        play(screen)


if __name__ == "__main__":
    curses.wrapper(play)
