from pathlib import Path

from evaluations.testset import GENERATION_EVAL_CASES


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_RESOURCES = PROJECT_ROOT / "eval_resources"


def test_eval_resources_files_exist():
    assert (EVAL_RESOURCES / "README.md").exists()
    assert (EVAL_RESOURCES / "METRICS.md").exists()
    assert (EVAL_RESOURCES / "eval_dataset.yaml").exists()


def test_eval_dataset_documents_all_python_cases():
    dataset_text = (EVAL_RESOURCES / "eval_dataset.yaml").read_text(encoding="utf-8")

    for case in GENERATION_EVAL_CASES:
        assert f"id: {case.id}" in dataset_text
        for term in case.expected_terms:
            assert term in dataset_text

