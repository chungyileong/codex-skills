import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "advisor-setup" / "scripts" / "configure_advisor.py"


class ConfigureAdvisorTest(unittest.TestCase):
    def run_script(self, directory, *arguments):
        env = {**os.environ, "CODEX_HOME": directory}
        return subprocess.run(
            [sys.executable, SCRIPT, *arguments],
            env=env,
            capture_output=True,
            text=True,
        )

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

    def test_status_rejects_malformed_config_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "agents" / "advisor.toml"
            target.parent.mkdir()
            target.write_text("not = valid = toml\n")
            before = target.read_bytes()

            result = self.run_script(directory, "--status")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid TOML", result.stdout)
            self.assertEqual(before, target.read_bytes())

    def test_status_reports_missing_config(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_script(directory, "--status")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("installed: no", result.stdout)
            self.assertIn("validation: missing", result.stdout)

    def test_existing_invalid_config_is_not_overwritten_by_default_setup(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "agents" / "advisor.toml"
            target.parent.mkdir()
            target.write_text("name = \"broken\"\n")
            before = target.read_bytes()

            result = self.run_script(directory)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("use --reset", result.stderr)
            self.assertEqual(before, target.read_bytes())

    def test_status_rejects_unsupported_model(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "CODEX_HOME": directory}
            codex = Path(directory) / "codex"
            codex.write_text("#!/bin/sh\nprintf '%s' '{\"models\":[{\"slug\":\"supported\"}]}'\n")
            codex.chmod(0o700)
            env["PATH"] = f"{directory}:{env['PATH']}"
            target = Path(directory) / "agents" / "advisor.toml"
            target.parent.mkdir()
            target.write_text(
                (Path(__file__).parents[1] / "skills" / "advisor-setup" / "assets" / "advisor.toml")
                .read_text()
                .replace('model = "gpt-5.6-sol"', 'model = "unsupported"')
            )

            result = subprocess.run(
                [sys.executable, SCRIPT, "--status"], env=env, capture_output=True, text=True
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("model is not available", result.stdout)

    def test_status_accepts_inherited_model_and_reasoning(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "agents" / "advisor.toml"
            target.parent.mkdir()
            target.write_text(
                (Path(__file__).parents[1] / "skills" / "advisor-setup" / "assets" / "advisor.toml")
                .read_text()
                .replace('model = "gpt-5.6-sol"\n', "")
                .replace('model_reasoning_effort = "medium"\n', "")
            )

            result = self.run_script(directory, "--status")

            self.assertEqual(result.returncode, 0)
            self.assertIn("validation: valid", result.stdout)

    def test_status_rejects_wrong_agent_identity_or_sandbox(self):
        template = (Path(__file__).parents[1] / "skills" / "advisor-setup" / "assets" / "advisor.toml").read_text()
        template = template.replace('model = "gpt-5.6-sol"\n', "")
        template = template.replace('model_reasoning_effort = "medium"\n', "")

        for field, value, message in (
            ("name", '"other"', 'name must be "advisor"'),
            ("sandbox_mode", '"workspace-write"', 'sandbox_mode must be "read-only"'),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "agents" / "advisor.toml"
                target.parent.mkdir()
                target.write_text(template.replace(f'{field} = "advisor"' if field == "name" else f'{field} = "read-only"', f"{field} = {value}"))

                result = self.run_script(directory, "--status")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stdout)

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
