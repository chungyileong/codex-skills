import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "advisor-setup" / "scripts" / "configure_advisor.py"


class ConfigureAdvisorTest(unittest.TestCase):
    def test_initialize_customize_inherit_and_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "CODEX_HOME": directory}
            target = Path(directory) / "agents" / "advisor.toml"
            codex = Path(directory) / "codex"
            codex.write_text("#!/bin/sh\nprintf '%s' '{\"models\":[{\"slug\":\"gpt-5.6-sol\",\"display_name\":\"GPT-5.6-Sol\"},{\"slug\":\"custom-model\",\"display_name\":\"Custom Model\"}]}'\n")
            codex.chmod(0o700)
            env["PATH"] = f"{directory}:{env['PATH']}"

            subprocess.run([sys.executable, SCRIPT], env=env, check=True, capture_output=True, text=True)
            self.assertIn('model = "gpt-5.6-sol"', target.read_text())
            target.write_text(target.read_text().replace("Act as the", 'model = "prompt text"\nAct as the'))

            subprocess.run(
                [sys.executable, SCRIPT, "--model", "custom-model", "--reasoning", "high"],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            configured = target.read_text()
            self.assertIn('model = "custom-model"', configured)
            self.assertIn('model_reasoning_effort = "high"', configured)
            self.assertIn("developer_instructions", configured)
            self.assertIn('model = "prompt text"', configured)

            subprocess.run(
                [sys.executable, SCRIPT, "--inherit-model", "--inherit-reasoning"],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            inherited = target.read_text()
            header = inherited.split("developer_instructions", 1)[0]
            self.assertNotIn("\nmodel =", header)
            self.assertNotIn("\nmodel_reasoning_effort =", header)
            self.assertIn('model = "prompt text"', inherited)

            subprocess.run([sys.executable, SCRIPT, "--reset"], env=env, check=True, capture_output=True, text=True)
            self.assertTrue(target.with_name("advisor.toml.bak").exists())
            self.assertIn('model = "gpt-5.6-sol"', target.read_text())

    def test_model_display_name_is_written_as_canonical_slug(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "CODEX_HOME": directory}
            codex = Path(directory) / "codex"
            codex.write_text("#!/bin/sh\nprintf '%s' '{\"models\":[{\"slug\":\"gpt-5.6-sol\",\"display_name\":\"GPT-5.6-Sol\"}]}'\n")
            codex.chmod(0o700)
            env["PATH"] = f"{directory}:{env['PATH']}"

            subprocess.run(
                [sys.executable, SCRIPT, "--model", "GPT-5.6-Sol"],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('model = "gpt-5.6-sol"', (Path(directory) / "agents" / "advisor.toml").read_text())

    def test_model_spacing_is_canonicalized_to_slug(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "CODEX_HOME": directory}
            codex = Path(directory) / "codex"
            codex.write_text("#!/bin/sh\nprintf '%s' '{\"models\":[{\"slug\":\"gpt-5.6-sol\"}]}'\n")
            codex.chmod(0o700)
            env["PATH"] = f"{directory}:{env['PATH']}"

            subprocess.run(
                [sys.executable, SCRIPT, "--model", "gpt-5.6 sol"],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('model = "gpt-5.6-sol"', (Path(directory) / "agents" / "advisor.toml").read_text())


if __name__ == "__main__":
    unittest.main()
