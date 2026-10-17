"""Synthetic accounting experiments, not Runtime/operation fixtures or workflow conformance."""
from __future__ import annotations

import copy
import json
import unittest

from tools import workflow_admission_probe as study


def children(limit: int = 1_000_000_000, *, count: int = 2,
             max_records: int = 4096, start: bool = True) -> study.Probe:
    probe = study.Probe((study.Stage("companies"), study.Stage("people", "companies")),
                        limits=study.Limits(max_bytes=limit, max_records=max_records))
    probe.begin_group()
    probe.finish_group([study.Result("root-instance", tuple(
        ('{"name":"company-' + str(i) + '"}').encode() for i in range(count)))])
    probe.select("companies", tuple(probe.sets["companies"]),
                 tuple("child-" + str(i) for i in range(count)))
    if start:
        probe.begin_group()
    return probe


def retry_example(limit: int) -> tuple[study.Probe, study.Decision]:
    probe = children(limit)
    decisions = probe.finish_group([
        study.Result("child-0", state="interrupted", response="uncertain synthetic response"),
        study.Result("child-1", ((json.dumps({"value": "x" * 4000})).encode(),)),
    ])
    return probe, decisions[0]


def measured_output_boundary() -> int:
    return study.examples()["acceptedAtExactLimit"]["maxBytes"]


class WorkflowAdmissionProbeTests(unittest.TestCase):
    def test_actual_candidate_fits_exactly_and_one_byte_less_refuses_in_probe(self) -> None:
        limit = measured_output_boundary()
        _, exact = study.boundary_probe(limit)
        _, over = study.boundary_probe(limit - 1)
        self.assertEqual(limit, exact.accepted.total_bytes)
        self.assertEqual(limit, over.accepted.total_bytes)
        self.assertTrue(exact.check_claim("accepted"))
        self.assertFalse(exact.check_claim("refused"))
        self.assertTrue(over.check_claim("refused"))
        self.assertLessEqual(over.refused.total_bytes, limit - 1)
        self.assertEqual(exact.accepted.as_files()["admission-proof.json"],
                         exact.refused.as_files()["admission-proof.json"])
        self.assertEqual(over.accepted.as_files()["admission-proof.sha256"],
                         over.refused.as_files()["admission-proof.sha256"])

    def test_proof_bytes_and_hash_sidecar_cannot_be_exempted(self) -> None:
        limit = measured_output_boundary() - 1
        _, decision = study.boundary_probe(limit)
        files = decision.accepted.as_files()
        proof_cost = len(files["admission-proof.json"]) + len(files["admission-proof.sha256"])
        self.assertEqual(72, len(files["admission-proof.sha256"]))
        self.assertLessEqual(decision.accepted.total_bytes - proof_cost, limit)
        self.assertGreater(decision.accepted.total_bytes, limit)
        self.assertEqual("refused", decision.outcome)

    def test_explicit_long_id_can_cross_the_same_measured_selection_boundary(self) -> None:
        limit = study.examples()["prospectiveIdBoundary"]["maxBytes"]
        _, short = study.selection_probe(limit, "p")
        _, long = study.selection_probe(limit, "p" + "x" * 63)
        self.assertEqual(limit, short.accepted.total_bytes)
        self.assertEqual("accepted", short.outcome)
        self.assertGreater(long.accepted.total_bytes, limit)
        self.assertLessEqual(long.refused.total_bytes, limit)
        self.assertEqual("refused", long.outcome)

    def test_unfittable_initial_proof_is_recording_unavailable(self) -> None:
        size = study.Probe().snapshot().total_bytes
        for _ in range(8):
            measured = study.Probe(limits=study.Limits(max_bytes=size)).snapshot().total_bytes
            if measured == size:
                break
            size = measured
        snapshot = study.Probe(limits=study.Limits(max_bytes=size)).snapshot()
        proof_cost = sum(len(raw) for path, raw in snapshot.files if path.startswith("admission-proof."))
        self.assertLess(snapshot.total_bytes - proof_cost, size - 1)
        with self.assertRaises(study.RecordingUnavailable):
            study.Probe(limits=study.Limits(max_bytes=size - 1))

    def test_equal_contents_at_distinct_paths_count_twice(self) -> None:
        probe = study.Probe()
        probe.begin_group()
        probe.finish_group([study.Result("root-instance", (b'{"same":true}', b'{"same":true}'))])
        snapshot = probe.snapshot()
        files = snapshot.as_files()
        first = files["outputs/root/root-instance/0/payload.json"]
        second = files["outputs/root/root-instance/1/payload.json"]
        self.assertEqual(first, second)
        self.assertEqual(files["root-case.json"], files["instances/root-instance/case.json"])
        self.assertEqual(2, snapshot.records)
        self.assertEqual(sum(map(len, files.values())), snapshot.total_bytes)
        deduplicated = {study.sha(raw): raw for raw in files.values()}
        self.assertLessEqual(sum(map(len, deduplicated.values())) + len(first), snapshot.total_bytes)

    def test_required_control_files_have_computed_pins_and_proposed_selectors(self) -> None:
        probe, decision = study.boundary_probe(measured_output_boundary())
        files = decision.accepted.as_files()
        workflow, execution = json.loads(files["workflow.json"]), json.loads(files["execution.json"])
        self.assertEqual(2, workflow["workflowVersion"])
        self.assertEqual(2, execution["executionVersion"])
        self.assertEqual(1, json.loads(files["admission-proof.json"])["admissionProofVersion"])
        self.assertEqual(study.sha(files["admission-proof.json"]), execution["admissionProofDigest"])
        for name in ("workflow", "execution", "admission-proof"):
            self.assertEqual((study.sha(files[name + ".json"]) + "\n").encode(),
                             files[name + ".sha256"])
        self.assertEqual(probe.sets["root"], json.loads(files["sets/root.json"])["records"])
        self.assertEqual(study.canon(json.loads(files["execution.json"])), files["execution.json"])

    def test_actual_file_bound_includes_output_pair(self) -> None:
        probe = study.Probe(limits=study.Limits(max_files=21))
        probe.begin_group()
        decision, = probe.finish_group([study.Result("root-instance", (b'{"value":"synthetic"}',))])
        self.assertEqual(22, len(decision.accepted.files))
        self.assertEqual(20, len(decision.refused.files))
        self.assertEqual("refused", decision.outcome)

    def test_payload_negative_zero_and_preparation_escapes_survive(self) -> None:
        raw = '{"n":-0,"text":"<&>\u2028\u2029"}'.encode()
        probe = study.Probe(root_case=raw)
        probe.begin_group()
        probe.finish_group([study.Result("root-instance", (raw,))])
        files = probe.snapshot().as_files()
        payload = files["outputs/root/root-instance/0/payload.json"]
        parsed = study.dialect.read_document(raw, "synthetic literal example")
        self.assertEqual(study.payload_bytes(parsed), payload)
        self.assertIn(b'"n":-0', payload)
        self.assertIn(b'\\u003c\\u0026\\u003e\\u2028\\u2029', payload)
        self.assertNotEqual(study.canon(parsed), payload)
        self.assertEqual(payload, files["root-case.json"])
        for name in ("sources.json", "preparation.json", "audit.json"):
            prefix = "instances/root-instance/attempts/1/"
            self.assertIn(files[prefix + name], files[prefix + "run.json"])

    def test_reverse_physical_completion_has_identical_logical_prefixes(self) -> None:
        first, second = children(), children()
        results = [study.Result("child-0", (b'{"person":"a"}',)),
                   study.Result("child-1", (b'{"person":"b"}',))]
        decisions_a = first.finish_group(results)
        decisions_b = second.finish_group(reversed(results))
        self.assertEqual(first.snapshot(), second.snapshot())
        self.assertEqual(decisions_a, decisions_b)
        early_files = decisions_a[0].accepted.as_files()
        self.assertNotIn("instances/child-1/attempts/1/run.json", early_files)
        epoch = json.loads(early_files["admission-proof.json"])["epochBlocks"][-1][-1]
        self.assertEqual(["child-0", "child-1"], [m["instance"] for m in epoch["starts"]])
        self.assertTrue(all(m["number"] == 1 for m in epoch["starts"]))
        self.assertEqual(["child-0"], [o["instance"] for o in epoch["results"]])
        self.assertEqual(["evaluated"], [o["state"] for o in epoch["results"]])

    def test_result_membership_cannot_omit_repeat_or_replace_a_begun_attempt(self) -> None:
        probe = children()
        before = probe.snapshot()
        for results in ([study.Result("child-0")],
                        [study.Result("child-0"), study.Result("child-0")],
                        [study.Result("child-0"), study.Result("foreign")]):
            with self.subTest(instances=[r.instance for r in results]):
                with self.assertRaisesRegex(study.ProbeError, "exactly once"):
                    probe.finish_group(results)
                self.assertEqual(before, probe.snapshot())

    def test_future_large_sibling_cannot_justify_an_earlier_false_refusal(self) -> None:
        probe = children()
        later = study.Result("child-1", (json.dumps({"value": "x" * 5000}).encode(),))
        before = probe.snapshot()
        with self.assertRaisesRegex(study.ProbeError, "original candidate"):
            probe.finish_group([later, study.Result("child-0", (b'{"person":"a"}',))],
                               claims=(("child-0", "refused"),))
        # Rejected at the first canonical candidate; later material never becomes its baseline.
        self.assertEqual(before, probe.snapshot())

    def test_retry_appends_history_without_remeasuring_old_refusal(self) -> None:
        _, measured = retry_example(1_000_000_000)
        limit = measured.accepted.total_bytes - 1
        for _ in range(8):
            _, measured = retry_example(limit)
            corrected = measured.accepted.total_bytes - 1
            if corrected == limit:
                break
            limit = corrected
        probe, refusal = retry_example(limit)
        self.assertEqual("refused", refusal.outcome)
        frozen = copy.deepcopy(refusal)
        previous_proof = probe.snapshot().as_files()["admission-proof.json"]
        probe.begin_group(retry="child-0")
        probe.finish_group([study.Result("child-0")])
        self.assertEqual(frozen, refusal)
        self.assertEqual("failed", probe.all_instances["child-1"]["state"])
        self.assertEqual("completed-zero", probe.all_instances["child-0"]["state"])
        epochs = probe.proof["epochBlocks"][-1]
        self.assertEqual("retry", epochs[-1]["kind"])
        self.assertEqual(study.sha(previous_proof), epochs[-1]["previousProofDigest"])
        self.assertNotIn("instances/child-0/attempts/2/run.json", refusal.accepted.as_files())
        self.assertEqual(2, len(probe.all_instances["child-0"]["attempts"]))

    def test_later_retry_does_not_change_an_old_fitting_candidate(self) -> None:
        probe, fitting = retry_example(1_000_000_000)
        original = copy.deepcopy(fitting)
        self.assertTrue(fitting.check_claim("accepted"))
        probe.begin_group(retry="child-0")
        probe.finish_group([study.Result("child-0", response="later synthetic material" * 100)])
        self.assertEqual(original, fitting)
        self.assertFalse(fitting.check_claim("refused"))

    def test_stops_have_no_attempt_and_deferred_first_work_needs_explicit_begin(self) -> None:
        probe = children()
        # Use a fresh reserved group; the helper's group has already begun its actual attempts.
        with self.assertRaises(study.ProbeError):
            probe.begin_group(stops=(("child-0", "cancelled"),))
        probe = children(start=False)
        probe.begin_group(stops=(("child-0", "interrupted"), ("child-1", "cancelled")))
        self.assertEqual([], probe.all_instances["child-0"]["attempts"])
        self.assertIsNone(probe.group)
        probe.begin_group(retry="child-0")
        self.assertEqual(1, len(probe.all_instances["child-0"]["attempts"]))
        probe.finish_group([study.Result("child-0")])
        self.assertIsNone(probe.all_instances["child-0"]["attempts"][0]["retry"])
        with self.assertRaisesRegex(study.ProbeError, "no-op"):
            study.Probe().begin_group(stops=(("root-instance", "interrupted"),))
        cancelled = study.Probe()
        cancelled.begin_group(stops=(("root-instance", "cancelled"),))
        self.assertEqual("cancelled", cancelled.all_instances["root-instance"]["state"])
        self.assertEqual([], cancelled.all_instances["root-instance"]["attempts"])
        with self.assertRaises(study.ProbeError):
            cancelled.begin_group(retry="root-instance")

    def test_cutoff_suppresses_no_run_begin_but_preserves_uncertainty(self) -> None:
        probe = children(count=3, max_records=4)
        decision, = probe.finish_group([
            study.Result("child-2", state="interrupted", response="uncertain received bytes"),
            study.Result("child-1", state="not-acquired"),
            study.Result("child-0", (b'{"person":"a"}', b'{"person":"b"}')),
        ])
        self.assertEqual("refused", decision.outcome)
        suppressed = probe.all_instances["child-1"]["attempts"][0]
        self.assertEqual("limit-exceeded", suppressed["failure"])
        self.assertIsNone(suppressed["runDigest"])
        self.assertEqual("interrupted", probe.all_instances["child-2"]["state"])
        self.assertIn("instances/child-2/attempts/1/sources.json", probe.snapshot().as_files())
        no_cutoff = study.Probe()
        no_cutoff.begin_group()
        with self.assertRaisesRegex(study.ProbeError, "proved cutoff"):
            no_cutoff.finish_group([study.Result("root-instance", state="not-acquired")])

    def test_consumed_root_cannot_be_retried_under_the_same_execution(self) -> None:
        probe = study.Probe((study.Stage("root"), study.Stage("child", "root")))
        probe.begin_group()
        probe.finish_group([study.Result("root-instance", state="interrupted")])
        probe.select("root", (), ())
        with self.assertRaisesRegex(study.ProbeError, "new execution"):
            probe.begin_group(retry="root-instance")

    def test_first_resume_of_deferred_sibling_requires_fork_after_set_consumption(self) -> None:
        probe = study.Probe((study.Stage("root"), study.Stage("people", "root"),
                             study.Stage("followup", "people")))
        probe.begin_group()
        probe.finish_group([study.Result("root-instance", (b'{"org":"a"}', b'{"org":"b"}'))])
        probe.select("root", tuple(probe.sets["root"]), ("person-a", "person-b"))
        probe.begin_group(stops=(("person-b", "interrupted"),))
        probe.finish_group([study.Result("person-a", (b'{"person":"a"}',))])
        probe.select("people", tuple(probe.sets["people"]), ("followup-a",))
        probe.begin_group(stops=(("followup-a", "cancelled"),))
        before = probe.snapshot()
        self.assertEqual([], probe.all_instances["person-b"]["attempts"])
        with self.assertRaisesRegex(study.ProbeError, "affected-stage fork"):
            probe.begin_group(retry="person-b")
        self.assertEqual(before, probe.snapshot())
        self.assertEqual("interrupted", probe.all_instances["person-b"]["state"])
        self.assertEqual([], probe.all_instances["person-b"]["attempts"])

    def test_consumed_deferred_slot_can_be_carried_unchanged_while_another_stage_resumes(self) -> None:
        probe = study.Probe((study.Stage("root"), study.Stage("left", "root"),
                             study.Stage("right", "root"), study.Stage("anchor", "root"),
                             study.Stage("leaf", "left")))
        probe.begin_group()
        probe.finish_group([study.Result("root-instance", (b'{"org":"synthetic"}',))])
        probe.select("root", tuple(probe.sets["root"]), ("left-a", "right-a", "anchor-a"))
        probe.begin_group(stops=(("left-a", "interrupted"), ("right-a", "interrupted")))
        probe.finish_group([study.Result("anchor-a")])
        probe.select("left", (), ())
        carried = copy.deepcopy(probe.all_instances["left-a"])
        probe.begin_group(retry="right-a")
        probe.finish_group([study.Result("right-a")])
        self.assertEqual(carried, probe.all_instances["left-a"])
        self.assertEqual(["left-a"], probe.proof["epochBlocks"][-1][-1]["deferred"])
        self.assertEqual("completed-zero", probe.all_instances["right-a"]["state"])

    def test_revised_unconsumed_selection_retains_its_old_refusal_history(self) -> None:
        def first(limit: int) -> tuple[study.Probe, study.Decision]:
            probe = study.Probe((study.Stage("root"), study.Stage("child", "root")),
                                limits=study.Limits(max_bytes=limit))
            probe.begin_group()
            probe.finish_group([study.Result("root-instance", tuple(
                json.dumps({"name": str(i)}).encode() for i in range(10)))])
            return probe, probe.select("root", tuple(probe.sets["root"]),
                                       tuple("a-" + str(i) for i in range(10)))
        limit = first(1_000_000_000)[1].accepted.total_bytes - 1
        for _ in range(8):
            corrected = first(limit)[1].accepted.total_bytes - 1
            if corrected == limit:
                break
            limit = corrected
        probe, refused = first(limit)
        frozen = copy.deepcopy(refused)
        old = probe.snapshot().as_files()["selections/root/1.json"]
        accepted = probe.select("root", (probe.sets["root"][0],), ("new-child",))
        self.assertEqual("refused", refused.outcome)
        self.assertEqual("accepted", accepted.outcome)
        self.assertEqual(frozen, refused)
        self.assertEqual(old, probe.snapshot().as_files()["selections/root/1.json"])
        self.assertIn("selections/root/2.json", probe.snapshot().as_files())
        self.assertEqual(2, probe.snapshot().instances)

    def test_byte_refused_prospective_ids_cannot_be_reused_and_reserve_no_capacity(self) -> None:
        refused_ids = tuple("refused-" + str(i) for i in range(10))

        def first(limit: int) -> tuple[study.Probe, study.Decision]:
            probe = study.Probe((study.Stage("root"), study.Stage("child", "root")),
                                limits=study.Limits(max_bytes=limit, max_instances=11))
            probe.begin_group()
            probe.finish_group([study.Result("root-instance", tuple(
                json.dumps({"name": str(i)}).encode() for i in range(10)))])
            return probe, probe.select("root", tuple(probe.sets["root"]), refused_ids)

        limit = first(1_000_000_000)[1].accepted.total_bytes - 1
        for _ in range(8):
            corrected = first(limit)[1].accepted.total_bytes - 1
            if corrected == limit:
                break
            limit = corrected
        probe, refused = first(limit)
        self.assertEqual("refused", refused.outcome)
        self.assertEqual({"root-instance"}, set(probe.all_instances))
        self.assertEqual(1, probe.snapshot().instances)
        before = probe.snapshot()
        with self.assertRaisesRegex(study.ProbeError, "fresh"):
            probe.select("root", (probe.sets["root"][0],), (refused_ids[0],))
        self.assertEqual(before, probe.snapshot())
        self.assertEqual(1, probe.snapshot().instances)
        accepted = probe.select("root", (probe.sets["root"][0],), ("fresh-child",))
        self.assertEqual("accepted", accepted.outcome)
        self.assertEqual(2, probe.snapshot().instances)
        self.assertGreater(len(probe.planned_ids), probe.limits.max_instances)

    def test_fork_keeps_retired_artifacts_counts_and_unaffected_sibling(self) -> None:
        probe = study.Probe((study.Stage("root"), study.Stage("left", "root"),
                             study.Stage("right", "root"), study.Stage("leaf", "left")))
        probe.begin_group()
        probe.finish_group([study.Result("root-instance", (b'{"name":"org"}',))])
        probe.select("root", tuple(probe.sets["root"]), ("left-old", "right-old"))
        probe.begin_group()
        probe.finish_group([study.Result("left-old", (b'{"name":"left"}',)),
                            study.Result("right-old", (b'{"name":"right"}',))])
        selected = tuple(probe.sets["left"])
        probe.select("left", selected, ("leaf-old",))
        probe.begin_group()
        probe.finish_group([study.Result("leaf-old", (b'{"name":"old leaf"}',))])
        before = probe.snapshot()
        sibling = copy.deepcopy(probe.all_instances["right-old"])
        decision = probe.select("left", selected, ("leaf-new",), fork=True)
        after = probe.snapshot()
        self.assertEqual("accepted", decision.outcome)
        self.assertNotIn("leaf-old", probe.active)
        self.assertIn("leaf-new", probe.active)
        self.assertIn("right-old", probe.active)
        self.assertEqual(sibling, probe.all_instances["right-old"])
        self.assertEqual(before.instances + 1, after.instances)
        self.assertEqual(before.records, after.records)
        for path, raw in before.files:
            if path.startswith(("instances/", "outputs/", "selections/")):
                self.assertEqual(raw, after.as_files()[path])
        self.assertEqual({"instances/leaf-new/case.json", "selections/left/2.json"},
                         set(after.as_files()) - set(before.as_files()))
        self.assertEqual(1, sum(path == "execution.json" for path, _ in after.files))
        self.assertEqual(study.sha(before.as_files()["admission-proof.json"]),
                         probe.proof["epochBlocks"][-1][-1]["previousProofDigest"])
        execution = json.loads(after.as_files()["execution.json"])
        self.assertEqual(4, len(execution["instances"]))
        self.assertEqual(5, after.instances)
        probe.begin_group(stops=(("leaf-new", "cancelled"),))
        with self.assertRaisesRegex(study.ProbeError, "fresh"):
            probe.select("left", selected, ("leaf-old",), fork=True)


if __name__ == "__main__":
    unittest.main()
