# -*- coding: utf-8 -*-
"""
Ollama Python Integration Demo
Minh hoa 4 cach dung Ollama trong Python:
  1. Chat don gian
  2. Streaming (real-time output)
  3. Multi-turn conversation (nho context)
  4. Goi thang REST API bang requests
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import ollama
import requests
import json

MODEL = "llama3.2:3b"

# ─────────────────────────────────────────────
# 1. CHAT ĐƠN GIẢN
# ─────────────────────────────────────────────
def demo_simple_chat():
    print("\n" + "="*50)
    print("1. CHAT DON GIAN")
    print("="*50)

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "user", "content": "ESG là gì? Giải thích trong 3 câu."}
        ]
    )

    print(response.message.content)


# ─────────────────────────────────────────────
# 2. STREAMING — hiển thị từng từ khi generate
# ─────────────────────────────────────────────
def demo_streaming():
    print("\n" + "="*50)
    print("2. STREAMING (real-time)")
    print("="*50)

    stream = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "user", "content": "Kể 3 lợi ích của năng lượng tái tạo."}
        ],
        stream=True,
    )

    for chunk in stream:
        print(chunk.message.content, end="", flush=True)
    print()  # newline cuối


# ─────────────────────────────────────────────
# 3. MULTI-TURN CONVERSATION — nhớ lịch sử chat
# ─────────────────────────────────────────────
def demo_multi_turn():
    print("\n" + "="*50)
    print("3. MULTI-TURN (nho context)")
    print("="*50)

    history = [
        {"role": "system", "content": "Bạn là chuyên gia ESG, trả lời ngắn gọn bằng tiếng Việt."}
    ]

    turns = [
        "Carbon footprint là gì?",
        "Làm sao để giảm carbon footprint trong doanh nghiệp?",
        "Ví dụ cụ thể cho ngành sản xuất?",
    ]

    for user_msg in turns:
        history.append({"role": "user", "content": user_msg})
        print(f"\n[User]: {user_msg}")

        response = ollama.chat(model=MODEL, messages=history)
        assistant_reply = response.message.content

        history.append({"role": "assistant", "content": assistant_reply})
        print(f"[AI]:   {assistant_reply}")


# ─────────────────────────────────────────────
# 4. REST API TRỰC TIẾP — không cần SDK
# ─────────────────────────────────────────────
def demo_rest_api():
    print("\n" + "="*50)
    print("4. REST API (raw requests)")
    print("="*50)

    url = "http://localhost:11434/api/chat"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Viết 1 câu slogan về ESG bằng tiếng Việt."}
        ],
        "stream": False,
    }

    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    print(data["message"]["content"])


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[Ollama Demo] model: {MODEL}")

    demo_simple_chat()
    demo_streaming()
    demo_multi_turn()
    demo_rest_api()

    print("\n[Done!]")
