"""تولید خروجی HTML چندکاناله با ظاهر و رفتار دقیقا شبیه اپ تلگرام (آفلاین، بدون منبع خارجی)."""

from __future__ import annotations

import html
import os
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")
MIME_MAP = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
    ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm",
    ".mkv": "video/x-matroska", ".ogg": "audio/ogg", ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4", ".wav": "audio/wav", ".pdf": "application/pdf",
    ".zip": "application/zip", ".rar": "application/x-rar-compressed",
    ".doc": "application/msword", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint", ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg", ".oga"}
FILE_ICONS = {
    ".pdf": "PDF", ".doc": "DOC", ".docx": "DOC", ".xls": "XLS",
    ".xlsx": "XLS", ".ppt": "PPT", ".pptx": "PPT", ".zip": "ZIP",
    ".rar": "RAR", ".txt": "TXT",
}
WEEKDAYS_FA = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
MONTHS_FA = [
    "ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن",
    "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر",
]


def _mime(path: str) -> str:
    return MIME_MAP.get(os.path.splitext(path)[1].lower(), "application/octet-stream")


def _local(value: object) -> Optional[datetime]:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(TEHRAN)


def _format_time(value: object) -> str:
    local = _local(value)
    if not local:
        return html.escape(str(value or ""))
    return f"{local:%H:%M}"


def _day_key(value: object) -> str:
    local = _local(value)
    if not local:
        return "نامشخص"
    return f"{local.year:04d}-{local.month:02d}-{local.day:02d}"


def _day_label(value: object) -> str:
    local = _local(value)
    if not local:
        return "نامشخص"
    today = datetime.now(TEHRAN).date()
    delta = (local.date() - today).days
    if delta == 0:
        return "امروز"
    if delta == -1:
        return "دیروز"
    return f"{local.day} {MONTHS_FA[local.month - 1]} {local.year}"


def _format_size(value: int) -> str:
    if not value:
        return ""
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    if value < 1024 * 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MB"
    return f"{value / (1024 * 1024 * 1024):.1f} GB"


def _render_media(message: dict) -> str:
    path = message.get("media_path")
    if not path or not os.path.exists(path):
        if message.get("media_skipped"):
            return '<div class="skipped">⚠️ فایل بزرگ‌تر از سقف مجاز است</div>'
        return ""
    rel = html.escape(message.get("media_rel_path") or f"media/{os.path.basename(path)}")
    media_type = message.get("media_type", "")
    extension = os.path.splitext(path)[1].lower()
    if media_type == "image" or extension in IMAGE_EXTS:
        return f'<a class="bubble-media image-link" href="{rel}" target="_blank"><img class="media-image" src="{rel}" loading="lazy" alt=""></a>'
    if media_type == "video" or extension in VIDEO_EXTS:
        poster = message.get("media_poster", "")
        poster_attr = f' poster="{html.escape(poster)}"' if poster else ""
        return (
            f'<div class="bubble-media"><video class="media-video" controls preload="metadata"{poster_attr}>'
            f'<source src="{rel}" type="{_mime(path)}">مرورگر شما ویدئو را پشتیبانی نمی‌کند.</video></div>'
        )
    if media_type == "audio" or extension in AUDIO_EXTS:
        name = html.escape(message.get("media_name") or os.path.basename(path))
        return f'<div class="audio"><div class="media-label">🎵 {name}</div><audio controls preload="metadata" src="{rel}"></audio></div>'
    name = html.escape(message.get("media_name") or os.path.basename(path))
    label = FILE_ICONS.get(extension, "FILE")
    size = _format_size(int(message.get("media_size", 0) or os.path.getsize(path)))
    return (
        f'<a class="document" href="{rel}" download="{name}"><span class="file-icon">{label}</span>'
        f'<span class="file-copy"><b>{name}</b><small>{size}</small></span><span class="download">↓</span></a>'
    )


def _render_message(message: dict, index: int) -> str:
    text = html.escape(message.get("text", "") or "").replace("\n", "<br>")
    reactions = "".join(
        f'<span class="reaction">{html.escape(str(item.get("emoji", "")))} {item.get("count", 0)}</span>'
        for item in message.get("reactions", [])
    )
    media_html = _render_media(message)
    has_media = bool(media_html) and "skipped" not in media_html
    text_html = f'<div class="bubble-text">{text}</div>' if text else ""
    if not media_html and not text:
        text_html = '<div class="bubble-text empty">رسانه یا متن قابل نمایش نیست</div>'
    type_name = "متن" if not message.get("media_type") else message.get("media_type")
    views = int(message.get("views", 0) or 0)
    views_html = f'<span class="views">👁 {views:,}</span>' if views else ""
    bubble_class = "bubble media-bubble" if has_media and not text else "bubble"
    return (
        f'<div class="msg-row" data-search="{html.escape((message.get("text", "") or "").casefold())}" '
        f'data-type="{html.escape(str(type_name))}" id="message-{index}">'
        f'<div class="{bubble_class}">'
        f'{media_html}{text_html}'
        f'<div class="meta"><span class="reactions">{reactions}</span>{views_html}'
        f'<span class="time">{_format_time(message.get("date"))}</span></div>'
        f'</div></div>'
    )


def _render_channel(channel: dict, index: int) -> str:
    name = html.escape(channel.get("name", ""))
    username = html.escape(channel.get("username", ""))
    avatar = channel.get("avatar_rel_path", "")
    avatar_html = (
        f'<img class="avatar" src="{html.escape(avatar)}" alt="">'
        if avatar
        else f'<div class="avatar fallback">{html.escape((name or "?")[:1])}</div>'
    )
    messages = channel.get("messages", [])

    rows: list[str] = []
    last_day: Optional[str] = None
    for message_index, message in enumerate(messages):
        day_key = _day_key(message.get("date"))
        if day_key != last_day:
            rows.append(
                f'<div class="day-sep" data-search="" data-type="__day__">'
                f'<span>{_day_label(message.get("date"))}</span></div>'
            )
            last_day = day_key
        rows.append(_render_message(message, index * 100000 + message_index))
    messages_html = "".join(rows)

    handle = f'<span>@{username}</span> · ' if username else ""
    return (
        f'<section class="channel" data-channel="{name}" id="channel-{index}">'
        f'<header class="chat-header">{avatar_html}<div class="chat-header-copy"><h2>{name}</h2>'
        f'<p>{handle}{len(messages)} پیام</p></div>'
        f'<a class="channel-link" href="#channel-{index}" aria-label="لینک کانال">#</a></header>'
        f'<div class="feed">{messages_html}</div></section>'
    )


def generate_html(
    channel_name: Optional[str] = None,
    channel_avatar_path: Optional[str] = None,
    messages: Optional[list] = None,
    msg_count: int = 0,
    *,
    channels: Optional[list[dict]] = None,
) -> str:
    if channels is None:
        channels = [{
            "name": channel_name or "",
            "avatar_rel_path": "media/avatar.jpg" if channel_avatar_path else "",
            "messages": messages or [],
        }]
    title = html.escape(channel_name or (channels[0].get("name", "") if channels else "Archive"))
    channel_html = "".join(_render_channel(channel, index) for index, channel in enumerate(channels))
    total_messages = sum(len(channel.get("messages", [])) for channel in channels)
    return f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<title>{title}</title>
<style>
:root{{
  --bg:#0e1621;--panel:#17212b;--panel-2:#1c2733;--in-bubble:#182533;
  --line:#0000004d;--text:#e9edef;--muted:#8296a8;--accent:#5eb5f7;--accent-2:#64b5f6;
  --tick:#4fae4e;--radius:14px;--shadow:0 4px 18px #00000040;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{
  margin:0;min-height:100vh;color:var(--text);
  font-family:Vazirmatn,"Segoe UI",Tahoma,sans-serif;
  background-color:var(--bg);
  background-image:
    radial-gradient(circle at 15% 8%,#17212b 0,transparent 40%),
    radial-gradient(circle at 85% 92%,#17212b 0,transparent 40%),
    repeating-linear-gradient(135deg,#0000 0 26px,#ffffff05 26px 27px),
    repeating-linear-gradient(45deg,#0000 0 26px,#ffffff05 26px 27px);
  padding-bottom:64px;
}}
.topbar{{position:sticky;top:0;z-index:20;padding:14px clamp(14px,4vw,40px);background:var(--panel);border-bottom:1px solid var(--line);box-shadow:var(--shadow)}}
.topbar-inner{{max-width:760px;margin:auto;display:flex;align-items:center;gap:14px;justify-content:space-between}}
.brand{{display:flex;align-items:center;gap:12px;min-width:0}}
.brand-mark{{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(140deg,var(--accent),#8e6ff0);font-size:19px;font-weight:900;color:#0b1621;flex:none}}
.brand h1{{margin:0;font-size:16px;letter-spacing:-.2px}}
.brand small{{display:block;color:var(--muted);font-size:11px;margin-top:2px}}
.count{{color:var(--muted);font-size:12px;white-space:nowrap}}

.toolbar{{max-width:760px;margin:16px auto 0;padding:0 14px;display:grid;grid-template-columns:1fr auto;gap:10px}}
.search-wrap{{position:relative}}
.search{{width:100%;background:var(--panel);border:1px solid var(--line);border-radius:20px;color:var(--text);padding:11px 40px 11px 14px;outline:none;font-size:13px;transition:.2s}}
.search:focus{{border-color:var(--accent);box-shadow:0 0 0 3px #5eb5f722}}
.search-icon{{position:absolute;right:14px;top:11px;color:var(--muted);font-size:15px}}
.filters{{display:flex;gap:6px;align-items:center}}
.filter{{cursor:pointer;border:1px solid var(--line);background:var(--panel);color:var(--muted);border-radius:16px;padding:9px 12px;font-size:11px}}
.filter.active,.filter:hover{{background:var(--accent);color:#08131f;border-color:var(--accent)}}

.summary{{max-width:760px;margin:12px auto 0;padding:0 14px;color:var(--muted);font-size:11px}}
.summary strong{{color:var(--accent)}}

.channel{{max-width:720px;margin:24px auto 0;padding:0 10px}}
.chat-header{{display:flex;gap:12px;align-items:center;padding:10px 14px;background:var(--panel);border-bottom:1px solid var(--line);border-radius:12px 12px 0 0;position:sticky;top:70px;z-index:6;box-shadow:var(--shadow)}}
.avatar{{width:44px;height:44px;border-radius:50%;object-fit:cover;flex:none;border:1px solid #ffffff1a}}
.avatar.fallback{{display:grid;place-items:center;background:linear-gradient(140deg,#2a9dcc,#6354bc);font-size:19px;font-weight:800}}
.chat-header-copy{{min-width:0;flex:1}}
.chat-header h2{{font-size:15px;margin:0 0 3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.chat-header p{{margin:0;color:var(--muted);font-size:11.5px}}
.channel-link{{color:var(--accent);text-decoration:none;font-size:17px;padding:6px 9px;border-radius:8px}}

.feed{{background:transparent;padding:14px 6px 22px;display:flex;flex-direction:column;gap:2px;border-radius:0 0 12px 12px}}

.day-sep{{display:flex;justify-content:center;margin:14px 0 10px}}
.day-sep span{{background:#182533cc;color:var(--muted);font-size:11.5px;padding:5px 14px;border-radius:12px}}

.msg-row{{display:flex;justify-content:flex-end;padding:0 4px;margin:2px 0}}
.bubble{{
  position:relative;max-width:78%;background:var(--in-bubble);
  border-radius:var(--radius) var(--radius) 4px var(--radius);
  padding:7px 10px 6px 8px;box-shadow:0 1px 2px #00000030;
}}
.bubble::after{{
  content:"";position:absolute;bottom:0;left:-7px;width:14px;height:16px;
  background:var(--in-bubble);
  -webkit-mask:radial-gradient(circle at top left,transparent 14px,#000 14.5px);
  mask:radial-gradient(circle at top left,transparent 14px,#000 14.5px);
}}
.bubble-text{{font-size:14.5px;line-height:1.65;word-break:break-word;white-space:pre-wrap;padding:2px 3px 0}}
.bubble-text.empty{{color:var(--muted);font-style:normal}}
.bubble-media{{border-radius:9px;overflow:hidden;background:#0b141c;margin-bottom:2px}}
.media-image{{display:block;width:100%;max-height:420px;object-fit:cover;cursor:zoom-in;border-radius:9px}}
.media-video{{display:block;width:100%;max-height:420px;border-radius:9px;background:#05090d}}
.media-bubble{{padding-bottom:4px}}
.audio{{background:var(--panel-2);border-radius:9px;padding:10px;color:var(--muted);font-size:11px;margin:2px 0}}
.audio audio{{display:block;width:100%;margin-top:8px}}
.document{{display:flex;align-items:center;gap:10px;background:var(--panel-2);border-radius:9px;padding:9px;color:var(--text);text-decoration:none;margin:2px 0}}
.file-icon{{width:38px;height:38px;border-radius:9px;background:linear-gradient(145deg,#236184,#263d76);display:grid;place-items:center;font-size:9px;font-weight:800;color:#d9f5ff;flex:none}}
.file-copy{{min-width:0;flex:1}}
.file-copy b{{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px}}
.file-copy small{{display:block;color:var(--muted);margin-top:3px}}
.download{{color:var(--accent);font-size:20px}}
.skipped{{color:var(--muted);font-size:12px;padding:8px 2px}}

.meta{{display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-top:2px;padding:0 2px}}
.reactions:empty{{display:none}}
.reactions{{display:flex;gap:4px;flex-wrap:wrap}}
.reaction{{background:#ffffff14;border-radius:10px;padding:1px 7px;font-size:10.5px;color:#c7efff}}
.views{{color:var(--muted);font-size:10.5px}}
.time{{color:var(--muted);font-size:10.5px}}

.empty-state{{max-width:720px;margin:50px auto;text-align:center;color:var(--muted);padding:30px}}
.top{{position:fixed;left:16px;bottom:16px;border:1px solid var(--line);background:var(--panel);color:var(--accent);width:40px;height:40px;border-radius:50%;cursor:pointer;font-size:17px;box-shadow:var(--shadow)}}

.lightbox{{position:fixed;inset:0;background:#000000ee;z-index:30;display:grid;place-items:center;padding:20px;cursor:zoom-out}}
.lightbox img{{max-width:96vw;max-height:94vh;object-fit:contain;border-radius:10px;box-shadow:0 20px 80px #000}}

@media(max-width:650px){{
  .toolbar{{grid-template-columns:1fr;margin-top:12px}}
  .filters{{justify-content:stretch}}.filter{{flex:1;text-align:center}}
  .channel{{margin-top:16px;padding:0}}
  .chat-header{{top:64px;border-radius:0}}
  .bubble{{max-width:88%}}
}}
</style>
</head>
<body>
<header class="topbar"><div class="topbar-inner"><div class="brand"><div class="brand-mark">✦</div><div><h1>آرشیو پیام‌ها</h1><small>زمان‌ها به وقت تهران نمایش داده می‌شوند</small></div></div><div class="count">{len(channels)} کانال · {total_messages} پیام</div></div></header>
<div class="toolbar"><div class="search-wrap"><span class="search-icon">⌕</span><input class="search" id="search" type="search" placeholder="جست‌وجو در پیام‌ها و کانال‌ها..." aria-label="جست‌وجو"></div><div class="filters"><button class="filter active" data-filter="all">همه</button><button class="filter" data-filter="متن">متن</button><button class="filter" data-filter="image">عکس</button><button class="filter" data-filter="video">ویدئو</button></div></div>
<div class="summary" id="summary">نمایش <strong>{total_messages}</strong> پیام از <strong>{len(channels)}</strong> کانال</div>
{channel_html or '<div class="empty-state">پیامی برای نمایش وجود ندارد.</div>'}
<button class="top" id="top" aria-label="بازگشت به بالا">↑</button>
<script>
const search=document.getElementById("search"), filters=[...document.querySelectorAll(".filter")], channels=[...document.querySelectorAll(".channel")], summary=document.getElementById("summary");
let active="all";
function apply(){{
  const q=(search.value||"").trim().toLocaleLowerCase();
  let visible=0,visibleChannels=0;
  channels.forEach(ch=>{{
    let shown=0;
    const channelName=(ch.dataset.channel||"").toLocaleLowerCase();
    ch.querySelectorAll(".msg-row").forEach(row=>{{
      const okType=active==="all"||row.dataset.type===active;
      const okText=!q||channelName.includes(q)||(row.dataset.search||"").includes(q);
      const visibleRow=okType&&okText;
      row.hidden=!visibleRow;
      if(visibleRow)shown++;
    }});
    ch.querySelectorAll(".day-sep").forEach(sep=>{{
      let node=sep.nextElementSibling,hasVisible=false;
      while(node&&!node.classList.contains("day-sep")){{
        if(!node.hidden){{hasVisible=true;break}}
        node=node.nextElementSibling;
      }}
      sep.hidden=!hasVisible;
    }});
    ch.hidden=!shown;
    if(shown)visibleChannels++;
    visible+=shown;
  }});
  summary.innerHTML=`نمایش <strong>${{visible}}</strong> پیام از <strong>${{visibleChannels}}</strong> کانال`;
}}
search.addEventListener("input",apply);
filters.forEach(btn=>btn.addEventListener("click",()=>{{filters.forEach(x=>x.classList.remove("active"));btn.classList.add("active");active=btn.dataset.filter;apply()}}));
document.getElementById("top").addEventListener("click",()=>scrollTo({{top:0,behavior:"smooth"}}));
document.addEventListener("click",event=>{{
  const image=event.target.closest(".media-image");
  if(!image)return;
  event.preventDefault();
  const layer=document.createElement("div");
  layer.className="lightbox";
  const copy=document.createElement("img");
  copy.src=image.src;
  layer.appendChild(copy);
  layer.onclick=()=>layer.remove();
  document.body.appendChild(layer);
}});
</script>
</body>
</html>"""
