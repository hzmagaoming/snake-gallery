"""风景贪吃蛇：十关追逐冒险。只依赖 Python 标准库 Tkinter。"""
import json
import math
import random
import time
import tkinter as tk
from collections import deque
from pathlib import Path

CELL, N, SIZE = 24, 25, 600
W, H, X0, Y0 = 910, 704, 36, 66
RECORD = Path.home() / '.landscape_snake_record.json'
INK, SUB = '#344454', '#6B7E88'
# 关卡名、天空、水或地面、远景、植物、点缀、情景
SCENES = [
 ('晨雾丛林','#E5F7E9','#D5EFCF','#A9DCBC','#56A57B','#F7B77D','jungle'),
 ('芦苇湿地','#E5F8F6','#C9EBE6','#A2D6CE','#6BAC94','#EFC987','wetland'),
 ('雨后雨林','#D5E8ED','#BFE3D8','#81BCAC','#397F68','#ECA8A9','rain'),
 ('湖畔黄昏','#FBEBD8','#D3E7E0','#98C1B9','#688E8B','#EEA578','lake'),
 ('竹海秘径','#E6F1DA','#D6E8D0','#9EBA91','#59866B','#F0BC75','bamboo'),
 ('珊瑚浅湾','#E4F7FA','#D4F1F7','#A9DAEC','#60B4C8','#FDAE98','coast'),
 ('萤火森林','#DFE8E5','#C9DCDA','#8FABAC','#46766E','#F7DA7F','firefly'),
 ('山谷溪流','#E3ECF5','#DBECE5','#A8C8BD','#5F9985','#EAAA82','valley'),
 ('秋日林地','#F8EBD8','#EADBC2','#CCAE89','#9A795E','#E99C67','autumn'),
 ('星光沼泽','#EDE9FB','#DFE8F6','#B9CDE4','#8CA8C3','#F8D79D','stars'),
]

class LandscapeSnake:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('糖果虫虫 · 十关风景追逐')
        self.root.resizable(False, False)
        self.c = tk.Canvas(self.root, width=W, height=H, bg='#F3F6F3', highlightthickness=0)
        self.c.pack()
        self.root.bind('<KeyPress>', self.key)
        self.c.bind('<Button-1>', self.click)
        self.best, self.unlocked = self.load()
        self.level, self.score, self.lives, self.deaths = 0, 0, 5, 0
        self.drawn_level = None
        self.buttons = {}
        self.reset()
        self.last_frame = time.perf_counter()
        self.root.after(16, self.frame)

    @staticmethod
    def load():
        try:
            d = json.loads(RECORD.read_text(encoding='utf-8'))
            return max(0,int(d['best'])), max(0,min(9,int(d['unlocked'])))
        except (OSError, ValueError, TypeError, KeyError):
            return 0,0

    def save(self):
        try:
            RECORD.write_text(json.dumps({'best':self.best,'unlocked':self.unlocked}), encoding='utf-8')
        except OSError: pass

    def reset(self):
        self.me = deque([(7,12),(6,12),(5,12)])
        starts = [(19,12),(19,4),(19,20)]
        count = 1 if self.level<3 else 2 if self.level<7 else 3
        self.enemies = [deque([(x,y),(x+1,y),(x+2,y)]) for x,y in starts[:count]]
        self.enemy_directions = [(-1,0)]*count
        self.hazards = set()
        if self.level>=3:
            self.hazards.update({(11,5),(12,5),(13,5),(11,19),(12,19),(13,19)})
        if self.level>=6:
            self.hazards.update({(4,7),(4,8),(20,16),(20,17)})
        if self.level>=8:
            self.hazards.update({(9,21),(10,21),(15,3),(16,3)})
        self.direction = (1,0)
        self.prev_me = list(self.me)
        self.prev_enemies = [list(e) for e in self.enemies]
        self.enemy_last_step = [time.perf_counter()]*count
        self.pending, self.queued = None,False
        self.eaten = 0
        self.state = 'ready'
        self.reason = ''
        self.tip = ''
        self.food, self.bonus = None,None
        self.bonus_expiry = 0.0
        self.bonus_spawned = False
        self.combo = 0
        self.combo_until = 0.0
        self.freeze_until = 0.0
        self.notice, self.notice_until = '',0.0
        self.pause_started = 0.0
        self.last_step = time.perf_counter()
        self.enemy_clock = 0.0
        self.place_food()

    def free_cell(self):
        used = set(self.me)|self.hazards
        for enemy in self.enemies: used.update(enemy)
        if self.bonus: used.add(self.bonus)
        if self.food: used.add(self.food)
        return random.choice([(x,y) for x in range(N) for y in range(N) if (x,y) not in used])

    def place_food(self):
        # 果实优先出现在玩家前方约 3～7 格内，避开猎手附近。
        old = self.food
        self.food = None
        used = set(self.me)|self.hazards
        for enemy in self.enemies: used.update(enemy)
        if self.bonus: used.add(self.bonus)
        hx,hy = self.me[0]
        options=[]
        for x in range(N):
            for y in range(N):
                pos=(x,y)
                if pos in used or any(self.distance(pos,e[0])<=2 for e in self.enemies):
                    continue
                dist=self.distance(pos,(hx,hy))
                if 3<=dist<=7:
                    forward=((x-hx)*self.direction[0]+(y-hy)*self.direction[1])
                    weight=3 if forward>0 else 1
                    options.extend([pos]*weight)
        if options:
            self.food=random.choice(options)
        else:
            try: self.food=self.free_cell()
            except IndexError: self.food=old

    def start(self):
        now = time.perf_counter()
        if self.state in ('paused', 'help') and self.pause_started:
            paused = now-self.pause_started
            for name in ('bonus_expiry', 'notice_until', 'combo_until', 'freeze_until'):
                if getattr(self,name)>self.pause_started:
                    setattr(self,name,getattr(self,name)+paused)
        self.pause_started = 0.0
        self.state = 'playing'
        self.last_step = now
        self.enemy_clock = 0.0

    def pause(self,mode='paused'):
        self.pause_started = time.perf_counter()
        self.state = mode

    def retry(self):
        self.score = 0
        self.reset()
        self.start()

    def restart_run(self):
        self.level, self.score, self.lives, self.unlocked, self.deaths = 0, 0, 5, 0, 0
        self.save()
        self.reset()
        self.start()

    def lose_life(self, reason):
        self.lives -= 1
        self.deaths += 1
        self.reason = reason
        tips = {
            '被追踪虫抓到了': '技巧：利用穿墙改变路线，别一直沿直线逃跑。',
            '碰到了危险荆棘': '技巧：荆棘位置固定，先看清红色标记再转弯。',
            '撞到了自己的身体': '技巧：提前一格转弯，避免钻进自己围成的小圈。',
        }
        self.tip = tips.get(reason, '技巧：优先吃附近果实，保持开阔的退路。')
        if self.deaths >= 4:
            self.tip = '技巧：连续吃 3 颗能冻住追兵，趁机拿到附近的生命心。'
        self.bonus = None
        if self.lives <= 0:
            self.level, self.unlocked = 0, 0
            self.save()
            self.state = 'gameover'
        else:
            self.state = 'hurt'

    def continue_after_hit(self):
        self.reset()
        self.start()

    def next_level(self):
        if self.level == 9:
            self.state = 'victory'
        else:
            self.level += 1
            self.unlocked = max(self.unlocked,self.level)
            self.save()
            self.reset()
            self.start()
            now=time.perf_counter()
            if self.level==3:
                message='新危险：红色荆棘不能碰！还有第二条追踪虫'
            elif self.level==6:
                message='小心！本关新增了荆棘，先观察红色标记'
            elif self.level==7:
                message='第三条追踪虫出现！利用穿墙和冻结争取空间'
            elif self.level==8:
                message='最后几关荆棘更多，别贪心冲进死角'
            else:
                message=f'第 {self.level+1} 关开始！找附近的果实，留意追踪虫'
            self.notice,self.notice_until=message,now+4

    def key(self,e):
        k=e.keysym.lower()
        dirs={'up':(0,-1),'w':(0,-1),'down':(0,1),'s':(0,1),
              'left':(-1,0),'a':(-1,0),'right':(1,0),'d':(1,0)}
        if k in dirs and self.state in ('ready','playing'):
            d=dirs[k]
            if not self.queued and d != (-self.direction[0],-self.direction[1]):
                self.pending,self.queued=d,True
                if self.state=='ready': self.start()
        elif k in ('space','p'):
            if self.state in ('ready','paused','help'): self.start()
            elif self.state=='playing': self.pause()
            elif self.state=='clear': self.next_level()
            elif self.state=='hurt': self.continue_after_hit()
            elif self.state=='gameover': self.restart_run()
            else: self.retry()
        elif k=='return' and self.state=='clear': self.next_level()
        elif k=='r': self.restart_run()
        elif k=='h':
            if self.state=='playing': self.pause('help')
            elif self.state=='help': self.start()
        elif k=='escape' and self.state=='playing': self.pause()

    def click(self,e):
        for name,box in self.buttons.items():
            x1,y1,x2,y2=box
            if x1<=e.x<=x2 and y1<=e.y<=y2:
                if name=='main':
                    if self.state=='playing': self.pause()
                    elif self.state=='clear': self.next_level()
                    elif self.state=='hurt': self.continue_after_hit()
                    elif self.state=='gameover': self.restart_run()
                    elif self.state=='victory': self.restart_run()
                    else: self.start()
                elif name=='retry': self.restart_run()
                elif name.startswith('stage'):
                    pass  # 关卡地图仅展示当前挑战进度；失去所有生命必须重头开始。
                break

    @staticmethod
    def move(p,d): return ((p[0]+d[0])%N,(p[1]+d[1])%N)

    @staticmethod
    def distance(a,b):
        dx,dy=abs(a[0]-b[0]),abs(a[1]-b[1])
        return min(dx,N-dx)+min(dy,N-dy)

    def enemy_choice(self,index):
        enemy=self.enemies[index]
        direction=self.enemy_directions[index]
        choices=[]
        occupied=set(self.hazards)
        for i,other in enumerate(self.enemies):
            occupied.update(list(other)[:-1] if i==index else other)
        for d in ((1,0),(-1,0),(0,1),(0,-1)):
            if d==(-direction[0],-direction[1]): continue
            p=self.move(enemy[0],d)
            if p in occupied or p in list(self.me)[1:]: continue
            choices.append((self.distance(p,self.me[0])+random.random()*.12,d,p))
        if not choices: return None,None
        _,d,p=min(choices)
        return d,p

    def protect_or_lose(self,now,index=0):
        self.lose_life('被追踪虫抓到了')
        return False

    def award_points(self,points,now):
        before=self.score//50
        self.score+=points
        earned=self.score//50-before
        if earned and self.lives<8:
            self.lives=min(8,self.lives+earned)
            self.notice,self.notice_until='积分达到 50 的倍数，奖励一条命！',now+3
        if self.score>self.best:
            self.best=self.score
            self.save()

    def step_me(self,now):
        self.prev_me=list(self.me)
        if self.pending is not None: self.direction,self.pending=self.pending,None
        self.queued=False
        head=self.move(self.me[0],self.direction)
        eating=head==self.food
        body=self.me if eating else list(self.me)[:-1]
        if head in body:
            self.lose_life('撞到了自己的身体')
            return
        if head in self.hazards:
            self.lose_life('碰到了危险荆棘')
            return
        for index,enemy in enumerate(self.enemies):
            if head in enemy:
                if not self.protect_or_lose(now,index): return
                break
        self.me.appendleft(head)
        if eating:
            self.eaten+=1
            self.combo = self.combo+1 if now<self.combo_until else 1
            self.combo_until = now+8
            self.award_points(10,now)
            if self.combo>=3:
                self.combo=0
                self.freeze_until=now+3.5
                self.award_points(20,now)
                self.notice,self.notice_until='连吃 3 颗！+20 分，追踪虫冻结 3.5 秒',now+3

            goal=3+self.level//3
            if self.eaten>=goal:
                self.state='clear'
                self.unlocked=max(self.unlocked,min(9,self.level+1))
                self.save()
                return
            self.place_food()
            if not self.bonus_spawned:
                self.bonus_spawned=True
                nearby=[(x,y) for x in range(N) for y in range(N)
                        if 2<=self.distance((x,y),self.me[0])<=6
                        and (x,y) not in (set(self.me)|self.hazards|{self.food})
                        and all((x,y) not in e for e in self.enemies)]
                self.bonus=random.choice(nearby) if nearby else self.free_cell()
                self.bonus_expiry=now+12
                self.notice,self.notice_until='生命心出现！碰到它可直接增加一条命',now+3
        else: self.me.pop()
        if head==self.bonus:
            self.bonus=None
            if self.lives<8:
                self.lives+=1
                self.notice,self.notice_until='拾取生命心：+1 条命！',now+3
            else:
                self.award_points(10,now)
                self.notice,self.notice_until='生命已满：生命心转为 +10 分！',now+3

    def step_enemy(self,now,index):
        d,p=self.enemy_choice(index)
        if d is None: return
        self.enemy_directions[index]=d
        self.prev_enemies[index]=list(self.enemies[index])
        self.enemy_last_step[index]=now
        enemy=self.enemies[index]
        enemy.appendleft(p)
        enemy.pop()
        if p in self.me: self.protect_or_lose(now,index)
        # 追踪虫不能偷走玩家的果实。
        # 追踪虫也不会抢走生命心。

    def frame(self):
        now=time.perf_counter()
        dt=min(.08,now-self.last_frame)
        self.last_frame=now
        if self.state=='playing':
            player_speed=max(.11,.205-self.level*.008)
            enemy_speed=max(.15,.285-self.level*.010)
            self.enemy_clock+=dt
            if self.bonus and now>=self.bonus_expiry: self.bonus=None
            if self.combo and now>=self.combo_until: self.combo=0
            if self.freeze_until and now>=self.freeze_until:
                self.freeze_until=0.0
                self.notice,self.notice_until='冻结结束：追踪虫重新行动，小心！',now+2.7
            player_due=now-self.last_step>=player_speed
            if now<self.freeze_until: self.enemy_clock=0.0
            enemy_due=self.enemy_clock>=enemy_speed and now>=self.freeze_until
            old_player=self.me[0]
            old_heads=[enemy[0] for enemy in self.enemies]
            if player_due:
                self.step_me(now)
                self.last_step=now
            if self.state=='playing' and enemy_due:
                for i in range(len(self.enemies)):
                    if self.state!='playing': break
                    self.step_enemy(now,i)
                self.enemy_clock=0
            if self.state=='playing' and player_due and enemy_due:
                for i,old in enumerate(old_heads):
                    if self.me[0]==old and self.enemies[i][0]==old_player:
                        self.protect_or_lose(now,i)
                        break
        self.draw(now)
        self.root.after(25,self.frame)

    def oval(self,x,y,rx,ry,color,outline=''):
        self.c.create_oval(x-rx,y-ry,x+rx,y+ry,fill=color,outline=outline)

    def box(self,x1,y1,x2,y2,color,r=12):
        c=self.c
        c.create_rectangle(x1+r,y1,x2-r,y2,fill=color,outline='')
        c.create_rectangle(x1,y1+r,x2,y2-r,fill=color,outline='')
        for x in (x1+r,x2-r):
            for y in (y1+r,y2-r): self.oval(x,y,r,r,color)

    def text(self,x,y,s,size=12,color=INK,bold=False,anchor='nw'):
        self.c.create_text(x,y,text=s,fill=color,anchor=anchor,
                           font=('Microsoft YaHei UI',size,'bold' if bold else 'normal'))

    def scenery(self,now):
        """粉彩风景插画：逐关更换地形、植物与装饰。"""
        c=self.c
        name,sky,ground,distant,plants,accent,kind=SCENES[self.level]
        c.create_rectangle(X0,Y0,X0+SIZE,Y0+SIZE,fill=sky,outline='')
        # 柔软的圆丘与水面，不遮挡游戏中的蛇。
        for x,y,rx,ry,col in [
            (X0+50,Y0+472,112,70,distant),
            (X0+212,Y0+488,140,76,ground),
            (X0+416,Y0+469,153,82,distant),
            (X0+565,Y0+495,120,75,ground),
        ]: self.oval(x,y,rx,ry,col)
        if kind in ('wetland','lake','coast','valley','stars'):
            water='#B8E7E9' if kind!='stars' else '#BDD3E9'
            c.create_polygon(X0,Y0+531,X0+125,Y0+512,X0+268,Y0+533,
                             X0+446,Y0+501,X0+SIZE,Y0+525,
                             X0+SIZE,Y0+SIZE,X0,Y0+SIZE,fill=water,outline='')
            for i in range(8):
                px=X0+25+i*77; py=Y0+545+(i%3)*14
                c.create_arc(px,py,px+39,py+10,start=195,extent=145,
                             style='arc',outline='#ECFAF5',width=2)
        rng=random.Random(self.level*971+123)
        # 插画元素集中在两侧，保留中间的移动区域。
        for i in range(23):
            px=X0+rng.choice((rng.randint(12,83),rng.randint(516,587)))
            py=Y0+rng.randint(45,558)
            if kind=='bamboo':
                c.create_line(px,py-19,px,py+18,fill=plants,width=3)
                self.oval(px-7,py-5,8,3,plants)
                self.oval(px+7,py+5,8,3,plants)
            elif kind in ('wetland','lake','stars'):
                c.create_line(px,py+12,px,py-15,fill=plants,width=2)
                self.oval(px,py-19,3,9,accent)
            elif kind in ('coast','valley'):
                self.oval(px,py,14,8,plants)
                self.oval(px+5,py-5,8,5,distant)
            else:
                c.create_line(px,py+16,px,py-8,fill=plants,width=3)
                self.oval(px-8,py-13,12,11,plants)
                self.oval(px+8,py-13,12,11,plants)
                self.oval(px,py-22,11,11,distant)
        for i in range(34):
            px=X0+rng.randint(10,590); py=Y0+rng.randint(16,565)
            color=accent if i%3==0 else '#FFFFFF'
            self.oval(px,py,2.5 if i%3==0 else 2,2.5 if i%3==0 else 2,color)
        if kind in ('firefly','stars'):
            for i in range(14):
                px=X0+rng.randint(22,572); py=Y0+rng.randint(20,440)
                self.oval(px,py,3,3,'#FFF3BE')

    def draw_snake(self,segments,body,head,look,previous=None,alpha=1):
        c=self.c
        positions=[]
        for i,(x,y) in enumerate(segments):
            if previous and i<len(previous):
                px,py=previous[i]
                if abs(x-px)>N//2 or abs(y-py)>N//2:
                    positions.append((x,y))  # 穿越边界时直接从另一侧出现
                else:
                    positions.append((px+(x-px)*alpha,py+(y-py)*alpha))
            else: positions.append((x,y))
        for i,(x,y) in reversed(list(enumerate(positions))):
            cx,cy=X0+x*CELL+12,Y0+y*CELL+12
            # 连缀的圆节身体，保持参考图中软软的虫虫轮廓。
            if i<len(segments)-1:
                x2,y2=positions[i+1]
                if abs(x-x2)+abs(y-y2)<1.2:
                    c.create_line(cx,cy,X0+x2*CELL+12,Y0+y2*CELL+12,
                                  fill=body,width=17,capstyle='round')
            if i:
                self.oval(cx,cy+1,11,11,body)
                if i%4==0: self.oval(cx-3,cy-4,2,2,'#F1FFF4')
            else:
                dx,dy=look
                for side in (-1,1):
                    ax,ay=cx+side*7-dx*3,cy-11-dy*3
                    c.create_line(cx+side*5,cy-6,ax,ay,fill=body,width=2)
                    self.oval(ax,ay,2.8,2.8,'#FFD7D9' if head=='#49AE80' else '#FFE6CF')
                self.oval(cx,cy,12.5,12.5,head)
                for ex in (-5,5):
                    self.oval(cx+ex,cy-3,3.9,4.8,'#FFFFFF')
                    self.oval(cx+ex+dx,cy-2+dy,2,2.6,'#342F47')
                    self.oval(cx+ex-1,cy-5,1,1,'#FFFFFF')
                self.oval(cx-9,cy+4,2.8,1.8,'#F7A6B6')
                self.oval(cx+9,cy+4,2.8,1.8,'#F7A6B6')
                c.create_arc(cx-4,cy-1,cx+4,cy+8,start=200,extent=140,
                             style='arc',outline='#A16A78',width=2)

    def button(self,name,x,y,w,label,color):
        self.buttons[name]=(x,y,x+w,y+42)
        self.box(x,y,x+w,y+42,color,12)
        self.text(x+w/2,y+21,label,13,'#FFFFFF',True,'center')

    def draw(self,now):
        c=self.c
        self.buttons.clear()
        name,sky,ground,distant,plants,accent,kind=SCENES[self.level]
        if self.drawn_level != self.level:
            c.delete('all')
            c.create_rectangle(0,0,W,H,fill='#FFF8EF',outline='')
            for x,y,r,col in [(12,13,24,'#FFD3DF'),(583,30,16,'#CBEEDA'),
                               (888,62,35,'#FCE3B6'),(21,682,39,'#D9E9FF')]:
                self.oval(x,y,r,r,col)
            self.text(36,17,'糖 果 虫 虫',22,'#E85D93',True)
            self.text(205,25,'SCENIC ADVENTURE  /  风景追逐',10,'#AC8195',True)
            self.scenery(now)
            for hx,hy in self.hazards:
                cx,cy=X0+hx*CELL+12,Y0+hy*CELL+12
                self.oval(cx,cy,10,10,'#FFE4DB')
                self.text(cx,cy,'✕',16,'#DE6470',True,'center')
            self.static_last=c.find_all()[-1]
            self.drawn_level=self.level
        c.delete('dynamic')
        if self.food:
            x,y=self.food
            fx,fy=X0+x*CELL+12,Y0+y*CELL+12
            r=10+math.sin(now*6)*1.2
            self.oval(fx,fy,r+2,r+2,'#FFE7BD')
            self.oval(fx,fy,r,r,'#FFAF71')
            self.oval(fx-4,fy-4,2,2,'#FFFFFF')
        if self.bonus:
            x,y=self.bonus
            fx,fy=X0+x*CELL+12,Y0+y*CELL+12
            self.oval(fx,fy,12,12,'#FFE2E9')
            self.text(fx,fy,'♥',17,'#E76488',True,'center')
        for i,enemy in enumerate(self.enemies):
            colors=[('#F19388','#E77E79'),('#B89EE8','#9E7CCC'),('#FFBA77','#F2A053')]
            body,head=colors[i]
            enemy_interval=max(.15,.285-self.level*.010)
            alpha=min(1,(now-self.enemy_last_step[i])/enemy_interval)
            self.draw_snake(enemy,body,head,self.enemy_directions[i],self.prev_enemies[i],alpha)
        player_interval=max(.11,.205-self.level*.008)
        alpha=min(1,(now-self.last_step)/player_interval)
        self.draw_snake(self.me,'#83D5A0','#49AE80',self.direction,self.prev_me,alpha)
        self.box(654,Y0,875,Y0+SIZE,'#FFFFFF',20)
        self.text(673,84,f'第 {self.level+1} / 10 关',18,'#E973A5',True)
        self.text(673,118,name,16,INK,True)
        self.text(673,150,f'绿色是你 · {len(self.enemies)} 条虫子追你',11,'#896F8C')
        goal=3+self.level//3
        self.text(673,185,'关卡进度',12,'#91798F')
        self.box(673,211,850,225,'#F3EAF0',7)
        if self.eaten: self.box(673,211,673+177*self.eaten/goal,225,'#FF84A7',7)
        self.text(673,235,f'{self.eaten} / {goal} 颗果实',11,'#896F8C')
        self.text(673,271,'当前得分',12,'#91798F')
        self.text(673,296,f'{self.score:04d}',28,'#F1729C',True)
        self.text(673,343,f'最高纪录  {self.best:04d}',12,'#9A6E91',True)
        self.text(673,366,f'生命  {self.lives} / 8  ♥',12,'#E97693',True)
        self.text(673,388,'关卡地图',12,INK,True)
        for i in range(10):
            x,y=673+(i%5)*36,416+(i//5)*39
            open_=i<=self.unlocked
            color='#FF84A7' if i==self.level else '#D9EEE4' if open_ else '#EEE8EE'
            self.box(x,y,x+31,y+31,color,8)
            self.text(x+15,y+15,str(i+1),10,'#FFFFFF' if i==self.level else INK if open_ else '#B5AAB7',True,'center')
            self.buttons[f'stage{i}']=(x,y,x+31,y+31)
        labels={'ready':'开始探险','playing':'暂停一下','paused':'继续游戏','help':'继续游戏',
                'clear':'进入下一关','hurt':'继续挑战','gameover':'从第一关重来','victory':'重新探险'}
        self.button('main',673,534,177,labels[self.state],'#FF84A7')
        self.button('retry',673,585,177,'从第一关重新挑战','#ADA0D9')
        if self.state=='playing' and now<self.notice_until:
            self.box(X0+116,Y0+19,X0+SIZE-116,Y0+58,'#FFFFFF',12)
            self.text(X0+SIZE/2,Y0+38,self.notice,12,'#916C86',True,'center')
        if self.state=='playing' and now<self.freeze_until:
            self.text(673,489,f'❄ 追踪虫冻结 {self.freeze_until-now:.1f} 秒',10,'#789BC8')
        elif self.state=='playing' and self.combo:
            self.text(673,489,f'连吃 {self.combo}/3 · 还剩 {max(0,self.combo_until-now):.1f} 秒',10,'#BE9160')
        elif self.bonus and self.state=='playing':
            self.text(673,489,'♥ 生命心限时出现，碰到可加一条命',10,'#BE9160')
        else:
            self.text(673,489,'♥ 每累计 50 分加一条命（最多 8 条）',10,'#BE9160')
        self.text(36,678,'方向键 / WASD 移动 · 空格暂停 · H 查看玩法 · R 从头挑战 · 红色荆棘危险',11,'#997C96')
        if self.state!='playing':
            c.create_rectangle(X0+1,Y0+1,X0+SIZE-1,Y0+SIZE-1,
                               fill='#FFFFFF',stipple='gray50',outline='')
            titles={'ready':'走进 '+name,'paused':'休息一下～','clear':'过关啦！',
                    'hurt':'失去一颗心','gameover':'挑战结束','victory':'十关通关啦！','help':'玩法说明'}
            notes={'ready':'绿色虫虫由你控制 · 粉色虫虫会追你',
                   'paused':'空格继续游戏','clear':'按空格或回车进入下一关',
                   'hurt':f'{self.reason} · 还剩 {self.lives} 条命，空格再试',
                   'gameover':'生命已用完 · 空格从第一关重新开始',
                   'victory':'十段风景都探索完了！','help':'按 H 或空格返回游戏'}
            mid=X0+SIZE/2
            self.oval(mid,Y0+SIZE/2-105,31,31,'#A1E5AF')
            for d in (-11,11): self.oval(mid+d,Y0+SIZE/2-112,4,5,'#433754')
            self.text(mid,Y0+SIZE/2-20,titles[self.state],28,'#E85D93',True,'center')
            self.text(mid,Y0+SIZE/2+31,notes[self.state],13,INK,False,'center')
            if self.state=='hurt' and self.deaths>=2:
                self.text(mid,Y0+SIZE/2+67,self.tip,12,'#A26373',True,'center')
            if self.state in ('ready','clear','help'):
                hazard_note='红色荆棘碰到会扣命' if self.hazards else '本关没有危险荆棘'
                self.text(mid,Y0+SIZE/2+57,f'{len(self.enemies)} 条追踪虫 · {hazard_note} · 初始 5 条命',11,'#A26373',False,'center')
            if self.state in ('ready','help'):
                self.text(mid,Y0+SIZE/2+69,'方向键 / WASD 移动 · 吃果实即可过关',12,INK,False,'center')
                self.text(mid,Y0+SIZE/2+94,'粉色生命心直接加命；每累计 50 分也会加命',12,INK,False,'center')
                self.text(mid,Y0+SIZE/2+119,'8 秒内连吃 3 颗：+20 分，冻结追踪虫 3.5 秒',12,INK,False,'center')
                self.text(mid,Y0+SIZE/2+144,'最多 8 条命 · 穿过边界可从对侧出现',12,INK,False,'center')
        for item in c.find_all():
            if item>self.static_last: c.addtag_withtag('dynamic',item)

    def run(self): self.root.mainloop()

if __name__=='__main__': LandscapeSnake().run()
