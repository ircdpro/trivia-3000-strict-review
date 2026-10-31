#!/usr/bin/env python3
"""Validate the published strict review pack using only Python's standard library."""

from __future__ import annotations

import json
import hashlib
import re
import sys
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TOPIC_FILE = re.compile(r"^(\d{3})_.+\.jsonl$")
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
    overlap = at & bt
    union = at | bt
    jaccard = len(overlap) / len(union) if union else 1.0
    containment = len(overlap) / min(len(at), len(bt)) if at and bt else 1.0
    ratio = SequenceMatcher(None, a, b).ratio()
    return jaccard >= 0.55 or containment >= 0.78 or ratio >= 0.82


def main() -> int:
    errors: list[str] = []
    topic_names_path = ROOT / "topic-names.json"
    topic_names = (
        json.loads(topic_names_path.read_text(encoding="utf-8"))
        if topic_names_path.exists() else {}
    )
    if set(topic_names) != {f"{number:03d}" for number in range(1, 301)}:
        errors.append("topic-names.json must contain exactly IDs 001..300")
    compact_names = [str(item.get("compact") or "") for item in topic_names.values()]
    if any(not name or len(name) > 28 for name in compact_names):
        errors.append("topic display names must contain 1..28 characters")
    if len({name.casefold() for name in compact_names}) != len(compact_names):
        errors.append("topic display names must be unique")
    files = sorted((ROOT / "questions").glob("[0-9][0-9][0-9]_*.jsonl"))
    expected_topics = {f"{number:03d}" for number in range(1, 301)}
    actual_topics = {path.name[:3] for path in files}
    if actual_topics != expected_topics:
        errors.append("topic file set is not exactly 001..300")

    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    seen_facts: set[tuple[str, str]] = set()
    by_answer: dict[str, list[str]] = defaultdict(list)
    total = 0

    for path in files:
        match = TOPIC_FILE.match(path.name)
        if not match:
            errors.append(f"invalid filename: {path.name}")
            continue
        topic_id = match.group(1)
        records = []
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                errors.append(f"{path.name}:{number}: invalid JSON: {error}")
        if len(records) != 10:
            errors.append(f"{path.name}: expected 10 records, found {len(records)}")

        topic_answers: set[str] = set()
        for item in records:
            total += 1
            item_id = str(item.get("id") or "")
            question = str(item.get("question") or "").strip()
            answer = str(item.get("answer") or "").strip()
            answer_key = norm(answer)
            question_key = norm(question)
            urls = item.get("source_urls") if isinstance(item.get("source_urls"), list) else []
            if item.get("source") == "wikimedia-structured-review":
                fact = (str(item.get("wikidata_entity") or ""), str(item.get("wikidata_property") or ""))
            else:
                fact = ("official", str(item.get("source_fact_id") or ""))

            if not re.fullmatch(rf"strict-{topic_id}-\d{{2}}", item_id):
                errors.append(f"{item_id or path.name}: invalid ID")
            if item_id in seen_ids:
                errors.append(f"{item_id}: duplicate ID")
            if str(item.get("topic_id") or "").zfill(3) != topic_id:
                errors.append(f"{item_id}: topic mismatch")
            expected_topic = str(topic_names.get(topic_id, {}).get("compact") or "")
            expected_full = str(topic_names.get(topic_id, {}).get("full_scope") or "")
            if item.get("topic") != expected_topic or item.get("topic_full") != expected_full:
                errors.append(f"{item_id}: compact/full topic metadata mismatch")
            if item.get("language") != "ms" or item.get("difficulty") != 3:
                errors.append(f"{item_id}: invalid language/difficulty")
            if item.get("review_status") != "pending_owner_review":
                errors.append(f"{item_id}: invalid review status")
            if not (12 <= len(question) <= 160 and question.endswith("?")):
                errors.append(f"{item_id}: invalid question shape")
            if not (1 <= len(answer) <= 80 and len(answer.split()) <= 10):
                errors.append(f"{item_id}: invalid answer shape")
            if answer_key and answer_key in question_key:
                errors.append(f"{item_id}: answer exposed in question")
            if question_key in seen_questions:
                errors.append(f"{item_id}: exact duplicate question")
            if answer_key in topic_answers:
                errors.append(f"{item_id}: repeated answer in topic")
            if fact in seen_facts:
                errors.append(f"{item_id}: repeated source fact")
            if any(near(question, prior) for prior in by_answer[answer_key]):
                errors.append(f"{item_id}: near-duplicate question")
            if item.get("source") == "wikimedia-structured-review":
                if not any(OLDID.search(str(url)) for url in urls):
                    errors.append(f"{item_id}: missing fixed Wikipedia revision")
                if not any(WIKIDATA.match(str(url)) for url in urls):
                    errors.append(f"{item_id}: missing Wikidata entity URL")
            elif item.get("source") == "official-source-review":
                excerpt = str(item.get("evidence_excerpt") or "").strip()
                digest = hashlib.sha256(excerpt.encode()).hexdigest()
                if not (20 <= len(excerpt) <= 500) or item.get("evidence_sha256") != digest:
                    errors.append(f"{item_id}: invalid official evidence")
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(item.get("source_retrieved_at") or "")):
                    errors.append(f"{item_id}: invalid official retrieval date")
                if not item.get("source_publisher") or not item.get("source_fact_id"):
                    errors.append(f"{item_id}: incomplete official source metadata")
            else:
                errors.append(f"{item_id}: invalid source type")

            seen_ids.add(item_id)
            seen_questions.add(question_key)
            seen_facts.add(fact)
            by_answer[answer_key].append(question)
            topic_answers.add(answer_key)

    if total != 3000:
        errors.append(f"expected 3,000 records, found {total}")
    manifest_path = ROOT / "manifest.json"
    if not manifest_path.exists():
        errors.append("manifest.json is missing")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") != "STRICT-PASS-REVIEW-ONLY":
            errors.append("manifest strict gate is not PASS")
        if manifest.get("questions_accepted") != 3000:
            errors.append("manifest does not report 3,000 accepted questions")
        if manifest.get("production_approved") is not False:
            errors.append("manifest must remain production_approved=false")

    if errors:
        print(f"STRICT-FAIL ({len(errors)} errors)")
        for error in errors[:200]:
            print(f"- {error}")
        if len(errors) > 200:
            print(f"- ... {len(errors) - 200} more")
        return 1
    print("STRICT-PASS-REVIEW-ONLY: 300 topics, 3,000 review candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
