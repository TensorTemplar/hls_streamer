import pytest

from app.configuration import FeatureFlags


# Test cases
@pytest.mark.parametrize(
    "env_value, expected_result",
    [
        ("True", True),
        ("true", True),
        ("1", True),
        ("False", False),
        ("false", False),
        ("0", False),
        ("yes", True),
        ("no", False),
        (None, False),
    ],
)
def test_feature_flags_parsing(monkeypatch, env_value, expected_result):
    # Set environment variable
    if env_value is not None:
        monkeypatch.setenv("FEATURE_ENABLE_PROMETHEUS", env_value)
    else:
        monkeypatch.delenv("FEATURE_ENABLE_PROMETHEUS", raising=False)

    # Instantiate and test the settings
    feature_flags = FeatureFlags()
    assert feature_flags.enable_prometheus == expected_result
