#!/usr/bin/env python3
"""Synthetic byte-accounting experiment for the RFC 0022 drafting discussion.

This is NOT a workflow verifier, production writer, conformance corpus, or operation recording.
It constructs workflow-shaped controls and explicitly synthetic, prevalidated artifact roles.
It does not validate a Dialect, Runtime export, receipt, signature, projection, or influence.
There is no filesystem/network acquisition and no arbitrary baseline-file-map input. A decision
checks only this experiment's reconstructed synthetic candidate, never a real refusal claim.

Run ``python tools/workflow_admission_probe.py`` for deterministic measured examples. The proposed
version selectors and this small experiment's transitions are not adopted portable semantics.
The only projection copies a whole synthetic parent object under ``parent``; outputs are the
``items`` array of the generated synthetic preparation. Runtime errors, genuine signatures,
receipt validation, auxiliary finalization, grammar validation and an independent proof replay
reader are outside this experiment. Its opaque synthetic roles must not be cited as valid Runtime
artifacts or evidence that a real writer refused correctly.
Pre-ID count refusals and local artifact-bound failures are not modeled; the selected synthetic
cases must fit those prevalidated domains. The experiment does not establish their validity.
"""
from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

if __package__:
    from . import dialect_verify as dialect
else:
    import dialect_verify as dialect

AT = "2026-01-01T00:00:00Z"
ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
PROOF_LIMIT = 8 * 1024 * 1024
sha = dialect.digest_of
canon = dialect.canon
payload_bytes = dialect.preparation_bytes


class ProbeError(ValueError):
    """Invalid input to the synthetic experiment; not a portable reader outcome."""


class RecordingUnavailable(ProbeError):
    """Mandatory synthetic recording bytes cannot fit; no valid refusal is claimed."""


@dataclass(frozen=True)
class Stage:
    id: str
    parent: str | None = None


@dataclass(frozen=True)
class Limits:
    max_bytes: int = 1_000_000_000
    max_files: int = 65536
    max_records: int = 4096
    max_instances: int = 4096
    max_attempts: int = 16


@dataclass(frozen=True)
class Snapshot:
    """Owned file bytes at a synthetic accounting point, counted once per path."""

    files: tuple[tuple[str, bytes], ...]
    instances: int
    records: int

    @property
    def total_bytes(self) -> int:
        return sum(len(raw) for _, raw in self.files)

    def as_files(self) -> dict[str, bytes]:
        return dict(self.files)


@dataclass(frozen=True)
class Decision:
    """A frozen synthetic comparison; later work cannot replace either accounting basis."""

    accepted: Snapshot
    refused: Snapshot
    limits: Limits
    cutoff: bool = False

    def fits(self, snapshot: Snapshot) -> bool:
        return (snapshot.total_bytes <= self.limits.max_bytes
                and len(snapshot.files) <= self.limits.max_files
                and snapshot.instances <= self.limits.max_instances
                and snapshot.records <= self.limits.max_records
                and len(snapshot.as_files()["admission-proof.json"]) <= PROOF_LIMIT)

    @property
    def outcome(self) -> str:
        if not self.cutoff and self.fits(self.accepted):
            return "accepted"
        if not self.fits(self.refused):
            return "recording-unavailable"
        return "refused"

    def check_claim(self, claim: str) -> bool:
        """Compare a claim about this synthetic decision, not an external workflow record."""
        return claim == self.outcome and claim != "recording-unavailable"


@dataclass(frozen=True)
class Result:
    """Synthetic prevalidated observation. Payloads are objects in literal-preserving JSON."""

    instance: str
    payloads: tuple[bytes, ...] = ()
    state: str = "completed"
    response: str = "synthetic response"

    def material(self) -> dict[str, bytes]:
        values = [dialect.read_document(raw, "synthetic output") for raw in self.payloads]
        if any(not isinstance(value, dict) for value in values):
            raise ProbeError("synthetic outputs must be objects")
        if self.state not in {"completed", "interrupted", "cancelled", "not-acquired"}:
            raise ProbeError("unsupported synthetic result state")
        if self.state != "completed" and values:
            raise ProbeError("stopped synthetic results have no outputs")
        if self.state == "not-acquired":
            return {}
        sources = payload_bytes({"synthetic": True, "response": self.response})
        files = {"sources.json": sources}
        if self.state == "completed":
            preparation = payload_bytes({"synthetic": True, "verifiedAt": AT,
                                         "facts": {"items": values}})
            audit = canon({"synthetic": True, "preparationDigest": sha(preparation)})
            files.update({"preparation.json": preparation, "audit.json": audit,
                          "preparation.sha256": (sha(preparation) + "\n").encode(),
                          "verified-at.txt": (AT + "\n").encode()})
        # Exact synthetic JSON value spans, without claiming a valid Runner export.
        run = b'{"synthetic":true,"run":{"state":' + canon(self.state)
        run += b',"input":{"source":{"sources":' + sources + b'}'
        if self.state == "completed":
            run += b',"preparation":' + preparation
        run += b'}'
        if self.state == "completed":
            run += b',"audit":' + audit
        files["run.json"] = run + b'}}'
        return files


class Probe:
    """Small synthetic state machine with a derived inventory, not caller-asserted baselines.

    Supported: object-copy projection, many outputs, reviewed selection, interrupted/cancelled
    results, explicit singleton retries, stops before first attempt, and affected-stage forks.
    Every method is an experiment operation, not an acquisition or permission API.
    """

    def __init__(self, stages: tuple[Stage, ...] = (Stage("root"),), *,
                 limits: Limits = Limits(), root_case: bytes = b'{}') -> None:
        if not stages or stages[0].parent is not None:
            raise ProbeError("one first root stage is required")
        seen: set[str] = set()
        for stage in stages:
            if not ID.fullmatch(stage.id) or stage.id in seen:
                raise ProbeError("invalid or duplicate synthetic stage ID")
            if stage != stages[0] and stage.parent not in seen:
                raise ProbeError("synthetic stages need an earlier parent")
            seen.add(stage.id)
        if any(value < 1 for value in vars(limits).values()):
            raise ProbeError("positive limits are required")
        root = dialect.read_document(root_case, "synthetic root case")
        if not isinstance(root, dict):
            raise ProbeError("root case must be an object")
        self.stages, self.limits = stages, limits
        self.artifacts: dict[str, bytes] = {}
        self.all_instances: dict[str, dict[str, Any]] = {}
        self.planned_ids = {"root-instance"}
        self.reserved_by: dict[str, int] = {}
        self.active: list[str] = []
        self.outputs: dict[str, tuple[dict[str, Any], bytes]] = {}
        self.sets = {s.id: [] for s in stages}
        self.selections: dict[str, dict[str, Any] | None] = {s.id: None for s in stages}
        self.selection_revisions = {s.id: 0 for s in stages}
        self.pending = ["root-instance"]
        self.reservation_epoch = 1
        self.group: list[str] | None = None
        self.cutoffs: set[str] = set()
        self.decisions: list[Decision] = []
        self.root_case = payload_bytes(root)
        documents = []
        self.frozen = []
        for stage in stages:
            base = f"stages/{stage.id}/"
            raw = canon({"synthetic": True, "stage": stage.id})
            for name in ("pack.json", "dialect.json", "bound-dialect.json", "release.json"):
                self.artifacts[base + name] = raw
            self.artifacts[base + "profiles.json"] = b"[]"
            self.frozen.append({"stage": stage.id, "publishedDialectDigest": sha(raw),
                                "bindingDocumentDigest": None, "boundDialectDigest": sha(raw),
                                "packDigest": sha(raw), "releaseDigest": sha(raw),
                                "runtimeDigest": sha(b"synthetic runtime, not an executable")})
            documents.append(self._stage_document(stage, sha(raw)))
        self.workflow = {"workflowVersion": 2, "stages": documents, "result": stages[-1].id,
                         "limits": {"maxStages": len(stages), "maxRecords": limits.max_records,
                                    "maxInstances": limits.max_instances,
                                    "maxAttempts": limits.max_attempts, "maxBytes": limits.max_bytes}}
        self.workflow_digest = sha(canon(self.workflow))
        self.proof = {"admissionProofVersion": 1, "workflowDigest": self.workflow_digest,
                      "execution": "synthetic-execution", "rootCaseDigest": sha(self.root_case),
                      "frozenDigest": sha(canon(self.frozen)), "rootInstance": "root-instance",
                      "epochBlocks": []}
        self._epoch("root", {"instance": "root-instance"})
        self._instance("root-instance", stages[0].id, None, None, self.root_case)
        self._require_fit(self.snapshot())

    def _stage_document(self, stage: Stage, pin: str) -> dict[str, Any]:
        doc = {"id": stage.id, "dialect": {"version": 3, "digest": pin},
               "pack": {"id": "urn:synthetic:" + stage.id, "digest": pin},
               "input": {"root": True} if stage.parent is None else
                        {"fromStage": stage.parent, "selected": True},
               "execution": "once" if stage.parent is None else "each-selected-record",
               "caseBindings": [] if stage.parent is None else
                               [{"from": "", "to": "/parent", "type": "object", "required": True}],
               "outputs": {"pointer": "/items", "cardinality": "many"},
               "relation": {"label": "synthetic-parent", "direction": "output-to-parent"}}
        if any(s.parent == stage.id for s in self.stages):
            doc["selection"] = {"mode": "reviewer"}
        return doc

    def _epoch(self, kind: str, plan: dict[str, Any]) -> None:
        previous = sha(canon(self.proof))
        blocks = self.proof["epochBlocks"]
        number = sum(len(block) for block in blocks) + 1
        if not blocks or len(blocks[-1]) == 4096:
            if len(blocks) == 32:
                raise RecordingUnavailable("synthetic proof block limit")
            blocks.append([])
        epoch = {"number": number, "previousProofDigest": previous, "kind": kind}
        if kind in {"selection", "fork"}:
            epoch.update(plan)
        elif kind == "group":
            epoch.update({"reservation": plan["reservationEpoch"],
                          "starts": [{"instance": slot["instance"], **slot["begin"]}
                                     for slot in plan["members"] if "begin" in slot],
                          "deferred": [slot["instance"] for slot in plan["members"]
                                       if slot.get("stop") == "interrupted"],
                          "cancelled": [{"instance": slot["instance"],
                                         "actor": "synthetic reviewer", "at": AT}
                                        for slot in plan["members"] if slot.get("stop") == "cancelled"],
                          "results": []})
        elif kind == "retry":
            slot, = plan["members"]
            epoch.update({"start": {"instance": slot["instance"], **slot["begin"]}, "results": []})
        blocks[-1].append(epoch)

    def _observe(self, value: dict[str, Any]) -> None:
        self.proof["epochBlocks"][-1][-1]["results"].append(value)

    def _instance(self, id: str, stage: str, parent: str | None, selection: str | None,
                  case: bytes) -> None:
        if not ID.fullmatch(id) or id in self.all_instances:
            raise ProbeError("instance IDs must be fresh across all retained history")
        bindings = next(s["caseBindings"] for s in self.workflow["stages"] if s["id"] == stage)
        input_pin = sha(self.root_case) if parent is None else sha(canon(
            {"parentRecord": parent, "selectionDigest": selection, "caseBindings": bindings}))
        self.all_instances[id] = {"id": id, "stage": stage, "parentRecord": parent,
                                  "selectionDigest": selection, "inputDigest": input_pin,
                                  "caseDigest": sha(case), "state": "interrupted",
                                  "failure": None, "attempts": []}
        self.active.append(id)
        self.reserved_by[id] = self.reservation_epoch
        self.artifacts[f"instances/{id}/case.json"] = case

    def _ordered(self, ids: Iterable[str]) -> list[str]:
        rank = {stage.id: i for i, stage in enumerate(self.stages)}
        active_rank = {id: i for i, id in enumerate(self.active)}
        return sorted(ids, key=lambda id: (rank[self.all_instances[id]["stage"]], active_rank[id]))

    def _set(self, stage: str) -> dict[str, Any]:
        return {"workflowDigest": self.workflow_digest, "execution": "synthetic-execution",
                "stage": stage, "records": self.sets[stage]}

    def snapshot(self) -> Snapshot:
        """Reconstruct all current controls; historical immutable paths remain present."""
        files = dict(self.artifacts)
        files.update({"workflow.json": canon(self.workflow), "root-case.json": self.root_case,
                      "admission-proof.json": canon(self.proof)})
        for name in ("workflow", "admission-proof"):
            files[name + ".sha256"] = (sha(files[name + ".json"]) + "\n").encode()
        output_sets = []
        for stage in self.stages:
            upstream = self.selections[stage.parent] if stage.parent is not None else None
            blocked = stage.parent is not None and (upstream is None or "refusal" in upstream)
            output_sets.append({"stage": stage.id, "status": "blocked" if blocked else "closed",
                                "records": list(self.sets[stage.id])})
            files[f"sets/{stage.id}.json"] = canon(self._set(stage.id))
        execution = {"executionVersion": 2, "workflowDigest": self.workflow_digest,
                     "execution": "synthetic-execution", "rootCaseDigest": sha(self.root_case),
                     "frozen": self.frozen, "instances": [self.all_instances[id]
                                                             for id in self._ordered(self.active)],
                     "outputSets": output_sets,
                     "selections": [None if self.selections[s.id] is None else
                                    sha(canon(self.selections[s.id])) for s in self.stages],
                     "admissionProofDigest": sha(files["admission-proof.json"])}
        files["execution.json"] = canon(execution)
        files["execution.sha256"] = (sha(files["execution.json"]) + "\n").encode()
        return Snapshot(tuple(sorted(files.items())), len(self.all_instances), len(self.outputs))

    def _require_fit(self, snapshot: Snapshot) -> None:
        if len(snapshot.as_files()["admission-proof.json"]) > PROOF_LIMIT:
            raise RecordingUnavailable("synthetic proof byte limit")
        if not Decision(snapshot, snapshot, self.limits).fits(snapshot):
            raise RecordingUnavailable("required synthetic recording does not fit")

    def _adopt(self, other: Probe) -> None:
        self.__dict__ = other.__dict__

    def _require_unconsumed(self, id: str) -> None:
        instance = self.all_instances[id]
        selection = self.selections[instance["stage"]]
        if selection is not None and "refusal" not in selection:
            if instance["parentRecord"] is None:
                raise ProbeError("a consumed root requires a new execution")
            raise ProbeError("consumed work requires an affected-stage fork")

    def begin_group(self, *, retry: str | None = None,
                    stops: tuple[tuple[str, str], ...] = ()) -> None:
        """Commit explicit begin stubs atomically; plan membership alone never begins work."""
        if self.group is not None:
            raise ProbeError("close the current synthetic group first")
        if len(dict(stops)) != len(stops) or any(state not in {"cancelled", "interrupted"}
                                                for _, state in stops):
            raise ProbeError("invalid synthetic stops")
        members = [retry] if retry is not None else self._ordered(self.pending)
        if not members or any(id not in members for id, _ in stops):
            raise ProbeError("group must cover its reserved slots")
        if retry is not None:
            if self.pending:
                raise ProbeError("resolve the reserved first-attempt group before retrying")
            instance = self.all_instances[retry]
            if retry not in self.active or instance["state"] not in {"failed", "interrupted"}:
                raise ProbeError("only active failed/interrupted instances can be explicitly retried")
            self._require_unconsumed(retry)
            if stops:
                raise ProbeError("pre-attempt stops are only supported for new reservations")
            if not instance["attempts"]:
                members = self._ordered(id for id in self.active
                                        if self.reserved_by[id] == self.reserved_by[retry]
                                        and self.all_instances[id]["state"] == "interrupted"
                                        and not self.all_instances[id]["attempts"])
                stops = tuple((id, "interrupted") for id in members if id != retry)
        candidate = copy.deepcopy(self)
        stop_states = dict(stops)
        slots = []
        for id in members:
            instance = candidate.all_instances[id]
            # Carrying an old deferred slot is unchanged work. Starting or cancelling it is not.
            if stop_states.get(id) != "interrupted":
                self._require_unconsumed(id)
            if id in stop_states:
                if instance["attempts"]:
                    raise ProbeError("stopping without an attempt is only valid before first begin")
                slots.append({"instance": id, "stop": stop_states[id]})
            else:
                number = len(instance["attempts"]) + 1
                if number > self.limits.max_attempts:
                    raise RecordingUnavailable("synthetic attempt bound")
                assertion = None if number == 1 else {"actor": "synthetic reviewer", "at": AT}
                slots.append({"instance": id, "begin": {"number": number, "retry": assertion}})
        is_retry = retry is not None and bool(self.all_instances[retry]["attempts"])
        plan = {"reservationEpoch": None if is_retry else self.reserved_by[members[0]],
                "members": slots}
        if not is_retry and all(slot.get("stop") == "interrupted" for slot in slots):
            raise ProbeError("a defer-only synthetic group is a no-op")
        candidate._epoch("retry" if is_retry else "group", plan)
        candidate.group, candidate.cutoffs = [], set()
        for slot in slots:
            id = slot["instance"]
            instance = candidate.all_instances[id]
            if "stop" in slot:
                instance["state"] = slot["stop"]
                continue
            number, assertion = slot["begin"]["number"], slot["begin"]["retry"]
            attempt = {"number": number, "state": "interrupted", "failure": None,
                       "preparationDigest": None, "auditDigest": None, "runDigest": None,
                       "evaluationErrorDigest": None, "retry": assertion}
            instance["attempts"].append(attempt)
            instance.update(state="interrupted", failure=None)
            candidate.group.append(id)
        candidate.pending = [id for id in candidate.pending if id not in members]
        if not candidate.group:
            candidate.group = None
        candidate._require_fit(candidate.snapshot())
        self._adopt(candidate)

    def finish_group(self, results: Iterable[Result], *,
                     claims: tuple[tuple[str, str], ...] = ()) -> tuple[Decision, ...]:
        """Physical arrival order is ignored. This method performs no acquisition."""
        received = list(results)
        by_id = {result.instance: result for result in received}
        if self.group is None or len(by_id) != len(received) or set(by_id) != set(self.group):
            raise ProbeError("results must cover the actual begun group exactly once")
        claimed = dict(claims)
        if len(claimed) != len(claims) or not set(claimed) <= set(self.group):
            raise ProbeError("invalid synthetic claim membership")
        if any(by_id[id].state != "completed" or claim not in {"accepted", "refused"}
               for id, claim in claimed.items()):
            raise ProbeError("claims only compare synthetic completed output proposals")
        decisions = []
        for id in list(self.group):
            result = by_id[id]
            common = copy.deepcopy(self)
            instance = common.all_instances[id]
            attempt = instance["attempts"][-1]
            material = result.material()
            base = f"instances/{id}/attempts/{attempt['number']}/"
            common.artifacts.update({base + name: raw for name, raw in material.items()})
            common._observe({"instance": id, "number": attempt["number"],
                             "state": {"completed": "evaluated", "not-acquired": "suppressed"}
                                      .get(result.state, result.state),
                             "failure": None,
                             "runDigest": sha(material["run.json"]) if "run.json" in material else None,
                             "preparationDigest": sha(material["preparation.json"])
                                                  if "preparation.json" in material else None,
                             "auditDigest": sha(material["audit.json"]) if "audit.json" in material else None,
                             "evaluationErrorDigest": None, "auditSignaturesDigest": None})
            for member, name in (("preparationDigest", "preparation.json"),
                                 ("auditDigest", "audit.json"), ("runDigest", "run.json")):
                attempt[member] = sha(material[name]) if name in material else None
            if result.state == "not-acquired":
                if instance["stage"] not in self.cutoffs:
                    raise ProbeError("a no-run suppression needs a proved cutoff in this epoch")
                instance.update(state="failed", failure="limit-exceeded")
                attempt.update(state="failed", failure="limit-exceeded")
                common._require_fit(common.snapshot())
                self._adopt(common)
                continue
            if result.state != "completed":
                instance.update(state=result.state, failure=None)
                attempt.update(state=result.state, failure=None)
                common._require_fit(common.snapshot())
                self._adopt(common)
                continue
            accepted, refused = copy.deepcopy(common), copy.deepcopy(common)
            values = dialect.read_document(material["preparation.json"], "synthetic preparation")["facts"]["items"]
            accepted._publish(id, values)
            refused.all_instances[id].update(state="failed", failure="limit-exceeded")
            refused.all_instances[id]["attempts"][-1].update(state="failed", failure="limit-exceeded")
            decision = Decision(accepted.snapshot(), refused.snapshot(), self.limits,
                                instance["stage"] in self.cutoffs)
            if id in claimed and not decision.check_claim(claimed[id]):
                raise ProbeError("synthetic claim disagrees with the original candidate")
            if decision.outcome == "recording-unavailable":
                raise RecordingUnavailable("synthetic result/refusal cannot fit; retain custody separately")
            chosen = accepted if decision.outcome == "accepted" else refused
            if decision.outcome == "refused":
                chosen.cutoffs.add(instance["stage"])
            chosen.decisions.append(decision)
            self._adopt(chosen)
            decisions.append(decision)
        self.group = None
        return tuple(decisions)

    def _publish(self, id: str, values: list[Any]) -> None:
        instance = self.all_instances[id]
        attempt = instance["attempts"][-1]
        frozen = next(f for f in self.frozen if f["stage"] == instance["stage"])
        state = "completed" if values else "completed-zero"
        instance.update(state=state, failure=None)
        attempt.update(state=state, failure=None)
        for index, value in enumerate(values):
            payload = payload_bytes(value)
            lineage = {"workflowDigest": self.workflow_digest, "execution": "synthetic-execution",
                       "stage": instance["stage"], "instance": id,
                       **{name: pin for name, pin in frozen.items() if name not in {"stage", "runtimeDigest"}},
                       "preparationDigest": attempt["preparationDigest"],
                       "auditDigest": attempt["auditDigest"], "outputPointer": "/items", "index": index,
                       "rootCaseDigest": sha(self.root_case), "caseDigest": instance["caseDigest"],
                       "parentRecord": instance["parentRecord"], "selectionDigest": instance["selectionDigest"],
                       "relation": {"label": "synthetic-parent", "direction": "output-to-parent"},
                       "influence": {"classes": ["generated"], "generatedInfluence": True}}
            record = {"outputRecordVersion": 1, "payloadDigest": sha(payload), "lineage": lineage}
            raw = canon(record)
            pin = sha(raw)
            self.outputs[pin] = (record, payload)
            base = f"outputs/{instance['stage']}/{id}/{index}/"
            self.artifacts.update({base + "record.json": raw, base + "payload.json": payload})
            self.sets[instance["stage"]].append(pin)

    def select(self, upstream: str, selected: tuple[str, ...], child_ids: tuple[str, ...], *,
               fork: bool = False) -> Decision:
        """Synthetic reviewed selection/fork. All descendants retire; all other stages survive."""
        if self.group is not None or self.pending:
            raise ProbeError("resolve the current reservation/group before selecting")
        if upstream not in self.sets or len(set(selected)) != len(selected):
            raise ProbeError("invalid synthetic selection")
        stage = next(s for s in self.stages if s.id == upstream)
        if stage.parent is not None and (self.selections[stage.parent] is None
                                         or "refusal" in self.selections[stage.parent]):
            raise ProbeError("blocked synthetic stages cannot select")
        offered = self.sets[upstream]
        if [pin for pin in offered if pin in selected] != list(selected):
            raise ProbeError("selection must be a subset in offered order")
        previous = self.selections[upstream]
        if previous is not None and "refusal" not in previous and not fork:
            raise ProbeError("consumed selections require an explicit fork")
        if fork and (previous is None or "refusal" in previous):
            raise ProbeError("fork requires a consumed selection")
        consumers = [s for s in self.stages if s.parent == upstream]
        if not consumers or len(child_ids) != len(consumers) * len(selected):
            raise ProbeError("child ID plan must cover all direct consumer slots")
        if len(self.all_instances) + len(child_ids) > self.limits.max_instances:
            raise ProbeError("pre-ID count refusals are outside this byte-accounting experiment")
        if len(set(child_ids)) != len(child_ids) or any(id in self.planned_ids or not ID.fullmatch(id)
                                                      for id in child_ids):
            raise ProbeError("prospective IDs must be valid and fresh across retained history")
        revision = self.selection_revisions[upstream] + 1
        if revision > 16:
            raise RecordingUnavailable("synthetic selection revision bound")
        selection = {"selectionVersion": 1, "workflowDigest": self.workflow_digest,
                     "execution": "synthetic-execution", "upstreamStage": upstream,
                     "outputSetDigest": sha(canon(self._set(upstream))), "selected": list(selected),
                     "mode": "reviewer", "revision": revision,
                     "review": {"actor": "synthetic reviewer", "assertion": "synthetic selection", "at": AT}}
        common = copy.deepcopy(self)
        common._epoch("fork" if fork else "selection", {"upstreamStage": upstream,
                       "revision": revision, "selectionCoreDigest": sha(canon(selection)),
                       "childIds": list(child_ids)})
        common.selection_revisions[upstream] = revision
        common.planned_ids.update(child_ids)
        common.reservation_epoch = common.proof["epochBlocks"][-1][-1]["number"]
        if fork:
            descendants = {upstream}
            for stage in self.stages:
                if stage.parent in descendants:
                    descendants.add(stage.id)
            descendants.remove(upstream)
            common.active = [id for id in common.active
                             if common.all_instances[id]["stage"] not in descendants]
            for stage in descendants:
                common.sets[stage], common.selections[stage] = [], None
        accepted, refused = copy.deepcopy(common), copy.deepcopy(common)
        path = f"selections/{upstream}/{revision}.json"
        accepted.selections[upstream] = selection
        accepted.artifacts[path] = canon(selection)
        offset = 0
        for consumer in consumers:
            for pin in selected:
                id = child_ids[offset]
                offset += 1
                case = payload_bytes({"parent": dialect.read_document(self.outputs[pin][1], "synthetic parent")})
                accepted._instance(id, consumer.id, pin, sha(canon(selection)), case)
                accepted.pending.append(id)
        refused_selection = {**selection, "refusal": "limit-exceeded"}
        refused.selections[upstream] = refused_selection
        refused.artifacts[path] = canon(refused_selection)
        decision = Decision(accepted.snapshot(), refused.snapshot(), self.limits)
        if decision.outcome == "recording-unavailable":
            raise RecordingUnavailable("synthetic selection/refusal cannot fit")
        chosen = accepted if decision.outcome == "accepted" else refused
        chosen.decisions.append(decision)
        self._adopt(chosen)
        return decision


def boundary_probe(limit: int) -> tuple[Probe, Decision]:
    """A measured one-output example; all artifacts are explicitly synthetic."""
    probe = Probe(limits=Limits(max_bytes=limit))
    probe.begin_group()
    decision, = probe.finish_group([Result("root-instance", (b'{"value":"synthetic"}',))])
    return probe, decision


def selection_probe(limit: int, child_id: str) -> tuple[Probe, Decision]:
    """One explicitly chosen child ID; no allocator or real projection is inferred."""
    probe = Probe((Stage("companies"), Stage("people", "companies")),
                  limits=Limits(max_bytes=limit))
    probe.begin_group()
    probe.finish_group([Result("root-instance", (b'{"name":"synthetic organisation"}',))])
    decision = probe.select("companies", tuple(probe.sets["companies"]), (child_id,))
    return probe, decision


def examples() -> dict[str, Any]:
    """Return measured arithmetic examples, never a workflow-verification report."""
    limit = boundary_probe(1_000_000_000)[1].accepted.total_bytes
    # maxBytes is itself serialized. Recompute the digit-width-dependent boundary.
    for _ in range(8):
        measured = boundary_probe(limit)[1].accepted.total_bytes
        if measured == limit:
            break
        limit = measured
    else:
        raise ProbeError("synthetic boundary did not stabilize")
    accepted = boundary_probe(limit)[1]
    over = boundary_probe(limit - 1)[1]
    selection_limit = selection_probe(1_000_000_000, "p")[1].accepted.total_bytes
    for _ in range(8):
        measured = selection_probe(selection_limit, "p")[1].accepted.total_bytes
        if measured == selection_limit:
            break
        selection_limit = measured
    else:
        raise ProbeError("synthetic selection boundary did not stabilize")
    short = selection_probe(selection_limit, "p")[1]
    long = selection_probe(selection_limit, "p" + "x" * 63)[1]
    return {"experiment": "synthetic-only; not workflow verification",
            "acceptedAtExactLimit": {"maxBytes": limit, "acceptedBytes": accepted.accepted.total_bytes,
                                     "refusedBytes": accepted.refused.total_bytes,
                                     "outcome": accepted.outcome},
            "oneByteOver": {"maxBytes": limit - 1, "acceptedBytes": over.accepted.total_bytes,
                            "refusedBytes": over.refused.total_bytes, "outcome": over.outcome},
            "proofBytesIncludingSidecar": sum(len(raw) for path, raw in over.accepted.files
                                               if path in {"admission-proof.json", "admission-proof.sha256"}),
            "acceptedFiles": len(accepted.accepted.files), "refusedFiles": len(over.refused.files),
            "prospectiveIdBoundary": {"maxBytes": selection_limit,
                                      "shortAcceptedBytes": short.accepted.total_bytes,
                                      "shortOutcome": short.outcome,
                                      "longAcceptedBytes": long.accepted.total_bytes,
                                      "longRefusedBytes": long.refused.total_bytes,
                                      "longOutcome": long.outcome}}


if __name__ == "__main__":
    print(json.dumps(examples(), sort_keys=True, indent=2))
