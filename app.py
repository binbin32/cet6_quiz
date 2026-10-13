# -*- coding: utf-8 -*-
"""
六级背单词 · 网页版（Streamlit）

在电脑上运行：
    pip install streamlit
    streamlit run app.py

手机访问：和电脑连同一个 WiFi，用运行后命令行里显示的 "Network URL" 打开。
"""
import random
import json
import os
from datetime import date, timedelta

import streamlit as st

# ============ 词库路径（按需改成完整路径）============
WORD_FILE = "cet6_words.txt"
# ==================================================

PROGRESS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(WORD_FILE)), "progress.json"
)

INTERVALS = [0, 1, 2, 4, 7, 15, 30]   # 记忆间隔（天）：等级 0~6


def load_words(path):
    words = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                words.append((parts[0], parts[1]))
    return words


def load_progress(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(path, progress):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def today():
    return date.today()


def days_from_now(n):
    return (today() + timedelta(days=n)).isoformat()


def due_words(words, progress):
    new, due = [], []
    for w, m in words:
        rec = progress.get(w)
        if rec is None:
            new.append((w, m))
        elif rec["next_review"] <= today().isoformat():
            due.append((w, m))
    return new, due


def make_question(all_meanings, target_meaning):
    distractors = random.sample(
        [m for m in all_meanings if m != target_meaning], 3
    )
    options = distractors + [target_meaning]
    random.shuffle(options)
    return options, options.index(target_meaning)


def record(progress, word, correct):
    rec = progress.get(word, {
        "level": 0, "correct": 0, "wrong": 0,
        "next_review": today().isoformat(),
    })
    if correct:
        rec["level"] = min(rec["level"] + 1, len(INTERVALS) - 1)
        rec["correct"] += 1
    else:
        rec["level"] = 1
        rec["wrong"] += 1
    rec["next_review"] = days_from_now(INTERVALS[rec["level"]])
    progress[word] = rec


st.set_page_config(page_title="六级背单词", page_icon="📖")
st.title("六级背单词")
st.caption("看英文单词，选正确的中文释义")

# ---- 第一次运行时初始化状态 ----
if "inited" not in st.session_state:
    st.session_state.words = load_words(WORD_FILE)
    st.session_state.progress = load_progress(PROGRESS_FILE)
    st.session_state.all_meanings = [m for _, m in st.session_state.words]
    new, due = due_words(st.session_state.words, st.session_state.progress)
    pool = new + due
    random.shuffle(pool)
    st.session_state.pool = pool
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.wrong = []
    st.session_state.inited = True

pool = st.session_state.pool
idx = st.session_state.idx

mastered = sum(1 for r in st.session_state.progress.values() if r["level"] >= 6)
st.write(
    f"📈 已进入长期记忆：{mastered} 词　|　本次答对：{st.session_state.score}"
    f"　|　第 {min(idx + 1, len(pool))} / {len(pool)} 题"
)

if not pool:
    st.info("今天没有到期要复习的词，全部搞定啦！")
    if st.button("重新开始一轮"):
        st.session_state.clear()
        st.rerun()
elif idx < len(pool):
    word, meaning = pool[idx]

    qkey = f"options_{idx}"
    if qkey not in st.session_state:
        options, answer_idx = make_question(st.session_state.all_meanings, meaning)
        st.session_state[qkey] = (options, answer_idx)
    options, answer_idx = st.session_state[qkey]

    st.subheader(word)
    choice = st.radio("它的中文意思是？", options, key=f"radio_{idx}")

    answered_key = f"answered_{idx}"

    if st.button("提交答案"):
        if choice is None:
            st.warning("请先选择一个答案")
        else:
            correct = (choice == options[answer_idx])
            record(st.session_state.progress, word, correct)
            if correct:
                st.session_state.score += 1
            else:
                st.session_state.wrong.append((word, meaning))
            st.session_state[answered_key] = correct
            save_progress(PROGRESS_FILE, st.session_state.progress)  # 每答一题就保存
            st.rerun()

    if st.session_state.get(answered_key) is not None:
        if st.session_state[answered_key]:
            st.success("回答正确！")
        else:
            st.error(f"回答错误。正确答案是：{options[answer_idx]}")
        if st.button("下一题"):
            st.session_state.idx += 1
            st.rerun()
else:
    save_progress(PROGRESS_FILE, st.session_state.progress)
    st.subheader("本次学习结束！")
    total = len(pool)
    st.write(
        f"答对 {st.session_state.score} / {total}，"
        f"正确率 {st.session_state.score / total * 100:.0f}%"
    )
    if st.session_state.wrong:
        st.write("答错的词（已安排 1 天后重测）：")
        for w, m in st.session_state.wrong:
            st.write(f"- {w} → {m}")
    if st.button("重新开始一轮"):
        st.session_state.clear()
        st.rerun()
