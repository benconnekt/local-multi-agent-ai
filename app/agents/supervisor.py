
import re

from app.agents.registry import AGENTS


ROUTING_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (
        ("review", "audit", "inspect"),
        ("reviewer", "security"),
    ),
    (
        ("ui", "screen", "frontend", "flutter", "design"),
        ("designer", "developer", "tester", "reviewer"),
    ),
    (
        ("api", "backend", "database", "authentication"),
        ("architect", "developer", "tester", "security", "reviewer"),
    ),
    (
        ("deployment", "deploy", "docker", "ci/cd", "infrastructure"),
        ("architect", "devops", "security", "tester"),
    ),
)

DEFAULT_AGENTS = ("developer", "tester", "reviewer")


def matches_keyword(text: str, keyword: str) -> bool:
    pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def validate_agents(agent_ids: tuple[str, ...]) -> list[str]:
    unknown = set(agent_ids) - AGENTS.keys()

    if unknown:
        raise ValueError(
            f"Unknown agents: {sorted(unknown)}"
        )

    return list(agent_ids)


def select_agents(task: str) -> list[str]:
    for keywords, agent_ids in ROUTING_RULES:
        if any(
            matches_keyword(task, keyword)
            for keyword in keywords
        ):
            return validate_agents(agent_ids)

    return validate_agents(DEFAULT_AGENTS)
