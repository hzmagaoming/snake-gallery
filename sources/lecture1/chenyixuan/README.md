# 中文贪吃蛇

一个基于 Python 3.11 和 Pygame 的桌面贪吃蛇游戏。

桌面版采用 1040×720 的高级深青色界面，包含玻璃质感卡片、动态光晕、
拟人卡通蛇、独立游戏侧栏、实时数据仪表和鼠标悬停反馈。

## 首次安装

需要先安装 Miniconda。下载或复制本项目后，打开终端，并进入
`snake_game.py` 所在的项目文件夹。

macOS 或 Linux：

```bash
cd "/请替换为你电脑上的项目文件夹路径"
```

Windows PowerShell：

```powershell
cd "C:\请替换为你电脑上的项目文件夹路径"
```

提示：在 macOS 中，可以先输入 `cd `（`cd` 后保留一个空格），然后把项目
文件夹直接拖进终端窗口，终端会自动填入正确路径。进入目录后，可以用
`pwd` 查看当前位置，并用 `ls` 确认列表中包含 `snake_game.py`。

第一次运行时创建环境并安装 Pygame：

```bash
conda create -n snake-game python=3.11 -y
conda activate snake-game
python -m pip install pygame
```

如果电脑中已经存在 `snake-game` 环境，可以跳过创建和安装步骤。

## 启动游戏

每次打开新的终端后，先进入 `snake_game.py` 所在的文件夹，再启动游戏：

```bash
cd "/请替换为你电脑上的项目文件夹路径"
conda activate snake-game
python snake_game.py
```

看到终端提示符前出现 `(snake-game)`，表示环境已成功激活。不要只执行
`python snake_game.py` 而不进入项目文件夹，否则 Python 会提示找不到文件。

也可以不激活环境，直接运行：

```bash
cd "/请替换为你电脑上的项目文件夹路径"
conda run -n snake-game python snake_game.py
```

如果不想切换文件夹，可以给出脚本的完整路径：

```bash
conda run -n snake-game python "/请替换为完整路径/snake_game.py"
```

例如，项目文件夹名为 `0914贪吃蛇` 时，应该进入该文件夹，而不是停留在
macOS 的用户主目录 `~` 中。

## 操作方法

- 主菜单点击“开始新游戏”，输入昵称并选择 1–18 的初始速度
- 新玩家昵称不可与排行榜中的已有昵称重复；重复时会提示更换
- 设置界面使用左右方向键或 `+/-`：调整初始速度
- 回车或点击“进入游戏”：确认设置并开始
- 方向键或 `WASD`：控制移动
- 空格或 `P`：暂停/继续
- `R` 或回车：游戏结束后重新开始
- 游戏中按 `Esc`：返回主菜单
- 主菜单按 `Esc` 或关闭窗口：退出游戏
- 游戏侧栏也可点击“暂停游戏”或“退出本轮并返回主菜单”

玩家可以在启动界面自行选择初始速度。游戏开始后，每吃到 3 个食物，
移动速度提高一级，最高为 18 级；重新开始会保留已选择的初始速度。

每局会随机生成 14 块岩石障碍。障碍不会出现在蛇的出生安全区或食物位置；
蛇头碰到岩石、边界或自身都会立即结束游戏。重新开始时障碍会重新随机生成。

## 排行榜

- 游戏界面顶部实时显示历史最高分
- 每轮结束后自动记录昵称和得分，并显示本轮得分、个人最佳和排行榜名次
- 同一昵称只保留一条记录；再次挑战时仅用更高成绩更新排行榜
- 点击“再玩一局”可保留昵称和初始速度继续挑战
- 排行榜保存在游戏目录中的 `leaderboard.json`，最多保留 100 条成绩

## 自动测试

```bash
conda run -n snake-game python -m unittest -v
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy conda run -n snake-game python snake_game.py --smoke-test
```
