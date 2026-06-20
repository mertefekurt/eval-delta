from eval_delta.stats import bootstrap_mean_interval


def test_bootstrap_interval_is_deterministic():
    values = [-0.2, -0.1, 0.0, 0.1]

    first = bootstrap_mean_interval(values, confidence=0.95, samples=500, seed=7)
    second = bootstrap_mean_interval(values, confidence=0.95, samples=500, seed=7)

    assert first == second


def test_single_value_interval_is_exact():
    assert bootstrap_mean_interval([-0.25], confidence=0.95, samples=100, seed=1) == (
        -0.25,
        -0.25,
    )
