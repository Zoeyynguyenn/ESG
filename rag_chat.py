# -*- coding: utf-8 -*-
"""
RAG Chatbot — Ollama + ChromaDB + Rich UI
  /ingest <file>  - Nap PDF/TXT vao vector store
  /docs           - Liet ke tai lieu da nap
  /deldoc <ten>   - Xoa tai lieu khoi vector store
  /rag on|off     - Bat/tat RAG (mac dinh: on)
  /save [ten]     - Luu lich su chat
  /load           - Tai lich su cu
  /sessions       - Liet ke sessions
  /history        - Xem lich su hoi thoai hien tai
  /clear          - Xoa lich su
  /model          - Doi model
  /help           - Tro giup
  /exit           - Thoat
"""
import sys, io, os, json, datetime

def _setup_utf8():
    """Chỉ gọi khi chạy trực tiếp, không khi import (tránh phá pytest)."""
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import ollama
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.rule import Rule
from rich.columns import Columns
from rich import box

from rag_engine import RagEngine

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_MODEL = "llama3.2:3b"
HISTORY_DIR   = os.path.join(os.path.dirname(__file__), "chat_history")
BASE_SYSTEM   = (
    "Ban la mot tro ly AI chuyen ve ESG va phat trien ben vung. "
    "Tra loi bang tieng Viet tru khi nguoi dung hoi bang tieng Anh. "
    "Su dung Markdown de dinh dang ro rang. "
    "Neu duoc cung cap TAI LIEU THAM KHAO, hay uu tien dung thong tin tu tai lieu do, "
    "va neu ro ban lay tu tai lieu nao."
)

console = Console(highlight=False, force_terminal=True)
os.makedirs(HISTORY_DIR, exist_ok=True)


# ════════════════════════════════════════════════════════════════════════════════
# UI helpers
# ════════════════════════════════════════════════════════════════════════════════

def print_banner(model: str, rag_on: bool, n_docs: int):
    rag_label = (
        Text("ON", style="green bold") if rag_on
        else Text("OFF", style="red bold")
    )
    doc_label = Text(f"{n_docs} tai lieu", style="yellow")
    console.print()
    console.print(Panel.fit(
        Text.assemble(
            ("  RAG Chatbot  (Ollama + ChromaDB)\n", "bold cyan"),
            ("  Model : ", "dim"), (f"{model}\n", "green bold"),
            ("  RAG   : ", "dim"), rag_label, ("\n", ""),
            ("  Docs  : ", "dim"), doc_label, ("\n", ""),
            ("  Go /help de xem lenh", "dim italic"),
        ),
        border_style="cyan", padding=(0, 2),
    ))
    console.print()


def print_help():
    table = Table(show_header=True, header_style="bold magenta",
                  box=box.ROUNDED, border_style="magenta", padding=(0,1))
    table.add_column("Lenh",       style="cyan bold", no_wrap=True)
    table.add_column("Chuc nang",  style="white")
    rows = [
        ("/ingest <duong-dan>", "Nap PDF hoac TXT vao vector store"),
        ("/docs",               "Liet ke tai lieu da nap"),
        ("/deldoc <ten-file>",  "Xoa tai lieu khoi vector store"),
        ("/rag on|off",         "Bat / tat RAG (mac dinh: on)"),
        ("/history",            "Xem lich su hoi thoai hien tai"),
        ("/save [ten]",         "Luu session ra JSON"),
        ("/load",               "Tai session cu"),
        ("/sessions",           "Liet ke tat ca session"),
        ("/clear",              "Xoa lich su, bat dau moi"),
        ("/model",              "Doi model Ollama"),
        ("/help",               "Hien thi bang nay"),
        ("/exit",               "Thoat chuong trinh"),
    ]
    for cmd, desc in rows:
        table.add_row(cmd, desc)
    console.print(); console.print(table); console.print()


def print_docs(rag: RagEngine):
    sources = rag.list_sources()
    console.print()
    if not sources:
        console.print(Panel(
            "[dim]Chua co tai lieu nao.\nDung [cyan]/ingest <duong-dan>[/cyan] de nap.[/dim]",
            title="Tai lieu", border_style="yellow"))
        console.print(); return

    table = Table(show_header=True, header_style="bold yellow",
                  box=box.ROUNDED, border_style="yellow", padding=(0,1))
    table.add_column("#",        style="dim",       width=3)
    table.add_column("File",     style="cyan bold", width=30)
    table.add_column("Chunks",   style="magenta",   width=8)
    for i, s in enumerate(sources, 1):
        table.add_row(str(i), s["source"], str(s["chunks"]))
    console.print(table)
    console.print(f"  [dim]Tong: {rag.count()} chunks trong vector store[/dim]\n")


def print_history(history: list):
    msgs = [m for m in history if m["role"] != "system"]
    console.print()
    if not msgs:
        console.print(Panel("[dim]Chua co tin nhan nao.[/dim]",
                            title="Lich su", border_style="yellow"))
        console.print(); return

    table = Table(show_header=True, header_style="bold yellow",
                  box=box.SIMPLE_HEAVY, border_style="yellow", expand=True)
    table.add_column("#",        style="dim",  width=3,  no_wrap=True)
    table.add_column("Vai tro",  style="bold", width=6,  no_wrap=True)
    table.add_column("Noi dung", ratio=1)
    for i, m in enumerate(msgs, 1):
        label = Text("Ban", style="green bold") if m["role"]=="user" else Text("AI ", style="cyan bold")
        snippet = m["content"].replace("\n"," ")[:120]
        if len(m["content"]) > 120: snippet += "..."
        table.add_row(str(i), label, snippet)
    console.print(table); console.print()


# ── Session save / load ───────────────────────────────────────────────────────

def _spath(name): return os.path.join(HISTORY_DIR, name.replace(" ","_")+".json")

def save_session(history, model, name=None):
    if not name:
        name = "rag_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(_spath(name), "w", encoding="utf-8") as f:
        json.dump({"saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
                   "model": model, "messages": history}, f, ensure_ascii=False, indent=2)
    return name

def load_session(name):
    p = _spath(name)
    if not os.path.exists(p): return None
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d["messages"], d.get("model", DEFAULT_MODEL)
    except (json.JSONDecodeError, KeyError, OSError):
        return None

def list_sessions():
    out = []
    for fn in os.listdir(HISTORY_DIR):
        if not fn.endswith(".json"): continue
        p = os.path.join(HISTORY_DIR, fn)
        try:
            d = json.load(open(p, encoding="utf-8"))
            turns = sum(1 for m in d.get("messages",[]) if m["role"]=="user")
            out.append({"name": fn[:-5], "saved_at": d.get("saved_at","?"),
                        "model": d.get("model","?"), "turns": turns})
        except: pass
    out.sort(key=lambda s: s["saved_at"], reverse=True)
    return out

def print_sessions():
    sessions = list_sessions()
    console.print()
    if not sessions:
        console.print(Panel("[dim]Chua co session.[/dim]", title="Sessions", border_style="yellow"))
        console.print(); return sessions
    table = Table(show_header=True, header_style="bold green",
                  box=box.ROUNDED, border_style="green", padding=(0,1))
    table.add_column("#",        style="dim",       width=3)
    table.add_column("Ten",      style="cyan bold", width=30, no_wrap=True)
    table.add_column("Luu luc",  style="white",     width=20, no_wrap=True)
    table.add_column("Model",    style="yellow",    width=14, no_wrap=True)
    table.add_column("Luot hoi", style="magenta",   width=9,  no_wrap=True)
    for i, s in enumerate(sessions, 1):
        table.add_row(str(i), s["name"], s["saved_at"].replace("T"," "),
                      s["model"], str(s["turns"]))
    console.print(table); console.print()
    return sessions

def pick_model(current):
    try: models = ollama.list().models
    except: console.print("[red]Khong the ket noi Ollama.[/red]"); return current
    if not models: return current
    table = Table(show_header=True, header_style="bold green",
                  box=box.ROUNDED, border_style="green")
    table.add_column("#", width=4, style="dim")
    table.add_column("Model", style="cyan bold")
    table.add_column("Size",  style="white")
    for i, m in enumerate(models, 1):
        size = f"{m.size/1e9:.1f} GB" if m.size else "?"
        mk   = " [green](dang dung)[/green]" if m.model == current else ""
        table.add_row(str(i), m.model+mk, size)
    console.print(); console.print(table)
    ch = Prompt.ask("  [cyan]Chon so[/cyan] (Enter=giu)", default="", console=console)
    if ch.isdigit():
        idx = int(ch)-1
        if 0 <= idx < len(models):
            console.print(f"  [green]>> Da chon:[/green] [bold]{models[idx].model}[/bold]\n")
            return models[idx].model
    console.print("  [dim]>> Giu nguyen.[/dim]\n"); return current


# ════════════════════════════════════════════════════════════════════════════════
# Streaming  +  RAG context injection
# ════════════════════════════════════════════════════════════════════════════════

def build_messages(base_history: list, question: str, rag: RagEngine, rag_on: bool) -> list:
    """
    Xay dung danh sach messages gui len LLM.
    Neu RAG on va co context, inject vao system prompt.
    """
    context = rag.query(question) if rag_on else ""

    if context:
        system_content = (
            BASE_SYSTEM
            + "\n\n=== TAI LIEU THAM KHAO ===\n\n"
            + context
            + "\n\n=== HET TAI LIEU ==="
        )
        # Thay the system prompt dau tien
        messages = [{"role": "system", "content": system_content}]
        messages += [m for m in base_history if m["role"] != "system"]
    else:
        messages = base_history.copy()

    messages.append({"role": "user", "content": question})
    return messages, bool(context)


def stream_response(model: str, messages: list, used_rag: bool) -> str:
    full_text = ""
    try:
        with console.status("[cyan]Dang suy nghi...[/cyan]", spinner="dots"):
            stream      = ollama.chat(model=model, messages=messages, stream=True)
            first_chunk = next(stream)
        full_text += first_chunk.message.content
    except StopIteration:
        console.print("[red]AI khong tra loi.[/red]"); return ""
    except ollama.ResponseError as e:
        console.print(f"[red]Loi Ollama:[/red] {e}"); return ""
    except Exception as e:
        console.print(f"[red]Loi:[/red] {e}"); return ""

    rag_badge = " [yellow][RAG][/yellow]" if used_rag else ""
    console.print(Rule(title=f"[bold cyan]  AI  [/bold cyan]{rag_badge}", style="cyan"))
    console.print()
    console.print(first_chunk.message.content, end="", style="white")
    try:
        for chunk in stream:
            tok = chunk.message.content
            full_text += tok
            console.print(tok, end="", style="white")
    except Exception as e:
        console.print(f"\n[red]Loi stream:[/red] {e}")

    console.print("\n")
    console.print(Panel(Markdown(full_text), title="[cyan]AI[/cyan]",
                        border_style="cyan", padding=(1,2)))
    console.print()
    return full_text


# ════════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════════

def main():
    model   = DEFAULT_MODEL
    rag_on  = True
    history = [{"role": "system", "content": BASE_SYSTEM}]

    console.print("\n[dim]Dang khoi dong RAG engine...[/dim]")
    rag = RagEngine()
    console.print(f"[dim]Vector store: {rag.count()} chunks | embed model: all-MiniLM-L6-v2[/dim]")

    print_banner(model, rag_on, len(rag.list_sources()))

    while True:
        try:
            user_input = Prompt.ask(
                Text.assemble(("  Ban", "green bold")), console=console
            ).strip()
        except (EOFError, KeyboardInterrupt):
            user_input = "/exit"

        if not user_input:
            continue

        # ── Commands ────────────────────────────────────────────────────────
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd   = parts[0].lower()
            arg   = parts[1].strip() if len(parts) > 1 else ""

            # /exit
            if cmd == "/exit":
                has = any(m["role"]=="user" for m in history)
                if has:
                    try: do_save = Confirm.ask("\n  [yellow]Luu session?[/yellow]", console=console)
                    except: do_save = False
                    if do_save:
                        name = save_session(history, model)
                        console.print(Panel(f"[green]Da luu:[/green] [bold]{name}.json[/bold]",
                                            border_style="green", padding=(0,2)))
                console.print(Panel("[cyan]Tam biet![/cyan]", border_style="cyan", padding=(0,2)))
                break

            # /help
            elif cmd == "/help":
                print_help()

            # /clear
            elif cmd == "/clear":
                history = [{"role": "system", "content": BASE_SYSTEM}]
                console.print(Panel("[green]Da xoa lich su![/green]",
                                    border_style="green", padding=(0,2)))
                console.print()

            # /history
            elif cmd == "/history":
                print_history(history)

            # /ingest <file>
            elif cmd == "/ingest":
                if not arg:
                    console.print("  [red]Thieu duong dan. Vi du: /ingest report.pdf[/red]\n")
                else:
                    fpath = arg.strip('"').strip("'")
                    if not os.path.exists(fpath):
                        console.print(f"  [red]Khong tim thay file: {fpath}[/red]\n")
                    else:
                        with console.status(f"[cyan]Dang nap {os.path.basename(fpath)}...[/cyan]",
                                            spinner="dots"):
                            result = rag.ingest(fpath)
                        console.print(Panel(
                            f"[green]Nap thanh cong:[/green] [bold]{result['source']}[/bold]\n"
                            f"Tong chunks  : [yellow]{result['chunks']}[/yellow]\n"
                            f"Them moi     : [green]{result['added']}[/green]\n"
                            f"Da co san    : [dim]{result['skipped']}[/dim]",
                            title="[green]Ingest[/green]",
                            border_style="green", padding=(0,2),
                        ))
                        print_banner(model, rag_on, len(rag.list_sources()))

            # /docs
            elif cmd == "/docs":
                print_docs(rag)

            # /deldoc <ten>
            elif cmd == "/deldoc":
                if not arg:
                    console.print("  [red]Thieu ten file. Vi du: /deldoc report.pdf[/red]\n")
                else:
                    n = rag.delete_source(arg)
                    if n:
                        console.print(Panel(
                            f"[green]Da xoa[/green] [bold]{arg}[/bold] ({n} chunks)",
                            border_style="green", padding=(0,2)))
                        print_banner(model, rag_on, len(rag.list_sources()))
                    else:
                        console.print(f"  [yellow]Khong tim thay:[/yellow] {arg}\n")

            # /rag on|off
            elif cmd == "/rag":
                if arg.lower() == "off":
                    rag_on = False
                    console.print(Panel("[red]RAG da TAT. AI se tra loi tu kien thuc chung.[/red]",
                                        border_style="red", padding=(0,2)))
                elif arg.lower() == "on":
                    rag_on = True
                    console.print(Panel("[green]RAG da BAT. AI se tim tai lieu truoc khi tra loi.[/green]",
                                        border_style="green", padding=(0,2)))
                else:
                    st = "[green]ON[/green]" if rag_on else "[red]OFF[/red]"
                    console.print(f"  RAG hien tai: {st}. Dung /rag on hoac /rag off\n")

            # /save
            elif cmd == "/save":
                has = any(m["role"]=="user" for m in history)
                if not has:
                    console.print(Panel("[yellow]Chua co noi dung.[/yellow]",
                                        border_style="yellow", padding=(0,2)))
                else:
                    name = save_session(history, model, name=arg or None)
                    console.print(Panel(
                        f"[green]Da luu:[/green] [bold]{name}.json[/bold]\n"
                        f"[dim]{_spath(name)}[/dim]",
                        title="[green]Luu thanh cong[/green]",
                        border_style="green", padding=(0,2)))
                console.print()

            # /sessions
            elif cmd == "/sessions":
                print_sessions()

            # /load
            elif cmd == "/load":
                sessions = print_sessions()
                if not sessions: continue
                ch = Prompt.ask("  [cyan]Chon so[/cyan] (Enter=huy)", default="", console=console)
                if not ch.isdigit(): console.print("  [dim]>> Huy.[/dim]\n"); continue
                idx = int(ch)-1
                if not (0 <= idx < len(sessions)): console.print("  [red]So khong hop le.[/red]\n"); continue
                result = load_session(sessions[idx]["name"])
                if result is None: console.print("  [red]Khong the tai.[/red]\n"); continue
                history, model = result
                console.print(Panel(
                    f"[green]Da tai:[/green] [bold]{sessions[idx]['name']}[/bold]\n"
                    f"[dim]{sum(1 for m in history if m['role']=='user')} luot hoi[/dim]",
                    title="[green]Tai thanh cong[/green]", border_style="green", padding=(0,2)))
                print_banner(model, rag_on, len(rag.list_sources()))

            # /model
            elif cmd == "/model":
                model = pick_model(model)
                print_banner(model, rag_on, len(rag.list_sources()))

            else:
                console.print(f"  [red]Lenh khong hop le:[/red] {cmd} — go [cyan]/help[/cyan]\n")
            continue

        # ── Chat với RAG ─────────────────────────────────────────────────────
        console.print(Panel(user_input, title="[green]Ban[/green]",
                            border_style="green", padding=(0,1)))

        messages, used_rag = build_messages(history, user_input, rag, rag_on)

        if used_rag:
            console.print(f"  [dim yellow]RAG: tim thay tai lieu lien quan, dang inject context...[/dim yellow]")

        reply = stream_response(model, messages, used_rag)

        if reply:
            history.append({"role": "user",      "content": user_input})
            history.append({"role": "assistant",  "content": reply})


if __name__ == "__main__":
    _setup_utf8()
    main()
