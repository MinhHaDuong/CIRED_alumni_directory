# tests/regression/test-askCIRED.py
import subprocess
from pathlib import Path
import pytest


@pytest.mark.slow
def test_askCIRED(tmp_path):
    script_src = Path("1_Scraping/askCIRED.py").resolve()
    script_dst = tmp_path / "askCIRED.py"
    script_dst.symlink_to(script_src)

    output = tmp_path / "askCIRED.vcf"
    subprocess.run(["python", "askCIRED.py"], cwd=tmp_path, check=True)

    expected = Path("tests/expected/askCIRED.vcf")

    def normalized_lines(path):
        with open(path, encoding="utf-8") as f:
            return [line for line in f if not line.startswith("REV:")] # Ignore timestamp lines

    actual_lines = normalized_lines(output)
    expected_lines = normalized_lines(expected)

    assert actual_lines == expected_lines
