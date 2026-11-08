import asyncio
import json
import os
import re
from dataclasses import dataclass

from app.ai.capabilities.text_generation import GenerationMessage
from app.ai.capabilities.types import AICapability
from app.ai.resolver import resolve_ai_provider_registry
from app.services.assistant_config import AssistantConfig
from app.services.assistant_orchestrator import AssistantOrchestrator
from app.services.task_extraction import TaskExtractionService


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    source: str


CASES = [
    EvaluationCase(
        name="Recipient, quantity, relative deadline and urgency",
        source=(
            "My manager wrote: 'Please review the client feedback "
            "from last week, identify the three most important issues, "
            "prepare a short summary for the team, and email it to me "
            "by Friday. This isn't urgent, so fit it around your "
            "other work.'"
        ),
    ),
    EvaluationCase(
        name="Absolute deadline and excluded action",
        source=(
            "Please update the onboarding checklist by 2026-11-20 "
            "and send the revised checklist to Priya. "
            "Do not schedule a meeting."
        ),
    ),
    EvaluationCase(
        name="No actionable work",
        source=(
            "For your information, the office renovation has been completed. No action is required."
        ),
    ),
]


def task_text(tasks: list) -> str:
    parts = []

    for task in tasks:
        parts.append(task.title)
        parts.append(task.description or "")

        for subtask in task.subtasks:
            parts.append(subtask.title)

    return " ".join(parts).lower()


def contains(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


def evaluate_extraction(
    case: EvaluationCase,
    tasks: list,
) -> list[str]:
    problems = []
    text = task_text(tasks)

    if case.name.startswith("Recipient"):
        requirements = {
            "Review feedback": r"\breview\b.*\bfeedback\b|\bfeedback\b.*\breview\b",
            "Three important issues": r"\b(three|3)\b.*\bissues?\b|\bissues?\b.*\b(three|3)\b",
            "Prepare summary": r"\b(prepar\w*|writ\w*|creat\w*)\b.*\bsummary\b",
            "Summary for the team": r"\bteam\b",
            "Email delivery": r"\bemail\b",
            "Recipient is manager": r"\bmanager\b",
            "Friday deadline": r"\bfriday\b",
        }

        for label, pattern in requirements.items():
            if not contains(text, pattern):
                problems.append(f"Missing requirement: {label}")

        if not tasks:
            problems.append("No tasks extracted")

        if any(task.due_date is not None for task in tasks):
            problems.append(
                "Relative Friday deadline was converted to an "
                "absolute date without a verified reference date"
            )

        if not any(
            contains(
                " ".join(
                    [
                        task.title,
                        task.description or "",
                        *[subtask.title for subtask in task.subtasks],
                    ]
                ),
                r"\bemail\b",
            )
            and contains(
                " ".join(
                    [
                        task.title,
                        task.description or "",
                        *[subtask.title for subtask in task.subtasks],
                    ]
                ),
                r"\bmanager\b",
            )
            for task in tasks
        ):
            problems.append("Emailing the manager is not preserved within one task")

    elif case.name.startswith("Absolute"):
        if not contains(text, r"\bonboarding\b"):
            problems.append("Missing onboarding checklist")

        if not contains(text, r"\bpriya\b"):
            problems.append("Missing recipient Priya")

        if not contains(text, r"\bsend\b"):
            problems.append("Missing delivery action")

        if not any(str(task.due_date) == "2026-11-20" for task in tasks):
            problems.append("Absolute deadline not preserved")

        if any(
            contains(
                f"{task.title} {task.description or ''}",
                r"\b(schedule|organize|arrange|book)\b.*\bmeeting\b",
            )
            for task in tasks
        ):
            problems.append("Check whether the excluded meeting was turned into a task")

    elif case.name == "No actionable work":
        if tasks:
            problems.append("Created tasks when the source explicitly requires no action")

    return problems


async def evaluate_task_extraction(
    extraction_service: TaskExtractionService,
    runs: int,
) -> int:
    failures = 0

    for case in CASES:
        for run in range(1, runs + 1):
            print(f"\nTASK EXTRACTION: {case.name} (run {run})")

            try:
                result = await extraction_service.extract(
                    text=case.source,
                )
            except Exception as error:
                failures += 1
                print(f"ERROR: {type(error).__name__}: {error}")
                continue

            print(
                json.dumps(
                    result.model_dump(mode="json"),
                    indent=2,
                    ensure_ascii=False,
                )
            )

            problems = evaluate_extraction(case, result.tasks)

            if problems:
                failures += 1

                for problem in problems:
                    print(f"FAIL: {problem}")
            else:
                print("PASS: Automated checks")

    return failures


async def evaluate_classification(
    orchestrator: AssistantOrchestrator,
) -> int:
    print("\nCLASSIFICATION: Task extraction follow-up")

    history = [
        GenerationMessage(
            role="user",
            content=CASES[0].source,
        ),
        GenerationMessage(
            role="assistant",
            content=("Your manager wants you to review the feedback and prepare a summary."),
        ),
    ]

    try:
        result = await orchestrator.classify(
            message="Can you break it down into tasks?",
            history=history,
        )
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}")
        return 1

    capabilities = result.capabilities

    print([capability.value for capability in capabilities])

    if capabilities == [AICapability.TASK_EXTRACTION]:
        print("PASS: Structured task extraction selected")
        return 0

    print("FAIL: Expected task_extraction")
    return 1


async def evaluate_explanation(
    orchestrator: AssistantOrchestrator,
) -> int:
    print("\nSTRUCTURED EXPLANATION: Accuracy check")

    try:
        results = await orchestrator.execute(
            message=CASES[0].source,
            capabilities=[AICapability.MESSAGE_EXPLANATION],
        )
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}")
        return 1

    explanation = results[0].structured_explanation

    if explanation is None:
        print("FAIL: Structured explanation was not produced")
        return 1

    print(
        json.dumps(
            explanation.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        )
    )

    text = " ".join(
        [
            explanation.explanation,
            *explanation.ambiguities,
            *explanation.steps,
            explanation.next_step or "",
        ]
    ).lower()

    requirements = {
        "Feedback": r"\bfeedback\b",
        "Summary": r"\bsummary\b",
        "Team": r"\bteam\b",
        "Manager": r"\bmanager\b",
        "Friday": r"\bfriday\b",
        "Three issues": r"\b(three|3)\b.*\bissues?\b|\bissues?\b.*\b(three|3)\b",
    }

    problems = [label for label, pattern in requirements.items() if not contains(text, pattern)]

    if problems:
        print(f"FAIL: Missing information: {', '.join(problems)}")
        return 1

    print("PASS: Automated explanation checks")
    return 0


async def main() -> None:
    runs = int(os.getenv("NEUROLENS_EVAL_RUNS", "1"))

    if runs < 1:
        raise ValueError("NEUROLENS_EVAL_RUNS must be at least 1")

    registry = resolve_ai_provider_registry()

    extraction_service = TaskExtractionService(
        registry=registry,
    )

    orchestrator = AssistantOrchestrator(
        registry=registry,
        config=AssistantConfig(
            highlight_ambiguity=True,
            step_by_step_guidance=True,
            always_show_next_step=True,
        ),
    )

    failures = 0

    failures += await evaluate_task_extraction(
        extraction_service=extraction_service,
        runs=runs,
    )

    failures += await evaluate_classification(orchestrator)
    failures += await evaluate_explanation(orchestrator)

    print("\n" + "=" * 50)

    if failures:
        print(f"EVALUATION FAILED: {failures} failing cases")
        raise SystemExit(1)

    print("AUTOMATED EVALUATION PASSED")
    print("Manual semantic review is still required.")


if __name__ == "__main__":
    asyncio.run(main())
