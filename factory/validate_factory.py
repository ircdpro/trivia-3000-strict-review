#!/usr/bin/env python3
"""Validate every published factory shard against the original review pack."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORDS = re.compile(r"[a-z0-9]+")
OLDID = re.compile(r"^https://(?:ms|en)\.wikipedia\.org/.+[?&]oldid=\d+")
WIKIDATA = re.compile(r"^https://www\.wikidata\.org/wiki/Q\d+$")


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(WORDS.findall(text))


def near(left: str, right: str) -> bool:
    a, b = norm(left), norm(right)
    at, bt = set(a.split()), set(b.split())
    overlap, union = at & bt, at | bt
    jaccard = len(overlap) / len(union) if union else 1.0
    containment = len(overlap) / min(len(at), len(bt)) if at and bt else 1.0
    return jaccard >= 0.55 or containment >= 0.78 or SequenceMatcher(None, a, b).ratio() >= 0.82


def records(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    errors: list[str] = []
    topic_names = json.loads((ROOT / "topic-names.json").read_text(encoding="utf-8"))
    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    seen_facts: set[tuple[str, str]] = set()
    by_answer: dict[str, list[str]] = defaultdict(list)
    topic_answers: dict[str, set[str]] = defaultdict(set)

    for item in records(ROOT / "all-questions.jsonl"):
        question = str(item.get("question") or "")
        answer = str(item.get("answer") or "")
        topic_id = str(item.get("topic_id") or "").zfill(3)
        seen_questions.add(norm(question))
        by_answer[norm(answer)].append(question)
        topic_answers[topic_id].add(norm(answer))
        seen_facts.add((str(item.get("wikidata_entity") or ""), str(item.get("wikidata_property") or "")))

    total = 0
    expected_sequence = 1
    batch_paths = sorted((ROOT / "factory" / "batches").glob("batch-*.jsonl"))
    for batch_number, path in enumerate(batch_paths, 1):
        if path.name != f"batch-{batch_number:05d}.jsonl":
            errors.append(f"non-contiguous batch name: {path.name}")
        batch = records(path)
        if not (1 <= len(batch) <= 5000):
            errors.append(f"{path.name}: batch size must be 1..5000")
        for line_number, item in enumerate(batch, 1):
            total += 1
            item_id = str(item.get("id") or "")
            topic_id = str(item.get("topic_id") or "").zfill(3)
            question = str(item.get("question") or "").strip()
            answer = str(item.get("answer") or "").strip()
            question_key, answer_key = norm(question), norm(answer)
            fact = (str(item.get("wikidata_entity") or ""), str(item.get("wikidata_property") or ""))
            urls = item.get("source_urls") if isinstance(item.get("source_urls"), list) else []
            location = f"{path.name}:{line_number}"

            if item_id != f"factory-{expected_sequence:09d}":
                errors.append(f"{location}: non-contiguous ID {item_id}")
            expected_sequence += 1
            if item_id in seen_ids:
                errors.append(f"{location}: duplicate ID")
            if topic_id not in topic_names:
                errors.append(f"{location}: invalid topic ID")
            else:
                topic = topic_names[topic_id]
                if item.get("topic") != topic["compact"] or item.get("topic_full") != topic["full_scope"]:
                    errors.append(f"{location}: topic metadata mismatch")
            if item.get("language") != "ms" or item.get("difficulty") != 3:
                errors.append(f"{location}: invalid language/difficulty")
            if item.get("review_status") != "pending_owner_review" or item.get("production_approved") is not False:
                errors.append(f"{location}: invalid review/approval state")
            if not (12 <= len(question) <= 160 and question.endswith("?")):
                errors.append(f"{location}: invalid question shape")
            if not (1 <= len(answer) <= 80 and len(answer.split()) <= 10):
                errors.append(f"{location}: invalid answer shape")
            if answer_key and answer_key in question_key:
                errors.append(f"{location}: answer exposed in question")
            if question_key in seen_questions:
                errors.append(f"{location}: duplicate question")
            if fact in seen_facts:
                errors.append(f"{location}: repeated source fact")
            if answer_key in topic_answers[topic_id]:
                errors.append(f"{location}: repeated answer in topic")
            if any(near(question, prior) for prior in by_answer[answer_key]):
                errors.append(f"{location}: near-duplicate with same answer")
            if item.get("source") != "wikimedia-structured-review":
                errors.append(f"{location}: unsupported source type")
            if not any(OLDID.search(str(url)) for url in urls):
                errors.append(f"{location}: missing fixed Wikipedia revision")
            if not any(WIKIDATA.match(str(url)) for url in urls):
                errors.append(f"{location}: missing Wikidata URL")

            seen_ids.add(item_id)
            seen_questions.add(question_key)
            seen_facts.add(fact)
            by_answer[answer_key].append(question)
            topic_answers[topic_id].add(answer_key)

    status = json.loads((ROOT / "factory" / "status.json").read_text(encoding="utf-8"))
    if status.get("published_questions") != total:
        errors.append("status published_questions does not match batch records")
    if status.get("published_batches") != len(batch_paths):
        errors.append("status published_batches does not match batch files")
    if status.get("production_approved") is not False:
        errors.append("factory must remain production_approved=false")

    if errors:
        print(f"FACTORY-FAIL ({len(errors)} errors)")
        for error in errors[:200]:
            print(f"- {error}")
        return 1
    print(f"FACTORY-PASS: {len(batch_paths)} batches, {total:,} pending review candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
