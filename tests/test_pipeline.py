from employee.models import Idea
from employee.pipeline import run_episode


CFG = {"gates": {"min_seeds": 2, "budget_tokens": 1000, "noise_floor": 0.005},
       "worker": {"timeout_s": 5, "seeds_per_stage": 2}}


def test_pipeline_fake_all_promoted(tmp_path):
    idea = Idea(name="d", title="t", hypothesis="h")
    summary = run_episode(idea, CFG, str(tmp_path / "j.jsonl"), fake=True)
    assert summary["fake"] is True
    assert set(summary["stages"]) == {"s1_implement", "s2_baseline_tune", "s3_explore", "s4_ablate"}
    assert all(v["promoted"] for v in summary["stages"].values())


def test_pipeline_hold_on_flat(tmp_path):
    # 噪声底抬高 -> s2 起 HOLD（fake metric 增量 0.001/seed，中位数差 0.001）
    cfg = {"gates": {"min_seeds": 2, "budget_tokens": 1000, "noise_floor": 5.0},
           "worker": {"timeout_s": 5, "seeds_per_stage": 2}}
    idea = Idea(name="d", title="t", hypothesis="h")
    summary = run_episode(idea, cfg, str(tmp_path / "j.jsonl"), fake=True)
    assert summary["stages"]["s2_baseline_tune"]["promoted"] is False
