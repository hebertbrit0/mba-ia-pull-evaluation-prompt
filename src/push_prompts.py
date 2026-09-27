"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_NAME = "bug_to_user_story_v2"
INPUT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB")
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB não configurado no .env")
        return False

    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data["user_prompt"]

    client = Client()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt),
    ])

    tags = list(dict.fromkeys(prompt_data.get("tags", []) + prompt_data.get("techniques_applied", [])))

    try:
        url = client.push_prompt(
            f"{username}/{prompt_name}",
            object=prompt,
            is_public=True,
            description=prompt_data.get("description", ""),
            tags=tags,
        )
    except Exception as e:
        print(f"❌ Erro ao fazer push do prompt no LangSmith: {e}")
        return False

    print(f"✅ Prompt publicado em: {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = ["description", "system_prompt", "user_prompt", "version"]
    for field in required_fields:
        if not prompt_data.get(field):
            errors.append(f"Campo obrigatório faltando ou vazio: {field}")

    user_prompt = prompt_data.get("user_prompt", "")
    if "{bug_report}" not in user_prompt:
        errors.append("user_prompt precisa conter a variável {bug_report}")

    techniques = prompt_data.get("techniques_applied", [])
    if not techniques:
        errors.append("Nenhuma técnica listada em techniques_applied")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("Push de Prompts para o LangSmith")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    prompts_file = load_yaml(str(INPUT_PATH))
    if not prompts_file:
        return 1

    prompt_data = prompts_file.get(PROMPT_NAME)
    if not prompt_data:
        print(f"❌ Prompt '{PROMPT_NAME}' não encontrado em {INPUT_PATH}")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    if not push_prompt_to_langsmith(PROMPT_NAME, prompt_data):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
