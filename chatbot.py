# -*- coding: utf-8 -*-
"""
CLI Chatbot powered by Ollama + Rich UI
Features:
  - Streaming real-time + Markdown rendering
  - Spinner / Panel / Table mau sac (Rich)
  - Multi-turn conversation (nho context)
  - Luu / Load lich su JSON
  - Auto-save khi thoat
  - /help, /clear, /history, /save, /load, /sessions, /model, /exit
"""
import sys
import io
import os
import json
import datetime

# ── Force UTF-8 tren Windows ──────────────────────────────────────────────────
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import ollama
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.rule import Rule
from rich import box

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_MODEL = "llama3.2:3b"
HISTORY_DIR   = os.path.join(os.path.dirname(__file__), "chat_history")
SYSTEM_PROMPT = (
    "Ban la mot tro ly AI thong minh, chuyen ve ESG va phat trien ben vung. "
    "Tra loi bang tieng Viet tru khi nguoi dung hoi bang tieng Anh. "
    "Su dung Markdown de dinh dang cau tra loi cho ro rang."
)

console = Console(highlight=False, force_terminal=True)

# ── Ensure history folder exists ──────────────────────────────────────────────
os.makedirs(HISTORY_DIR, exist_ok=True)


# ════════════════════════════════════════════════════════════════════════════════
# JSON Save / Load
# ════════════════════════════════════════════════════════════════════════════════

def _session_path(name: str) -> str:
    """Tra ve duong dan file JSON tu ten session."""
    safe = name.replace(" ", "_").replace("/", "-")
    if not safe.endswith(".json"):
        safe += ".json"
    return os.path.join(HISTORY_DIR, safe)


def save_history(history: list, model: str, name: str | None = None) -> str:
    """
    Luu history vao JSON.
    Ten mac dinh: chat_YYYYMMDD_HHMMSS
    Tra ve ten file da luu.
    """
    if not name:
        name = "chat_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    path = _session_path(name)
    payload = {
        "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "model":    model,
        "messages": history,           # bao gom ca system prompt
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return name


def load_history(name: str) -> tuple[list, str] | None:
    """
    Doc file JSON va tra ve (history, model).
    None neu khong tim thay hoac loi.
    """
    path = _session_path(name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        return payload["messages"], payload.get("model", DEFAULT_MODEL)
    except Exception as e:
        console.print(f"[red]Loi doc file:[/red] {e}")
        return None


def list_sessions() -> list[dict]:
    """
    Liet ke tat ca session da luu, sap xep moi nhat truoc.
    Moi item: {name, saved_at, model, turns, path}
    """
    sessions = []
    for fname in os.listdir(HISTORY_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(HISTORY_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            turns = sum(1 for m in data.get("messages", [])
                        if m["role"] == "user")
            sessions.append({
                "name":     fname[:-5],          # bo .json
                "saved_at": data.get("saved_at", "?"),
                "model":    data.get("model", "?"),
                "turns":    turns,
                "path":     path,
            })
        except Exception:
            pass
    sessions.sort(key=lambda s: s["saved_at"], reverse=True)
    return sessions


# ════════════════════════════════════════════════════════════════════════════════
# UI Components
# ════════════════════════════════════════════════════════════════════════════════

def print_banner(model: str):
    console.print()
    console.print(Panel.fit(
        Text.assemble(
            ("  Ollama CLI Chatbot\n", "bold cyan"),
            ("  Model  : ",           "dim"),
            (f"{model}\n",            "green bold"),
            ("  Go /help de xem lenh","dim italic"),
        ),
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()


def print_help():
    table = Table(
        show_header=True, header_style="bold magenta",
        box=box.ROUNDED, border_style="magenta", padding=(0, 1),
    )
    table.add_column("Lenh",      style="cyan bold", no_wrap=True)
    table.add_column("Chuc nang", style="white")

    rows = [
        ("/help",           "Hien thi bang tro giup nay"),
        ("/clear",          "Xoa lich su, bat dau cuoc tro chuyen moi"),
        ("/history",        "Xem tom tat lich su hoi thoai hien tai"),
        ("/save [ten]",     "Luu session hien tai ra file JSON"),
        ("/load",           "Chon va tai lai mot session cu"),
        ("/sessions",       "Liet ke tat ca session da luu"),
        ("/model",          "Doi sang model Ollama khac"),
        ("/exit",           "Thoat (tu dong hoi luu neu co noi dung)"),
    ]
    for cmd, desc in rows:
        table.add_row(cmd, desc)

    console.print()
    console.print(table)
    console.print()


def print_history(history: list):
    msgs = [m for m in history if m["role"] != "system"]
    console.print()
    if not msgs:
        console.print(Panel("[dim]Chua co tin nhan nao.[/dim]",
                            title="Lich su", border_style="yellow"))
        console.print()
        return

    table = Table(
        show_header=True, header_style="bold yellow",
        box=box.SIMPLE_HEAVY, border_style="yellow", expand=True,
    )
    table.add_column("#",        style="dim",  width=3,  no_wrap=True)
    table.add_column("Vai tro",  style="bold", width=6,  no_wrap=True)
    table.add_column("Noi dung", ratio=1)

    for i, msg in enumerate(msgs, 1):
        label = (Text("Ban", style="green bold")
                 if msg["role"] == "user"
                 else Text("AI ", style="cyan bold"))
        snippet = msg["content"].replace("\n", " ")[:120]
        if len(msg["content"]) > 120:
            snippet += "..."
        table.add_row(str(i), label, snippet)

    console.print(table)
    console.print()


def print_sessions(sessions: list[dict]):
    console.print()
    if not sessions:
        console.print(Panel(
            "[dim]Chua co session nao duoc luu.\nGo [cyan]/save[/cyan] de luu session hien tai.[/dim]",
            title="Sessions", border_style="yellow",
        ))
        console.print()
        return

    table = Table(
        show_header=True, header_style="bold green",
        box=box.ROUNDED, border_style="green", padding=(0, 1),
    )
    table.add_column("#",        style="dim",        width=3,  no_wrap=True)
    table.add_column("Ten",      style="cyan bold",  width=28, no_wrap=True)
    table.add_column("Luu luc",  style="white",      width=20, no_wrap=True)
    table.add_column("Model",    style="yellow",     width=14, no_wrap=True)
    table.add_column("Luot hoi", style="magenta",    width=9,  no_wrap=True)

    for i, s in enumerate(sessions, 1):
        table.add_row(
            str(i),
            s["name"],
            s["saved_at"].replace("T", " "),
            s["model"],
            str(s["turns"]),
        )

    console.print(table)
    console.print()


def pick_model(current: str) -> str:
    try:
        models = ollama.list().models
    except Exception:
        console.print("[red]Khong the ket noi Ollama.[/red]")
        return current
    if not models:
        console.print("[yellow]Khong co model nao.[/yellow]")
        return current

    table = Table(
        show_header=True, header_style="bold green",
        box=box.ROUNDED, border_style="green",
    )
    table.add_column("#",     width=4, style="dim")
    table.add_column("Model", style="cyan bold")
    table.add_column("Size",  style="white")

    for i, m in enumerate(models, 1):
        size = f"{m.size/1e9:.1f} GB" if m.size else "?"
        marker = " [green](dang dung)[/green]" if m.model == current else ""
        table.add_row(str(i), m.model + marker, size)

    console.print()
    console.print(table)

    choice = Prompt.ask("  [cyan]Chon so[/cyan] (Enter = giu nguyen)",
                        default="", console=console)
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(models):
            chosen = models[idx].model
            console.print(f"  [green]>> Da chon:[/green] [bold]{chosen}[/bold]\n")
            return chosen
    console.print("  [dim]>> Giu nguyen.[/dim]\n")
    return current


# ════════════════════════════════════════════════════════════════════════════════
# Streaming response
# ════════════════════════════════════════════════════════════════════════════════

def stream_response(model: str, history: list) -> str:
    full_text = ""

    try:
        with console.status("[cyan]Dang suy nghi...[/cyan]", spinner="dots"):
            stream      = ollama.chat(model=model, messages=history, stream=True)
            first_chunk = next(stream)
        full_text += first_chunk.message.content
    except StopIteration:
        console.print("[red]AI khong tra loi.[/red]")
        return ""
    except ollama.ResponseError as e:
        console.print(f"[red]Loi Ollama:[/red] {e}")
        return ""
    except Exception as e:
        console.print(f"[red]Loi:[/red] {e}")
        return ""

    console.print(Rule(title="[bold cyan]  AI  [/bold cyan]", style="cyan"))
    console.print()
    console.print(first_chunk.message.content, end="", style="white")

    try:
        for chunk in stream:
            token      = chunk.message.content
            full_text += token
            console.print(token, end="", style="white")
    except Exception as e:
        console.print(f"\n[red]Loi stream:[/red] {e}")

    console.print("\n")
    console.print(Panel(
        Markdown(full_text),
        title="[cyan]AI[/cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print()
    return full_text


# ════════════════════════════════════════════════════════════════════════════════
# Main loop
# ════════════════════════════════════════════════════════════════════════════════

def main():
    model   = DEFAULT_MODEL
    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    print_banner(model)

    while True:
        try:
            user_input = Prompt.ask(
                Text.assemble(("  Ban", "green bold")),
                console=console,
            ).strip()
        except (EOFError, KeyboardInterrupt):
            # Xu ly nhu /exit
            user_input = "/exit"

        if not user_input:
            continue

        # ── Commands ────────────────────────────────────────────────────────
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd   = parts[0].lower()
            arg   = parts[1].strip() if len(parts) > 1 else ""

            # /exit ──────────────────────────────────────────────────────────
            if cmd == "/exit":
                has_content = any(m["role"] == "user" for m in history)
                if has_content:
                    try:
                        do_save = Confirm.ask(
                            "\n  [yellow]Luu session truoc khi thoat?[/yellow]",
                            console=console,
                        )
                    except (EOFError, KeyboardInterrupt):
                        do_save = False

                    if do_save:
                        name = save_history(history, model)
                        console.print(Panel(
                            f"[green]Da luu:[/green] [bold]{name}.json[/bold]\n"
                            f"[dim]Thu muc: {HISTORY_DIR}[/dim]",
                            border_style="green", padding=(0, 2),
                        ))

                console.print(Panel(
                    "[cyan]Tam biet! Hen gap lai.[/cyan]",
                    border_style="cyan", padding=(0, 2),
                ))
                break

            # /help ──────────────────────────────────────────────────────────
            elif cmd == "/help":
                print_help()

            # /clear ─────────────────────────────────────────────────────────
            elif cmd == "/clear":
                history = [{"role": "system", "content": SYSTEM_PROMPT}]
                console.print(Panel(
                    "[green]Da xoa lich su. Bat dau cuoc tro chuyen moi![/green]",
                    border_style="green", padding=(0, 2),
                ))
                console.print()

            # /history ───────────────────────────────────────────────────────
            elif cmd == "/history":
                print_history(history)

            # /save [ten] ────────────────────────────────────────────────────
            elif cmd == "/save":
                has_content = any(m["role"] == "user" for m in history)
                if not has_content:
                    console.print(Panel(
                        "[yellow]Chua co noi dung de luu.[/yellow]",
                        border_style="yellow", padding=(0, 2),
                    ))
                else:
                    name = save_history(history, model, name=arg or None)
                    console.print(Panel(
                        f"[green]Da luu session:[/green] [bold]{name}[/bold]\n"
                        f"[dim]{_session_path(name)}[/dim]",
                        title="[green]Luu thanh cong[/green]",
                        border_style="green", padding=(0, 2),
                    ))
                console.print()

            # /sessions ──────────────────────────────────────────────────────
            elif cmd == "/sessions":
                sessions = list_sessions()
                print_sessions(sessions)

            # /load ──────────────────────────────────────────────────────────
            elif cmd == "/load":
                sessions = list_sessions()
                print_sessions(sessions)

                if not sessions:
                    continue

                choice = Prompt.ask(
                    "  [cyan]Chon so session[/cyan] (Enter = huy)",
                    default="", console=console,
                )
                if not choice.isdigit():
                    console.print("  [dim]>> Huy tai.[/dim]\n")
                    continue

                idx = int(choice) - 1
                if not (0 <= idx < len(sessions)):
                    console.print("  [red]So khong hop le.[/red]\n")
                    continue

                result = load_history(sessions[idx]["name"])
                if result is None:
                    console.print("  [red]Khong the tai session.[/red]\n")
                    continue

                history, model = result
                console.print(Panel(
                    f"[green]Da tai session:[/green] [bold]{sessions[idx]['name']}[/bold]\n"
                    f"[dim]Model: {model} | "
                    f"{sum(1 for m in history if m['role']=='user')} luot hoi[/dim]",
                    title="[green]Tai thanh cong[/green]",
                    border_style="green", padding=(0, 2),
                ))
                print_banner(model)

            # /model ─────────────────────────────────────────────────────────
            elif cmd == "/model":
                model = pick_model(model)
                print_banner(model)

            # unknown ────────────────────────────────────────────────────────
            else:
                console.print(
                    f"  [red]Lenh khong hop le:[/red] [bold]{cmd}[/bold]"
                    "  -- go [cyan]/help[/cyan]\n"
                )
            continue

        # ── Chat ────────────────────────────────────────────────────────────
        console.print(Panel(
            user_input,
            title="[green]Ban[/green]",
            border_style="green",
            padding=(0, 1),
        ))

        history.append({"role": "user", "content": user_input})
        reply = stream_response(model, history)

        if reply:
            history.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
