/* 突发事件模拟仿真游戏 · 主页逻辑 */
"use strict";

const LS_KEY = "snake-gallery-liked";

let gamesData = null;      // data/games.json
let likesMap = {};         // { game_id: count }
let currentLectureId = 1;
let likedSet = new Set(JSON.parse(localStorage.getItem(LS_KEY) || "[]"));

/* ---------- 名字徽章：按名字哈希出稳定配色与装饰 ---------- */
const BADGE_THEMES = [
  { bg: "linear-gradient(135deg,#FF9FB2,#FFB07C)", emojis: ["🌸", "🍑"] },
  { bg: "linear-gradient(135deg,#7FD8BE,#8FCBFF)", emojis: ["🌿", "🐳"] },
  { bg: "linear-gradient(135deg,#C3B2F0,#8FCBFF)", emojis: ["🔮", "⭐"] },
  { bg: "linear-gradient(135deg,#FFD66B,#FFB07C)", emojis: ["🌻", "🍊"] },
  { bg: "linear-gradient(135deg,#8FCBFF,#7FD8BE)", emojis: ["☁️", "🍀"] },
  { bg: "linear-gradient(135deg,#FF8FA3,#C3B2F0)", emojis: ["🎀", "🦄"] },
  { bg: "linear-gradient(135deg,#6FCF97,#FFD66B)", emojis: ["🥑", "🌞"] },
  { bg: "linear-gradient(135deg,#F2994A,#FF5C7A)", emojis: ["🔥", "🍓"] },
  { bg: "linear-gradient(135deg,#56CCF2,#C3B2F0)", emojis: ["💧", "🐬"] },
  { bg: "linear-gradient(135deg,#FFB07C,#FFD66B)", emojis: ["🧸", "🍯"] },
  { bg: "linear-gradient(135deg,#9BE15D,#7FD8BE)", emojis: ["🍏", "🐸"] },
  { bg: "linear-gradient(135deg,#F857A6,#FF9FB2)", emojis: ["🌷", "🍭"] }
];

function hashName(name) {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.codePointAt(0)) >>> 0;
  return h;
}

function badgeHTML(author) {
  const theme = BADGE_THEMES[hashName(author) % BADGE_THEMES.length];
  return `
    <div class="name-badge" style="background:${theme.bg}">
      <span class="badge-emoji e1">${theme.emojis[0]}</span>
      <span class="badge-emoji e2">${theme.emojis[1]}</span>
      <span class="badge-name">${escapeHTML(author)}</span>
      <span class="badge-role">小游戏设计师</span>
    </div>`;
}

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

/* ---------- 数据加载 ---------- */
// 离线模式：无服务器（GitHub Pages / 静态托管）时自动降级，
// 点赞只存在本浏览器 localStorage，排行榜仅反映本机数据。
const LS_LIKES = "snake-gallery-likes-local";
let offlineMode = false;

function loadLocalLikes() {
  try { return JSON.parse(localStorage.getItem(LS_LIKES) || "{}"); }
  catch (e) { return {}; }
}

async function loadAll() {
  gamesData = await (await fetch("data/games.json")).json();
  try {
    const res = await fetch("api/likes");
    if (!res.ok) throw new Error("no like server");
    likesMap = await res.json();
  } catch (e) {
    offlineMode = true;
    likesMap = loadLocalLikes();
  }
  renderNav();
  renderLecture();
  renderRanking();
  if (offlineMode) showOfflineBadge();
}

function showOfflineBadge() {
  const hint = document.querySelector(".ranking-hint");
  if (hint) hint.innerHTML = "本机演示模式 ✨<br>点赞仅保存在此浏览器<br>（课堂共享排名请运行 server.py）";
}

async function refreshLikes() {
  if (offlineMode) return;
  try {
    likesMap = await (await fetch("api/likes")).json();
    renderRanking();
    updateCardLikeCounts();
  } catch (e) { /* 静默失败，下次轮询再试 */ }
}

/* ---------- 左栏：讲次导航 ---------- */
function renderNav() {
  const nav = document.getElementById("lectureNav");
  nav.innerHTML = "";
  for (const lec of gamesData.lectures) {
    const btn = document.createElement("button");
    btn.className = "lecture-tab" +
      (lec.id === currentLectureId ? " active" : "") +
      (lec.active ? "" : " locked");
    const short = lec.title.split("·")[0].trim() || `第${"一二三四五六七八"[lec.id - 1]}讲`;
    btn.textContent = short;
    if (lec.active) {
      btn.addEventListener("click", () => {
        currentLectureId = lec.id;
        closePlayer();
        renderNav();
        renderLecture();
      });
    } else {
      btn.title = "本讲作业尚未布置，敬请期待～";
    }
    nav.appendChild(btn);
  }
}

/* ---------- 中栏：卡片墙 ---------- */
function currentLecture() {
  return gamesData.lectures.find(l => l.id === currentLectureId);
}

function renderLecture() {
  const lec = currentLecture();
  const banner = document.getElementById("lectureBanner");
  banner.innerHTML = lec.active
    ? `<span class="banner-emoji">🎯</span>${escapeHTML(lec.title)}<span class="banner-note">点击卡片开始玩，玩完别忘了点赞哦</span>`
    : `<span class="banner-emoji">🚧</span>${escapeHTML(lec.title)}<span class="banner-note">本讲作业尚未布置，敬请期待</span>`;

  const grid = document.getElementById("cardsGrid");
  grid.innerHTML = "";

  if (!lec.active || lec.games.length === 0) {
    const div = document.createElement("div");
    div.className = "game-card coming-soon";
    div.style.gridColumn = "1 / -1";
    div.innerHTML = "🎈<br>游戏还在路上，先去第一讲看看吧";
    grid.appendChild(div);
    return;
  }

  for (const game of lec.games) {
    grid.appendChild(gameCard(game));
  }
}

function gameCard(game) {
  const card = document.createElement("div");
  card.className = "game-card";

  if (game.placeholder) {
    card.classList.add("coming-soon");
    card.innerHTML = `📮<br><strong>${escapeHTML(game.author)}</strong><br>作业提交中，敬请期待`;
    return card;
  }

  const liked = likedSet.has(game.id);
  const count = likesMap[game.id] || 0;
  const tags = (game.tags || []).map(t => `<span class="card-tag">${escapeHTML(t)}</span>`).join("");

  card.innerHTML = `
    ${badgeHTML(game.author)}
    <div class="card-title">${escapeHTML(game.title)}</div>
    <div class="card-tags">${tags}</div>
    <div class="card-actions">
      <button class="btn-play">▶ 开始玩</button>
      <button class="btn-like ${liked ? "liked" : ""}" data-game-id="${escapeHTML(game.id)}">
        ${liked ? "❤️" : "🤍"} <span class="like-count">${count}</span>
      </button>
    </div>`;

  card.querySelector(".btn-play").addEventListener("click", () => openPlayer(game));
  card.querySelector(".btn-like").addEventListener("click", (e) => likeGame(game, e));
  return card;
}

/* ---------- 播放器 ---------- */
function openPlayer(game) {
  const wrap = document.getElementById("playerWrap");
  const frame = document.getElementById("gameFrame");
  document.getElementById("playerTitle").textContent =
    `${game.title} · by ${game.author}`;
  frame.src = game.path + "index.html";
  wrap.classList.remove("hidden");
  wrap.scrollIntoView({ behavior: "smooth", block: "start" });
  frame.addEventListener("load", () => frame.contentWindow && frame.contentWindow.focus());
}

function closePlayer() {
  const wrap = document.getElementById("playerWrap");
  document.getElementById("gameFrame").src = "about:blank";
  wrap.classList.add("hidden");
}

document.getElementById("btnClosePlayer").addEventListener("click", closePlayer);

/* ---------- 点赞 ---------- */
async function likeGame(game, event) {
  if (likedSet.has(game.id)) return;
  likedSet.add(game.id);
  localStorage.setItem(LS_KEY, JSON.stringify([...likedSet]));

  const btn = event.currentTarget;
  btn.classList.add("liked", "bouncing");
  btn.querySelector(".like-count").textContent = (likesMap[game.id] || 0) + 1;
  btn.innerHTML = `❤️ <span class="like-count">${(likesMap[game.id] || 0) + 1}</span>`;

  // 飘出 +1 动画
  const toast = document.getElementById("likeToast");
  const rect = btn.getBoundingClientRect();
  toast.style.left = rect.left + rect.width / 2 - 20 + "px";
  toast.style.top = rect.top - 10 + "px";
  toast.classList.remove("pop");
  void toast.offsetWidth;
  toast.classList.add("pop");

  if (offlineMode) {
    // 本机演示模式：点赞只存 localStorage
    likesMap[game.id] = (likesMap[game.id] || 0) + 1;
    localStorage.setItem(LS_LIKES, JSON.stringify(likesMap));
  } else {
    try {
      const res = await fetch("api/like", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id: game.id })
      });
      const data = await res.json();
      likesMap[game.id] = data.likes;
    } catch (e) {
      likesMap[game.id] = (likesMap[game.id] || 0) + 1;
    }
  }
  renderRanking();
  updateCardLikeCounts();
}

function updateCardLikeCounts() {
  document.querySelectorAll(".btn-like .like-count").forEach(span => {
    const id = span.closest(".btn-like").dataset.gameId;
    span.textContent = likesMap[id] || 0;
  });
}

/* ---------- 右栏：排行榜 ---------- */
function renderRanking() {
  const list = document.getElementById("rankingList");
  const all = [];
  for (const lec of gamesData.lectures) {
    for (const g of (lec.games || [])) {
      if (!g.placeholder) all.push(g);
    }
  }
  all.sort((a, b) => (likesMap[b.id] || 0) - (likesMap[a.id] || 0));

  list.innerHTML = "";
  if (all.length === 0) {
    list.innerHTML = `<li class="ranking-empty">还没有游戏上榜～</li>`;
    return;
  }

  const medals = ["🥇", "🥈", "🥉"];
  all.forEach((g, i) => {
    const li = document.createElement("li");
    li.className = "rank-item" + (i < 3 ? ` top${i + 1}` : "");
    li.innerHTML = `
      ${i < 3
        ? `<span class="rank-medal">${medals[i]}</span>`
        : `<span class="rank-num">${i + 1}</span>`}
      <div class="rank-info">
        <div class="rank-author">${escapeHTML(g.author)}</div>
        <div class="rank-game">${escapeHTML(g.title)}</div>
      </div>
      <span class="rank-likes">❤️ ${likesMap[g.id] || 0}</span>`;
    list.appendChild(li);
  });
}

/* ---------- 启动 ---------- */
loadAll();
setInterval(refreshLikes, 10000);
