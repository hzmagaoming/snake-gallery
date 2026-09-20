EMERGENCY RUN | 应急行动
最终交付版 · 2026-09-15

这是完整源码版，需要 Python 才能运行。
请整体保留文件夹，不能只打开或发送 main.py。
如果收到 ZIP，请先完整解压，再运行。

一、先进入正确文件夹

macOS：
1. 打开“终端”。
2. 输入 cd，后面加一个空格，先不要按回车。
3. 把本交付文件夹从 Finder 拖进终端。
4. 按回车。提示符应显示 EMERGENCY_RUN_Final_2026-09-15，不应仍是 ~。

下面所有命令都在这个文件夹里执行。
每次只输入一行，按回车，执行完再输入下一行。
不要输入示例外的 (base)、用户名或 %。

二、使用 Anaconda 安装环境

你已经创建过 emergency-run 环境：
直接执行：
conda activate emergency-run

如果尚未创建：
conda create -n emergency-run python=3.11
出现 Proceed ([y]/n)? 时输入 y，然后按回车。
创建结束后执行：
conda activate emergency-run

终端前面的环境名称应变成 (emergency-run)。
不要使用之前 Python 3.14 的 (base) 环境。

三、安装依赖（第一次运行需要）

python -m pip install -r requirements.txt

等安装成功后再启动。
requirements.txt 固定了本版验证使用的 pygame==2.6.1。

四、启动游戏

python main.py

点击“游戏说明”查看四步救援流程和物资/危险图例。
点击“开始行动”，查看任务卡，再点击“出发”。
此交付副本存档为零分、未完成教学，首次行动会使用教学布局。

五、以后怎么打开

重新打开终端后：
1. 用第一节的方法进入交付文件夹。
2. 执行 conda activate emergency-run
3. 执行 python main.py

已经安装成功，不用每次重新安装或创建环境。

六、基本操作

WASD / 方向键：移动
SPACE：暂停 / 继续
E：风险扫描
R：重新开始
ESC：返回主菜单
主菜单“退出”或窗口关闭按钮：退出游戏

主要目标：找到群众 → 接触装车 → 前往帐篷安置点 → 完成转移。
物资同样需要送到安置点结算；危险障碍和积水应避开。

七、常见报错

找不到 main.py 或 requirements.txt：
说明终端不在交付文件夹；重新执行第一节。

No module named pygame：
先确认已启用 emergency-run，再执行第三节安装命令。

安装时报 Failed building wheel：
先执行 python --version，检查是否为 Python 3.11；
不要在 Python 3.14 的 base 中安装本版。

中文变成方框：
本版已验证 macOS 系统中文字体。
Windows / Linux 的中文字体未验收，需按 02_交接说明.md 补充可用字体路径。

八、文件说明

README.md：项目简介、操作、已实现功能和文件职责
02_交接说明.md：冻结版本范围、资源说明、验收和已知限制
screenshots/：交付副本实际渲染的界面截图
SHA256SUMS.txt：交付文件校验清单
data/save.json：本地记录；删除后游戏会自动建立默认记录

本交付副本的初始记录已清零，原开发项目的个人试玩存档没有改动。
文件夹需要可写权限，否则本地记录无法正常保存。
