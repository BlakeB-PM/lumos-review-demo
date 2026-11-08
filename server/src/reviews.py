import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REVIEWER = "reviewer-dana"
SCENARIOS = {"tour": "AD-REVIEW", "warehouse": "Q4-DATA"}
REMEDIATION = "not_performed_in_simulation"
SEARCH_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def page(records, cursor=0, limit=10):
    end = cursor + limit
    return {"records": records[cursor:end], "next_cursor": end if end < len(records) else None}


class Reviews:
    def __init__(self, state_path, simulated_albus=False, scenario="tour"):
        self.state_path = state_path
        self.campaign_id = SCENARIOS[scenario]
        self.campaigns = {
            c["id"]: c for c in read_json(DATA / "campaigns.json")
            if c["reviewer_id"] == REVIEWER and c["id"] == self.campaign_id
        }
        self.reviewer = next(r for r in read_json(DATA / "reviewers.json") if r["id"] == REVIEWER)
        self.items = {
            i["id"]: i for i in read_json(DATA / "review-items.json")
            if i["review_id"] in self.campaigns
        }
        self.recommendations = {
            r["item_id"]: r for r in read_json(DATA / "recommendations.json")
            if r["item_id"] in self.items
        }
        self.sources = {}
        for path in sorted((DATA / "knowledge").glob("*/*.md")):
            _, metadata, body = path.read_text(encoding="utf-8").split("---", 2)
            source = json.loads(metadata)
            self.sources[source["id"]] = {**source, "excerpt": body.strip()}
        self.albus = read_json(ROOT / "fixtures/albus-responses.json") if simulated_albus else None
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS demo_run (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS snapshots (
                    item_id TEXT PRIMARY KEY, version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS batches (
                    key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL, client TEXT NOT NULL,
                    review_id TEXT NOT NULL, decisions TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    seq INTEGER PRIMARY KEY, batch_key TEXT NOT NULL,
                    item_id TEXT NOT NULL, result TEXT NOT NULL,
                    UNIQUE(batch_key, item_id)
                );
                CREATE TABLE IF NOT EXISTS decisions (
                    item_id TEXT PRIMARY KEY, receipt TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS investigations (
                    id TEXT PRIMARY KEY, item_id TEXT NOT NULL, result TEXT NOT NULL
                );
            """)
            db.execute("INSERT OR IGNORE INTO demo_run VALUES (1, ?)", (str(uuid4()),))

    @contextmanager
    def db(self, write=False):
        db = sqlite3.connect(self.state_path, timeout=10)
        try:
            if write:
                db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def reset(self):
        with self.db(write=True) as db:
            for table in ("investigations", "decisions", "attempts", "batches", "proposals", "snapshots"):
                db.execute(f"DELETE FROM {table}")
            run_id = str(uuid4())
            db.execute("UPDATE demo_run SET id = ? WHERE singleton = 1", (run_id,))
            return run_id

    def start_demo(self, trigger_phrase):
        run_id = self.reset()
        campaign = self.campaign(self.campaign_id)
        items = [item for item in self.items.values() if item["review_id"] == campaign["id"]]
        return {
            "status": "demo_restarted",
            "run_id": run_id,
            "reviewer": self.reviewer,
            "campaign": campaign,
            "counts": {"recorded": 0, "pending": len(items), "failed_pending": 0},
            "items": [
                dict(item, status="pending", original_recommendation=self.recommendations[item["id"]])
                for item in items
            ],
        }

    def run_id(self, db):
        return db.execute("SELECT id FROM demo_run WHERE singleton = 1").fetchone()[0]

    def require_current_run(self, db, run_id):
        if self.run_id(db) != run_id:
            raise ValueError("The demo restarted. Prepare and confirm a new batch for the current run.")

    def advance_sandbox_snapshot(self):
        if "AR-107" not in self.items:
            raise ValueError("This control is available in the warehouse scenario only.")
        with self.db(write=True) as db:
            db.execute("INSERT OR IGNORE INTO snapshots VALUES ('AR-107', 2)")
        return {"item_id": "AR-107", "snapshot_version": 2}

    def campaign(self, review_id):
        if review_id not in self.campaigns:
            raise ValueError("Review is unavailable for this reviewer.")
        return self.campaigns[review_id]

    def version(self, db, item_id):
        row = db.execute("SELECT version FROM snapshots WHERE item_id = ?", (item_id,)).fetchone()
        return row[0] if row else self.items[item_id]["snapshot_version"]

    def source_for(self, db, evidence_id, item_id):
        source = self.sources.get(evidence_id)
        if source and item_id in source["item_ids"] and self.version(db, item_id) >= source.get("min_snapshot", 1):
            return {key: value for key, value in source.items() if key != "min_snapshot"}
        return None

    def list_my_reviews(self, status=None, cursor=0, limit=10):
        records = []
        for campaign in self.campaigns.values():
            if status is None or status == campaign["status"]:
                counts = self.get_review_status(campaign["id"])["counts"]
                records.append({**campaign, "counts": counts})
        return {"reviewer": self.reviewer, **page(records, cursor, limit)}

    def get_review_items(self, review_id, status=None, cursor=0, limit=10):
        self.campaign(review_id)
        records = []
        with self.db() as db:
            db.execute("BEGIN")
            run_id = self.run_id(db)
            recorded = {row[0] for row in db.execute("SELECT item_id FROM decisions")}
            for item_id, item in self.items.items():
                item_status = "recorded" if item_id in recorded else "pending"
                if item["review_id"] != review_id or status not in (None, item_status):
                    continue
                records.append(self.item_record(db, item, item_status))
        return {"review_id": review_id, "run_id": run_id, **page(records, cursor, limit)}

    def item_record(self, db, item, status):
        item_id = item["id"]
        version = self.version(db, item_id)
        record = dict(item, status=status, snapshot_version=version,
                      original_recommendation=self.recommendations[item_id])
        if version > item["snapshot_version"]:
            record["key_facts"] = ["Owner closed the sandbox assignment. Prior usage telemetry is historical."]
            record["evidence_refs"] = [*item["evidence_refs"], "OBS-AR-107-V2"]
        return record

    def audit_report(self, review_id):
        campaign = self.campaign(review_id)
        items = [item for item in self.items.values() if item["review_id"] == review_id]
        item_ids = {item["id"] for item in items}
        with self.db() as db:
            db.execute("BEGIN")
            run_id = self.run_id(db)
            receipts = {item_id: json.loads(receipt) for item_id, receipt in
                        db.execute("SELECT item_id, receipt FROM decisions") if item_id in item_ids}
            events = [
                {"sequence": seq, "batch_key": batch_key, **json.loads(result)}
                for seq, batch_key, item_id, result in db.execute(
                    "SELECT seq, batch_key, item_id, result FROM attempts ORDER BY seq DESC")
                if item_id in item_ids
            ]
            latest = {}
            for event in events:
                latest.setdefault(event["item_id"], event)
            rows = []
            for item in items:
                item_id = item["id"]
                receipt = receipts.get(item_id)
                row = self.item_record(db, item, "recorded" if receipt else "pending")
                refs = receipt["evidence"] if receipt else [{"id": ref} for ref in self.sources]
                sources = []
                for ref in refs:
                    source = self.source_for(db, ref["id"], item_id)
                    if source and source["version"] == ref.get("version", source["version"]):
                        sources.append(source)
                rows.append({**row, "receipt": receipt, "latest_attempt": latest.get(item_id),
                             "evidence_sources": sources})
        return {"run_id": run_id, "campaign": campaign, "reviewer": self.reviewer,
                "items": rows, "events": events, "remediation_status": REMEDIATION}

    def get_evidence(self, evidence_ids):
        records, unavailable = [], []
        with self.db() as db:
            db.execute("BEGIN")
            for evidence_id in dict.fromkeys(evidence_ids):
                source = next((record for item_id in self.items
                               if (record := self.source_for(db, evidence_id, item_id))), None)
                if source:
                    records.append(source)
                else:
                    unavailable.append(evidence_id)
        return {"records": records, "unavailable": unavailable}

    def search_review_evidence(self, review_id, query, item_id=None, limit=8):
        self.campaign(review_id)
        scope = [i for i, item in self.items.items() if item["review_id"] == review_id]
        if item_id is not None:
            if item_id not in scope:
                raise ValueError("Item is unavailable in this review.")
            scope = [item_id]
        terms = set(SEARCH_TOKEN.findall(query.casefold()))
        matches = []
        with self.db() as db:
            db.execute("BEGIN")
            for evidence_id in self.sources:
                source = next((record for i in scope if (record := self.source_for(db, evidence_id, i))), None)
                if source:
                    title_terms = set(SEARCH_TOKEN.findall(source["title"].casefold()))
                    body_terms = set(SEARCH_TOKEN.findall(json.dumps(source).casefold()))
                    score = 2 * len(terms & title_terms) + len(terms & body_terms)
                    if score:
                        matches.append((score, evidence_id, source))
        matches.sort(key=lambda entry: (-entry[0], entry[1]))
        return {"review_id": review_id, "item_id": item_id, "records": [m[2] for m in matches[:limit]]}

    def prepare_review_batch(self, review_id, run_id, decisions, client):
        self.campaign(review_id)
        ids = [decision["item_id"] for decision in decisions]
        if len(ids) != len(set(ids)):
            raise ValueError("Each item must appear only once in the batch.")
        proposal_id = str(uuid4())
        with self.db(write=True) as db:
            self.require_current_run(db, run_id)
            preview = []
            for decision in decisions:
                item_id = decision["item_id"]
                item = self.items.get(item_id)
                if item is None or item["review_id"] != review_id:
                    raise ValueError("Item is unavailable in this review.")
                if decision["outcome"] not in item["allowed_actions"]:
                    raise ValueError(f"Unsupported outcome for {item_id}.")
                if decision["snapshot_version"] != self.version(db, item_id):
                    raise ValueError(f"{item_id} changed. Refresh it before preparing the batch.")
                if db.execute("SELECT 1 FROM decisions WHERE item_id = ?", (item_id,)).fetchone():
                    raise ValueError(f"{item_id} has already been reviewed.")
                if any(self.source_for(db, ref, item_id) is None for ref in decision["evidence_refs"]):
                    raise ValueError(f"{item_id} has an unavailable evidence reference.")
                preview.append({**decision, "person": item["person"], "entitlement": item["entitlement"],
                                "original_recommendation": self.recommendations[item_id]["outcome"]})
            db.execute("INSERT INTO proposals VALUES (?, ?, ?, ?, ?)",
                       (proposal_id, run_id, client, review_id, json.dumps(decisions)))
        return {"proposal_id": proposal_id, "review_id": review_id, "status": "awaiting_confirmation",
                "decisions": preview}

    def record_review_batch(self, proposal_id, client):
        with self.db() as db:
            row = db.execute(
                "SELECT run_id, review_id, decisions FROM proposals WHERE id = ? AND client = ?",
                (proposal_id, client),
            ).fetchone()
        if row is None:
            raise ValueError("That proposal is unavailable. Prepare a new batch.")
        run_id, review_id, decisions = row
        return self.submit_decisions(review_id, json.loads(decisions), proposal_id, True, run_id, client)

    def submit_decisions(self, review_id, decisions, idempotency_key, reviewer_confirmed, run_id,
                         client="local_mcp_demo"):
        self.campaign(review_id)
        if not reviewer_confirmed:
            raise ValueError("Obtain explicit reviewer confirmation for this exact batch.")
        ids = [decision["item_id"] for decision in decisions]
        if len(ids) != len(set(ids)):
            raise ValueError("Each item must appear only once in the batch.")
        payload = json.dumps([review_id, decisions], sort_keys=True, separators=(",", ":"))
        if client != "local_mcp_demo":
            payload = f"{client}:{payload}"
        fingerprint = hashlib.sha256(payload.encode()).hexdigest()
        with self.db(write=True) as db:
            self.require_current_run(db, run_id)
            db.execute("INSERT OR IGNORE INTO batches VALUES (?, ?)", (idempotency_key, fingerprint))
            stored = db.execute("SELECT fingerprint FROM batches WHERE key = ?", (idempotency_key,)).fetchone()[0]
            if fingerprint != stored:
                raise ValueError("Idempotency key already belongs to a different payload.")

        results = []
        for decision in decisions:
            item_id = decision["item_id"]
            with self.db(write=True) as db:
                self.require_current_run(db, run_id)
                previous = db.execute("SELECT result FROM attempts WHERE batch_key = ? AND item_id = ?",
                                      (idempotency_key, item_id)).fetchone()
                if previous:
                    results.append(json.loads(previous[0]))
                    continue
                result = self.record_decision(db, review_id, decision, client)
                db.execute("INSERT INTO attempts(batch_key, item_id, result) VALUES (?, ?, ?)",
                           (idempotency_key, item_id, json.dumps(result)))
                results.append(result)
        return {"results": results, "atomicity": "per_item"}

    def record_decision(self, db, review_id, decision, client):
        item_id = decision["item_id"]
        item = self.items.get(item_id)
        result = {"item_id": item_id, "attempted_at": utc_now(), "client": client}
        if item is None or item["review_id"] != review_id:
            return {**result, "status": "item_unavailable"}
        version = self.version(db, item_id)
        if decision["snapshot_version"] != version:
            return {**result, "status": "refresh_required", "current_snapshot_version": version}
        if db.execute("SELECT 1 FROM decisions WHERE item_id = ?", (item_id,)).fetchone():
            return {**result, "status": "already_recorded"}
        if decision["outcome"] not in item["allowed_actions"] or not decision["reason"].strip():
            return {**result, "status": "invalid_decision"}
        refs = list(dict.fromkeys(decision["evidence_refs"]))
        sources = [self.source_for(db, ref, item_id) for ref in refs]
        if not sources or any(source is None for source in sources):
            return {**result, "status": "invalid_evidence"}
        investigation_id = decision.get("investigation_id")
        if investigation_id:
            row = db.execute("SELECT result FROM investigations WHERE id = ? AND item_id = ?",
                             (investigation_id, item_id)).fetchone()
            if row is None or json.loads(row[0])["snapshot_version"] != version:
                return {**result, "status": "invalid_investigation"}
        receipt = {**result, "status": "recorded", "receipt_id": str(uuid4()),
                   "review_id": review_id, "reviewer_id": REVIEWER,
                   "authority": "reviewer_confirmation_reported_by_client",
                   "snapshot_version": version, "outcome": decision["outcome"],
                   "reason": decision["reason"], "remediation_status": REMEDIATION,
                   "original_recommendation": self.recommendations[item_id],
                   "evidence": [{"id": source["id"], "version": source["version"]} for source in sources],
                   "investigation_id": investigation_id}
        if "context_summary" in decision:
            receipt["context_summary"] = decision["context_summary"]
        db.execute("INSERT INTO decisions VALUES (?, ?)", (item_id, json.dumps(receipt)))
        return receipt

    def get_review_status(self, review_id):
        self.campaign(review_id)
        ids = {i for i, item in self.items.items() if item["review_id"] == review_id}
        with self.db() as db:
            db.execute("BEGIN")
            recorded = {i: json.loads(r) for i, r in db.execute("SELECT item_id, receipt FROM decisions") if i in ids}
            failed = {}
            for item_id, result in db.execute("SELECT item_id, result FROM attempts ORDER BY seq"):
                if item_id in ids and item_id not in recorded:
                    failed[item_id] = json.loads(result)
        pending = sorted(ids - recorded.keys())
        return {"review_id": review_id, "recorded": list(recorded.values()), "pending": pending,
                "failed_pending": list(failed.values()), "remediation_status": REMEDIATION,
                "counts": {"recorded": len(recorded), "pending": len(pending), "failed_pending": len(failed)}}

    def ask_albus(self, item_id, snapshot_version, question, shared_context=None):
        started = perf_counter()
        if item_id not in self.items:
            raise ValueError("Item is unavailable for this reviewer.")
        with self.db(write=True) as db:
            if self.version(db, item_id) != snapshot_version:
                return {"mode": "fixture_simulation", "status": "unavailable",
                        "issue": "refresh_required", "current_snapshot_version": self.version(db, item_id)}
            variants = self.albus.get(item_id, {})
            variant = "clarified" if shared_context and shared_context["sharing_intent"] == "share_for_this_investigation" else "initial"
            fixture = variants.get(variant, variants.get("initial"))
            if fixture and not any(term in question.casefold() for term in fixture["question_terms"]):
                fixture = None
            fixture = fixture or {"status": "insufficient_evidence", "answer": "This question has no scripted investigation.",
                                  "unresolved_issues": ["Use scoped retrieval or ask the business owner."]}
            source_ids = fixture.get("sources", [])
            sources = [self.source_for(db, ref, item_id) for ref in source_ids]
            if any(source is None for source in sources):
                raise ValueError("The scripted investigation references unavailable evidence.")
            result = {key: val for key, val in fixture.items() if key not in ("sources", "question_terms")}
            result.update(mode="fixture_simulation", investigation_id=str(uuid4()), item_id=item_id,
                          snapshot_version=snapshot_version, source_refs=[
                              {"id": s["id"], "version": s["version"]} for s in sources
                          ], evidence_retrieved=source_ids, usage={"model_calls": 0},
                          recorded_at=utc_now(), elapsed_ms=round((perf_counter() - started) * 1000, 2))
            db.execute("INSERT INTO investigations VALUES (?, ?, ?)",
                       (result["investigation_id"], item_id, json.dumps(result)))
        return result
