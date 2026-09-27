"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def prompt_data():
    """Carrega o prompt otimizado (v2) que deve ser validado pelos testes."""
    data = load_prompts(str(PROMPT_FILE))
    key = next(iter(data))
    return data[key]

class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data
        assert prompt_data["system_prompt"].strip() != ""

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_data["system_prompt"].lower()
        assert "você é" in system_prompt or "voce e" in system_prompt

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data["system_prompt"].lower()
        assert "markdown" in system_prompt or "user story" in system_prompt

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data["system_prompt"].lower()
        has_example_section = "exemplo" in system_prompt or "example" in system_prompt
        techniques = [t.lower() for t in prompt_data.get("techniques_applied", [])]
        has_few_shot_technique = any("few-shot" in t for t in techniques)
        assert has_example_section and has_few_shot_technique

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert "TODO" not in prompt_data["system_prompt"]
        assert not any("TODO" in error for error in errors)

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert len(techniques) >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])