"""Build the standalone 12-slide scientific pitch and embedded paper library."""

from __future__ import annotations

import base64
import html
import json
import mimetypes
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCE = DOCS / "tactile_worlds_research_pitch_12_slides.md"
OUTPUT = DOCS / "ruihan_gao_partnership_pitch.html"
ASSETS = DOCS / "presentation_assets"
SLIDE_COUNT = 12


def inline(value: str) -> str:
    value = html.escape(value, quote=False)
    value = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: '<a href="' + html.escape(html.unescape(m[2]), quote=True)
        + '" target="_blank" rel="noopener noreferrer">' + m[1] + "</a>",
        value,
    )
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    return value


def markdown(value: str) -> str:
    blocks = []
    for block in re.split(r"\n\s*\n", value.strip()):
        lines = block.strip().splitlines()
        if not lines:
            continue
        if lines[0].startswith("|"):
            rows = [[cell.strip() for cell in line.strip().strip("|").split("|")]
                    for line in lines if not re.match(r"^\|[\s:|\-]+\|$", line)]
            if not rows:
                continue
            head = "".join("<th scope=\"col\">" + inline(cell) + "</th>" for cell in rows[0])
            body = "".join("<tr>" + "".join("<td>" + inline(cell) + "</td>" for cell in row) + "</tr>"
                           for row in rows[1:])
            blocks.append("<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>")
        elif all(line.startswith("- ") for line in lines):
            blocks.append("<ul>" + "".join("<li>" + inline(line[2:]) + "</li>" for line in lines) + "</ul>")
        elif all(re.match(r"^\d+\. ", line) for line in lines):
            blocks.append("<ol>" + "".join("<li>" + inline(re.sub(r"^\d+\. ", "", line)) + "</li>" for line in lines) + "</ol>")
        else:
            blocks.append("<p>" + inline(" ".join(lines)) + "</p>")
    return "\n".join(blocks)


def data_uri(filename: str) -> str:
    path = ASSETS / filename
    if not path.is_file():
        raise FileNotFoundError(path)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return "data:" + mime + ";base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def figure(filename: str, caption: str, alt: str, *, cover: bool = False) -> str:
    mode = " cover" if cover else ""
    return ('<figure class="visual' + mode + '"><button class="image-zoom" type="button" '
            'aria-label="Enlarge image: ' + html.escape(alt, quote=True) + '"><img src="'
            + data_uri(filename) + '" alt="' + html.escape(alt, quote=True)
            + '" draggable="false"></button><figcaption>' + inline(caption) + '</figcaption></figure>')


def read_slides() -> list[dict[str, str | int]]:
    text = SOURCE.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^## Slide (\d+) — (.+)$", text, flags=re.M))
    if len(matches) != SLIDE_COUNT:
        raise ValueError(f"The source must contain exactly {SLIDE_COUNT} slides")
    slides = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else text.index("\n---\n", match.end())
        chunk = text[match.end():end]
        fields = {}
        labels = ("Purpose", "Status on slide", "On-slide text", "Reference footer", "Speaker notes")
        next_field = "|".join(re.escape(label) for label in labels)
        for label in labels:
            field = re.search(r"\*\*" + re.escape(label) + r":\*\*\s*(.*?)(?=\n\*\*(?:" + next_field + r"):\*\*|\Z)", chunk, flags=re.S)
            fields[label] = field[1].strip() if field else ""
        slides.append({
            "number": int(match[1]), "title": match[2], "status": fields["Status on slide"],
            "body": markdown(fields["On-slide text"]), "notes": markdown(fields["Speaker notes"]),
            "references": inline(fields["Reference footer"]), "purpose": fields["Purpose"],
        })
    if [slide["number"] for slide in slides] != list(range(1, SLIDE_COUNT + 1)):
        raise ValueError("Slide numbering must be sequential")
    return slides


def paper_library() -> tuple[str, int]:
    catalog = json.loads((DOCS / "paper_dictionary.json").read_text(encoding="utf-8"))
    extra = [
        {"title": "Tactile DreamFusion: Exploiting Tactile Sensing for 3D Generation", "source_url": "https://arxiv.org/abs/2412.06785", "publication": "NeurIPS 2024", "role": "Spatial and regional tactile-guided 3D texture generation"},
        {"title": "Controllable Visual-Tactile Synthesis", "source_url": "https://arxiv.org/abs/2305.03051", "publication": "ICCV 2023", "role": "Aligned generated visual/tactile content and haptic rendering"},
        {"title": "PAT3D: Physics-Augmented Text-to-3D Scene Generation", "source_url": "https://arxiv.org/abs/2511.21978", "publication": "ICLR 2026", "role": "Physics-assisted, simulation-ready scene arrangement"},
    ]
    def entry(paper: dict[str, str]) -> str:
        label = html.escape(paper["title"])
        link = html.escape(paper["source_url"], quote=True)
        publication = html.escape(paper["publication"])
        role = html.escape(paper.get("role", paper.get("prediction_or_output", "")))
        return f'<li><a href="{link}" target="_blank" rel="noopener noreferrer">{label}</a><div class="paper-status">{publication}</div><p>{role}</p></li>'
    papers = list(catalog["papers"].values())
    groups = ['<h3>Texture generation and scene construction</h3><ul class="paper-list">' + "".join(entry(paper) for paper in extra) + '</ul>']
    for category in catalog["categories"]:
        items = sorted((paper for paper in papers if paper["category"] == category["id"]), key=lambda paper: (paper["year"], paper["title"]))
        groups.append('<h3>' + html.escape(category["title"]) + '</h3><ul class="paper-list">' + "".join(entry(paper) for paper in items) + '</ul>')
    return "".join(groups), len(papers) + len(extra)


CSS = r"""
:root{--paper:#f8f7f2;--ink:#23332d;--muted:#66736b;--accent:#a75032;--line:#d7dcd3;--scale:1;color-scheme:light}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden}
body{background:#202823;font-family:'Segoe UI',Arial,sans-serif;color:var(--ink)}
button,a{-webkit-tap-highlight-color:transparent}button{font:inherit}button:focus-visible,a:focus-visible{outline:3px solid #d99369;outline-offset:4px}
.deck-shell{position:relative;width:100%;height:calc(100% - 56px);overflow:hidden}
#stage{position:absolute;left:50%;top:50%;width:1600px;height:900px;transform:translate(-50%,-50%) scale(var(--scale));transform-origin:center center}
.slide{position:absolute;inset:0;display:none;flex-direction:column;padding:56px 76px 38px;background:var(--paper);overflow:hidden}
.slide.active{display:flex}.slide h1{font-size:56px;line-height:1.08;font-weight:650;letter-spacing:-1.7px;margin:0 0 34px;max-width:1450px}
.status{font-size:20px;line-height:1.25;letter-spacing:.5px;color:var(--accent);margin:0 0 16px;font-weight:600}
.main{display:flex;gap:48px;flex:1;min-height:0;align-items:center}.copy{flex:1;min-width:0;font-size:28px;line-height:1.35}
.copy p{margin:0 0 22px}.copy p:last-child{margin-bottom:0}.copy strong{font-weight:650}.copy ul,.copy ol{padding-left:28px;margin:0 0 26px}
.copy li{padding-left:4px;margin-bottom:17px}.copy li::marker{color:var(--accent)}
table{width:100%;border-collapse:collapse;margin:8px 0 26px;table-layout:fixed;font-size:28px;line-height:1.28}
th{text-align:left;font-size:20px;font-weight:600;color:var(--muted);padding:0 12px 14px 0;border-bottom:2px solid var(--ink)}
td{vertical-align:top;padding:21px 16px 21px 0;border-bottom:1px solid var(--line)}td:first-child{font-weight:600}th:first-child,td:first-child{width:36%}
a{color:inherit;text-decoration:underline;text-decoration-color:#abb7ad;text-underline-offset:3px}
.media{width:46%;flex:0 0 46%;min-width:0;display:flex;flex-direction:column;gap:28px;justify-content:center;max-height:100%}
.visual{margin:0;min-height:0;display:flex;flex-direction:column}.image-zoom{appearance:none;padding:0;border:0;background:transparent;display:block;width:100%;cursor:zoom-in;line-height:0;min-height:0}
.visual img{display:block;width:100%;height:auto;max-height:495px;object-fit:contain}.visual figcaption{font-size:17px;line-height:1.35;color:var(--muted);margin-top:13px;max-width:100%}
.image-zoom{flex-shrink:0}.visual.cover img{height:540px;max-height:540px;object-fit:cover;object-position:40% center}
.slide-footer{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding-top:23px;margin-top:24px;min-height:42px}
.references{font-size:16px;line-height:1.5;color:var(--muted);max-width:1330px}.references:empty{display:none}.page-number{font-size:19px;letter-spacing:2px;color:var(--muted);white-space:nowrap;margin-left:auto}
.s1 h1{font-size:66px;margin-bottom:30px}.s1 .copy{font-size:30px;line-height:1.4;flex:0 0 39%}.s1 .copy p:first-child{font-size:40px;line-height:1.17;margin-bottom:30px}.s1 .media{width:57%;flex-basis:57%}.s1 .copy p:last-child{font-size:28px;padding-top:10px}
.s2 .copy{max-width:1435px;font-size:29px}.s2 .copy p:first-child{font-size:40px}.s2 table{font-size:30px}.s2 td{padding-top:22px;padding-bottom:22px}.s2 .copy p:last-child{color:var(--accent);font-size:29px}
.s3 .copy,.s5 .copy,.s6 .copy{max-width:1435px;font-size:28px}.s3 table,.s5 table,.s6 table{font-size:28px}.s3 td,.s5 td,.s6 td{padding-top:16px;padding-bottom:16px}.s3 th:first-child,.s3 td:first-child,.s5 th:first-child,.s5 td:first-child{width:29%}.s6 th:first-child,.s6 td:first-child{width:30%}.s3 .copy p,.s5 .copy p,.s6 .copy p{margin-bottom:16px}.s3 .copy p:last-child,.s5 .copy p:last-child,.s6 .copy p:last-child{font-size:26px;color:var(--accent)}.s3 .references,.s4 .references,.s5 .references,.s6 .references{font-size:15px}.s5 table{font-size:27px;margin-bottom:20px}.s5 td{padding-top:13px;padding-bottom:13px}
.s4 .copy{font-size:28px;line-height:1.36}.s4 .copy p{margin-bottom:23px}.s4 .copy p:last-child{font-size:26px;color:var(--accent)}.s4 .media{width:46%;flex-basis:46%;gap:25px}.s4 .visual img{max-height:250px}.s4 .visual figcaption{font-size:16px;margin-top:8px}
.s7 .copy{max-width:1435px;font-size:29px}.s7 .copy p:first-child{font-size:39px;line-height:1.18;margin-bottom:25px}.s7 table{font-size:28px}.s7 td{padding-top:17px;padding-bottom:17px}.s7 th:first-child,.s7 td:first-child{width:32%}.s7 .copy p:last-child{font-size:29px;color:var(--accent)}.s7 .references{font-size:15px}
.s8 .copy{font-size:26px;line-height:1.32}.s8 table{font-size:26px}.s8 td{padding-top:17px;padding-bottom:17px}.s8 th:first-child,.s8 td:first-child{width:29%}.s8 .copy p:first-child{font-size:30px;line-height:1.25}.s8 .copy p:last-child{font-size:26px;color:var(--accent)}.s8 .media{width:39%;flex-basis:39%}.s8 .visual figcaption{font-size:18px}.s8 .references{font-size:15px}
.s9 .copy{font-size:26px;flex:0 0 35%;line-height:1.35}.s9 .copy p:first-child{font-size:30px;line-height:1.25}.s9 .copy li{margin-bottom:18px}.s9 .copy p:last-child{font-size:26px;color:var(--accent)}.s9 .media{width:62%;flex-basis:62%}.s9 .visual img{max-height:500px}.s9 .visual figcaption{font-size:18px;line-height:1.4}.s9 .references{font-size:16px}
.s10 .copy{font-size:27px;line-height:1.32}.s10 .copy p:first-child{font-size:32px;line-height:1.22}.s10 .copy p{margin-bottom:20px}.s10 .copy li{margin-bottom:14px}.s10 .copy ul{margin-bottom:22px}.s10 .copy p:last-child{font-size:27px;color:var(--accent)}.s10 .media{width:43%;flex-basis:43%}.s10 .visual figcaption{font-size:18px}.s10 .references{font-size:15px}
.s11 .copy{font-size:28px;max-width:1435px}.s11 .copy p:first-child{font-size:37px;margin-bottom:25px}.s11 table{font-size:29px}.s11 td{padding-top:16px;padding-bottom:16px}.s11 th:first-child,.s11 td:first-child{width:27%}.s11 .copy p:last-child{font-size:27px;color:var(--accent)}.s11 .references{font-size:15px}
.s12{background:#18382e;color:#f4f6ed}.s12 .status{color:#dfba94}.s12 h1{font-size:58px}.s12 .copy{font-size:28px;max-width:1435px}.s12 .copy p:first-child{font-size:42px;line-height:1.16;margin-bottom:28px}.s12 table{font-size:28px;margin-bottom:23px}.s12 th{color:#c1d8c9;border-color:#c1d8c9}.s12 td{padding-top:17px;padding-bottom:17px;border-color:#577265}.s12 th:first-child,.s12 td:first-child{width:40%}.s12 .copy p{margin-bottom:20px}.s12 .copy p:last-child{font-size:27px;color:#c1d8c9;margin-top:25px}.s12 .page-number,.s12 .references{color:#c1d8c9}
.toolbar{height:56px;position:fixed;bottom:0;left:0;right:0;background:#202823;color:#e6ebe4;display:flex;align-items:center;justify-content:space-between;padding:0 24px;font-size:14px;gap:15px}
.toolbar-group{display:flex;align-items:center;gap:7px}.toolbar button{color:inherit;background:transparent;border:1px solid transparent;padding:8px 11px;cursor:pointer;border-radius:3px}
.toolbar button{white-space:nowrap}.toolbar button:hover{background:#35453b}.toolbar button:disabled{opacity:.35;cursor:default}.toolbar .counter{font-variant-numeric:tabular-nums;min-width:52px;text-align:center}.hint{color:#acb9af}.progress{position:fixed;bottom:56px;left:0;height:3px;background:#b6774f;width:0;transition:width .18s}
dialog{border:0;padding:0;max-width:none;max-height:none;color:var(--ink);background:var(--paper)}dialog::backdrop{background:#14241ce8}.dialog-top{display:flex;justify-content:space-between;align-items:center;padding:19px 26px;border-bottom:1px solid var(--line);gap:20px}.dialog-top button{border:0;background:transparent;font:inherit;cursor:pointer;padding:8px 12px;color:var(--ink)}
#zoom-dialog{width:min(96vw,1720px);max-height:95vh}#zoom-img{width:100%;max-height:calc(92vh - 145px);object-fit:contain;display:block;background:white}#zoom-caption{font-size:16px;line-height:1.4;padding:0 25px 20px;margin:15px 0 0}
#overview-dialog{width:min(92vw,1000px);max-height:88vh}.overview-list{display:grid;grid-template-columns:1fr 1fr;gap:0;padding:18px 26px;overflow:auto;max-height:calc(88vh - 75px)}.overview-list button{border:0;border-bottom:1px solid var(--line);padding:18px 20px 18px 0;margin-right:22px;display:flex;gap:14px;text-align:left;background:transparent;cursor:pointer;font-size:18px;line-height:1.3;color:var(--ink)}.overview-list button:hover{color:var(--accent)}.overview-list span{color:var(--accent);font-variant-numeric:tabular-nums}
#notes-dialog{width:min(92vw,920px);max-height:90vh}.notes-content{padding:25px 30px;overflow:auto;max-height:calc(90vh - 140px);font-size:21px;line-height:1.65}.notes-content h2{font-size:30px;line-height:1.25;margin:10px 0 24px}.notes-content .notes-status{font-size:15px;color:var(--accent)}.notes-content .notes-sources{font-size:14px;line-height:1.6;color:var(--muted);margin-top:28px}.notes-controls{padding:12px 25px 20px;display:flex;gap:8px}.notes-controls button{border:1px solid var(--line);background:none;color:var(--ink);font:inherit;padding:9px 13px;cursor:pointer}
#papers-dialog{width:min(94vw,1180px);max-height:92vh}.paper-content{padding:24px 35px;overflow:auto;max-height:calc(92vh - 80px);font-size:18px;line-height:1.5}.paper-content h3{font-size:26px;margin:35px 0 14px;color:var(--accent)}.paper-content>p{margin:0 0 15px;color:var(--muted)}.paper-list{list-style:none;margin:0;padding:0}.paper-list li{padding:16px 0;border-bottom:1px solid var(--line)}.paper-list a{font-size:20px;font-weight:600}.paper-list p{margin:7px 0 0;font-size:17px}.paper-status{font-size:14px;color:var(--muted);margin-top:5px}
.toast{position:fixed;top:18px;left:50%;transform:translateX(-50%);background:var(--paper);padding:12px 20px;font-size:15px;border:1px solid var(--line);display:none;z-index:20}.toast.show{display:block}
@media(max-width:750px){.toolbar{padding:0 8px}.toolbar .hint{display:none}.toolbar button{padding:8px}.overview-list{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){.progress{transition:none}}
@page{size:1600px 900px;margin:0}
@media print{html,body{height:auto!important;overflow:visible!important;background:white}.toolbar,.progress,dialog,.toast{display:none!important}.deck-shell{height:auto!important;overflow:visible!important}#stage{position:static;transform:none!important;width:1600px;height:auto}.slide{position:relative;display:flex!important;width:1600px;height:900px;break-after:page;page-break-after:always;print-color-adjust:exact;-webkit-print-color-adjust:exact}.slide:last-child{break-after:auto;page-break-after:auto}.image-zoom{cursor:default}a{text-decoration:none}}
"""


JAVASCRIPT = r"""
const data = __DECK_DATA__;
const slides = [...document.querySelectorAll('.slide')];
let current = 0;
let notesWindow = null;
const stage = document.getElementById('stage');
const shell = document.querySelector('.deck-shell');
const overview = document.getElementById('overview-dialog');
const zoom = document.getElementById('zoom-dialog');
const notesDialog = document.getElementById('notes-dialog');
const papersDialog = document.getElementById('papers-dialog');
const toast = document.getElementById('toast');
function fit(){const scale=Math.min(shell.clientWidth/1600,shell.clientHeight/900);document.documentElement.style.setProperty('--scale',scale);}
function message(text){toast.textContent=text;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),3800);}
function updateNotes(){
  document.getElementById('inline-notes-title').textContent=data[current].title;
  document.getElementById('inline-notes-status').textContent=`${current+1} / ${slides.length} — ${data[current].status}`;
  document.getElementById('inline-notes-body').innerHTML=data[current].notes;
  document.getElementById('inline-notes-sources').innerHTML=data[current].references||'';
  if(!notesWindow || notesWindow.closed)return;
  const d=notesWindow.document;
  d.getElementById('number').textContent=`${current+1} / ${slides.length}`;
  d.getElementById('status').textContent=data[current].status;
  d.getElementById('title').textContent=data[current].title;
  d.getElementById('notes').innerHTML=data[current].notes;
  d.getElementById('sources').innerHTML=data[current].references||'';
  d.getElementById('next').textContent=current+1<slides.length?data[current+1].title:'Discussion';
}
function show(index){
  current=Math.max(0,Math.min(slides.length-1,index));
  slides.forEach((s,i)=>{s.classList.toggle('active',i===current);s.setAttribute('aria-hidden',String(i!==current));s.inert=i!==current;});
  document.getElementById('counter').textContent=`${current+1} / ${slides.length}`;
  document.getElementById('previous').disabled=current===0;
  document.getElementById('next-slide').disabled=current===slides.length-1;
  document.querySelector('.progress').style.width=`${(current+1)/slides.length*100}%`;
  document.title=`${current+1}/${slides.length} — ${data[current].title}`;
  try{history.replaceState(null,'',`#slide-${current+1}`);}catch(e){}
  updateNotes();
}
function openNotes(){
  if(notesWindow&&!notesWindow.closed){notesWindow.focus();updateNotes();return;}
  notesWindow=window.open('','tactile-worlds-speaker-notes','width=760,height=850');
  if(!notesWindow){message('Allow pop-ups for this file, then select Notes again.');return;}
  notesWindow.document.open();
  notesWindow.document.write(`<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Tactile Worlds — Speaker Notes</title><style>
  *{box-sizing:border-box}body{margin:0;padding:30px;background:#f8f7f2;color:#23332d;font:19px/1.6 'Segoe UI',Arial,sans-serif}header{display:flex;justify-content:space-between;border-bottom:1px solid #d7dcd3;padding-bottom:14px;margin-bottom:23px}h1{font-size:30px;line-height:1.2;margin:9px 0 24px}#status{font-size:14px;color:#a75032}#notes{font-size:22px}#sources{font-size:13px;color:#66736b;margin-top:24px}a{color:inherit}footer{margin-top:35px;padding-top:18px;border-top:1px solid #d7dcd3;font-size:15px}button{font:inherit;background:none;border:1px solid #d7dcd3;padding:8px 16px;color:#23332d;cursor:pointer;margin:0 8px 0 0}small{color:#66736b}#next{font-size:18px;margin:5px 0 22px}</style></head><body><header><span>Speaker notes</span><span id="number"></span></header><div id="status"></div><h1 id="title"></h1><main id="notes"></main><div id="sources"></div><footer><small>Next slide</small><div id="next"></div><button id="back">Previous</button><button id="forward">Next</button><p><small>This separate window follows the presentation. Move it to your presenter screen.</small></p></footer></body></html>`);
  notesWindow.document.close();
  notesWindow.document.getElementById('back').addEventListener('click',()=>show(current-1));
  notesWindow.document.getElementById('forward').addEventListener('click',()=>show(current+1));
  notesWindow.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='PageDown'){e.preventDefault();show(current+1);}if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();show(current-1);}});
  updateNotes();
}
async function fullscreen(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch(e){message('Use your browser’s fullscreen command if fullscreen is unavailable.');}}
document.getElementById('previous').addEventListener('click',()=>show(current-1));
document.getElementById('next-slide').addEventListener('click',()=>show(current+1));
document.getElementById('notes-button').addEventListener('click',()=>{updateNotes();notesDialog.showModal();});
document.getElementById('notes-popup').addEventListener('click',openNotes);
document.getElementById('notes-previous').addEventListener('click',()=>show(current-1));
document.getElementById('notes-next').addEventListener('click',()=>show(current+1));
document.getElementById('fullscreen-button').addEventListener('click',fullscreen);
document.getElementById('print-button').addEventListener('click',()=>window.print());
document.getElementById('overview-button').addEventListener('click',()=>overview.showModal());
document.getElementById('papers-button').addEventListener('click',()=>papersDialog.showModal());
document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>b.closest('dialog').close()));
document.querySelectorAll('[data-slide-index]').forEach(b=>b.addEventListener('click',()=>{show(Number(b.dataset.slideIndex));overview.close();}));
document.querySelectorAll('.image-zoom').forEach(b=>b.addEventListener('click',()=>{const img=b.querySelector('img');const target=document.getElementById('zoom-img');target.src=img.src;target.alt=img.alt;document.getElementById('zoom-caption').textContent=b.closest('figure').querySelector('figcaption').textContent;zoom.showModal();}));
document.addEventListener('keydown',e=>{
  if(e.target.matches('input,textarea,select')||e.target.isContentEditable)return;
  if(papersDialog.open){if(e.key.toLowerCase()==='r'){e.preventDefault();papersDialog.close();}return;}
  if(overview.open||zoom.open)return;
  if(notesDialog.open){if(e.key.toLowerCase()==='n'){e.preventDefault();notesDialog.close();}else if(e.key==='ArrowRight'){e.preventDefault();show(current+1);}else if(e.key==='ArrowLeft'){e.preventDefault();show(current-1);}return;}
  if(['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)){e.preventDefault();show(current+1);}
  else if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();show(current-1);}
  else if(e.key==='Home'){e.preventDefault();show(0);}
  else if(e.key==='End'){e.preventDefault();show(slides.length-1);}
  else if(e.key.toLowerCase()==='n'){e.preventDefault();updateNotes();notesDialog.showModal();}
  else if(e.key.toLowerCase()==='f'){e.preventDefault();fullscreen();}
  else if(e.key.toLowerCase()==='o'){e.preventDefault();overview.showModal();}
  else if(e.key.toLowerCase()==='r'){e.preventDefault();papersDialog.showModal();}
});
window.addEventListener('resize',fit);
window.addEventListener('hashchange',()=>{const n=Number(location.hash.replace('#slide-',''));if(Number.isInteger(n)&&n>=1&&n<=slides.length)show(n-1);});
const initial=Number(location.hash.replace('#slide-',''));
show(Number.isInteger(initial)&&initial>=1&&initial<=slides.length?initial-1:0);fit();
"""


def main() -> None:
    slides = read_slides()
    bibliography, paper_count = paper_library()
    media = {
        1: figure("01-tactile-room-vision.png", "AI-generated concept illustration. Proposed system.", "Conceptual tactile room with a robot probe and varied material surfaces", cover=True),
        4: figure("papers/tactile_dreamfusion_figure1.png", "Gao et al., Tactile DreamFusion, NeurIPS 2024, Fig. 1.", "Tactile DreamFusion texture generation examples")
        + figure("papers/pat3d_project_teaser.png", "Lin et al., PAT3D, ICLR 2026. Official scene-generation teaser.", "PAT3D simulation-ready scene examples"),
        9: figure("05-existing-development-results.png", "Saved development comparison: two repeatedly exposed specimens; mean log10 band-power MAE, lower is better. Training-condition coverage differs.", "Matched development chart comparing retrieval, fixed features and encoder in both orientations"),
        8: figure("06-tactile-surface-asset.png", "AI-generated concept illustration. Proposed surface asset.", "Conceptual surface atlas with ceramic, rubber and rough base regions"),
        10: figure("07-proposed-sliding-experiment.png", "AI-generated concept illustration. Proposed setup; acquisition feasibility unresolved.", "Proposed prescribed sliding experiment with independent force measurement"),
    }
    sections = []
    for slide in slides:
        n = slide["number"]
        visual = '<aside class="media">' + media[n] + '</aside>' if n in media else ""
        sections.append(f'''<section class="slide s{n}" id="slide-{n}" aria-labelledby="title-{n}" aria-hidden="true">
<header><p class="status">{html.escape(str(slide['status']))}</p><h1 id="title-{n}">{html.escape(str(slide['title']))}</h1></header>
<div class="main"><div class="copy">{slide['body']}</div>{visual}</div>
<footer class="slide-footer"><div class="references">{slide['references']}</div><div class="page-number">{n:02d} / {SLIDE_COUNT}</div></footer>
</section>''')
    overview = "".join('<button type="button" data-slide-index="' + str(slide["number"] - 1) + '"><span>'
                       + str(slide["number"]).zfill(2) + '</span>' + html.escape(str(slide["title"])) + '</button>' for slide in slides)
    data = json.dumps([{key: slide[key] for key in ("title", "status", "notes", "references")} for slide in slides], ensure_ascii=False).replace("</", "<\\/")
    script = JAVASCRIPT.replace("__DECK_DATA__", data)
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="A 12-slide scientific pitch for tactile worlds: the ultimate goal, existing research capabilities, gap, proposed system, evidence and research plan.">
<title>Tactile Worlds — Scientific Pitch</title><style>{CSS}</style></head><body>
<main class="deck-shell" aria-label="Tactile Worlds presentation"><div id="stage">{''.join(sections)}</div></main>
<div class="progress" aria-hidden="true"></div>
<nav class="toolbar" aria-label="Presentation controls"><div class="toolbar-group"><button id="previous" type="button" title="Previous slide (Left arrow)">Previous</button><span id="counter" class="counter" aria-live="polite"></span><button id="next-slide" type="button" title="Next slide (Right arrow)">Next</button></div><span class="hint">Arrows navigate · N notes · R papers · O overview · F fullscreen</span><div class="toolbar-group"><button id="overview-button" type="button">Overview</button><button id="notes-button" type="button">Notes</button><button id="papers-button" type="button" title="Full paper library (R)">Papers</button><button id="print-button" type="button">Print / PDF</button><button id="fullscreen-button" type="button">Fullscreen</button></div></nav>
<dialog id="zoom-dialog" aria-label="Enlarged figure"><div class="dialog-top"><strong>Figure</strong><button type="button" data-close>Close</button></div><img id="zoom-img" alt=""><p id="zoom-caption"></p></dialog>
<dialog id="overview-dialog" aria-labelledby="overview-title"><div class="dialog-top"><strong id="overview-title">{SLIDE_COUNT}-slide overview</strong><button type="button" data-close>Close</button></div><div class="overview-list">{overview}</div></dialog>
<dialog id="notes-dialog" aria-labelledby="inline-notes-title"><div class="dialog-top"><strong>Speaker notes</strong><button type="button" data-close>Close</button></div><div class="notes-content"><div id="inline-notes-status" class="notes-status"></div><h2 id="inline-notes-title"></h2><div id="inline-notes-body"></div><div id="inline-notes-sources" class="notes-sources"></div></div><div class="notes-controls"><button id="notes-previous" type="button">Previous slide</button><button id="notes-next" type="button">Next slide</button><button id="notes-popup" type="button">Open separate window</button></div></dialog>
<dialog id="papers-dialog" aria-labelledby="papers-title"><div class="dialog-top"><strong id="papers-title">Paper library · {paper_count} entries</strong><button type="button" data-close>Close</button></div><div class="paper-content"><p>The existing 99-paper research catalog plus three texture/scene references. Curated coverage, with reported outputs and publication status; this is supporting material for the 12 slides.</p><p>Catalog reviewed 11 October 2026. Slide preparation: 12 October 2026. Preprints and broader abstract/metadata reviews are included. Source links open the primary paper or author resource. <a href="paper_dictionary.md" target="_blank" rel="noopener noreferrer">Detailed evidence, limits and review depth</a>.</p>{bibliography}</div></dialog>
<div id="toast" class="toast" role="status"></div><script>{script}</script></body></html>'''
    OUTPUT.write_text(document, encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "slides": len(slides), "bytes": OUTPUT.stat().st_size,
                      "embedded_visuals": sum(fragment.count("<figure") for fragment in media.values()), "paper_library_entries": paper_count}))


if __name__ == "__main__":
    main()
