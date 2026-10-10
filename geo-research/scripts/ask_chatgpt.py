#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向 ChatGPT（或任意 OpenAI 兼容接口）批量提问，供「AI 问答结构提取」步骤使用。

用法（在 geo-research 技能目录内运行；从仓库根目录运行请改用 geo-research/scripts/ask_chatgpt.py）：
  python3 scripts/ask_chatgpt.py --question "What is the best X?"
  python3 scripts/ask_chatgpt.py --question "Q1" --question "Q2"
  python3 scripts/ask_chatgpt.py --questions-file questions.txt

环境变量（配置在运行环境，绝不写入仓库）：
  CHATGPT_API_KEY    必填，接口密钥
  CHATGPT_API_BASE   可选，默认 https://api.openai.com/v1
  CHATGPT_MODEL      可选，默认 gpt-4o-mini
  CHATGPT_TIMEOUT    可选，单次请求超时秒数，默认 120

输出：JSON 数组，每项包含 query / answer / error 字段。
"""

import argparse
import json
import os
import sys
import urllib.request


SYSTEM_PROMPT = (
    "你是面向海外用户的内容研究助手。请直接、完整地回答用户的问题，"
    "先给结论再给理由；回答中如引用外部资料，请注明资料来源与链接。"
    "回答语言与用户问题保持一致。"
)


def build_url(base):
    return base.rstrip("/") + "/chat/completions"


def ask_once(api_key, base, model, question, timeout):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "temperature": 0.2,
        "max_tokens": 3000,
    }
    request = urllib.request.Request(
        build_url(base),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError("接口返回格式异常: " + json.dumps(data, ensure_ascii=False)[:500])


def load_questions(args):
    questions = []
    if args.question:
        questions.extend(args.question)
    if args.questions_file:
        with open(args.questions_file, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    questions.append(line)
    return questions


def main():
    parser = argparse.ArgumentParser(
        description=__doc__.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--question", action="append", help="要提问的问题，可重复传入")
    parser.add_argument("--questions-file", help="问题文件，每行一个问题")
    args = parser.parse_args()

    questions = load_questions(args)
    if not questions:
        parser.error("至少需要 --question 或 --questions-file")

    api_key = os.environ.get("CHATGPT_API_KEY", "").strip()
    if not api_key:
        result = [{"query": q, "answer": "", "error": "未配置 CHATGPT_API_KEY"} for q in questions]
        print(json.dumps(result, ensure_ascii=False))
        return 1

    base = os.environ.get("CHATGPT_API_BASE", "https://api.openai.com/v1").strip()
    model = os.environ.get("CHATGPT_MODEL", "gpt-4o-mini").strip()
    timeout = float(os.environ.get("CHATGPT_TIMEOUT", "120").strip())

    results = []
    for question in questions:
        try:
            answer = ask_once(api_key, base, model, question, timeout)
            results.append({"query": question, "answer": answer, "error": ""})
        except Exception as exc:
            results.append({"query": question, "answer": "", "error": str(exc)})

    print(json.dumps(results, ensure_ascii=False))
    return 0 if all(not item["error"] for item in results) else 1


if __name__ == "__main__":
    sys.exit(main())
