# Snake Game

## 一、项目简介

这是一个基于 Python 和 Pygame 开发的贪吃蛇小游戏。玩家需要控制蛇在迷宫路线中移动，吃到食物并不断进入更高等级，同时避开障碍物、自己的身体和毒物。

## 二、运行环境

- Python 3.10 或更高版本
- Pygame 2.x
- macOS、Windows 或 Linux

## 三、安装依赖

在终端中进入项目文件夹后执行：

```bash
python3 -m pip install pygame
```

如果电脑使用的是 Windows，也可以使用：

```bash
py -m pip install pygame
```

## 四、启动游戏

先进入 `SnakeGame` 文件夹：

```bash
cd SnakeGame
```

然后运行：

```bash
python3 snake.py
```

Windows 用户可以运行：

```bash
python snake.py
```

## 五、操作说明

- `Space`：开始游戏或重新开始
- `方向键` 或 `WASD`：连续控制蛇移动，转弯不再受整格限制
- `P`：暂停或继续游戏
- `Esc`：退出游戏

## 六、游戏规则

- 蛇需要在每一关成长到该关目标长度后，才能进入下一关；关卡越高，目标长度越长。
- 不同等级拥有不同密度和布局的迷宫障碍物。
- 第 4 轮开始，障碍物改为带缺口的螺旋布局；蛇可以沿连续曲线移动并在任意时刻转向。
- 前几关难度较低，后续关卡逐步增加障碍物。
- 食物只会生成在蛇可以到达的区域，不会出现在封闭死区中。
- 蛇撞到边界、迷宫障碍物、自己的身体或毒物时，游戏结束。
- 不同关卡的障碍物和食物使用不同颜色主题。

## 七、项目文件

```text
SnakeGame/
├── snake.py      # 游戏主程序
└── README.md     # 项目说明
```

## 八、提交说明

压缩项目文件夹时，保留 `snake.py` 和 `README.md` 即可。`__pycache__` 文件夹属于 Python 临时缓存，可以删除，不需要提交。
