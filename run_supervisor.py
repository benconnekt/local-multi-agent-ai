
import time

from app.agents.registry import AGENTS
from app.graphs.supervisor_graph import supervisor_graph


def main():
    print("\nRebalanc Local Agent Studio")
    print("================================")
    print("Supervisor: Alex (Tech Lead)", flush=True)

    task = input("\nEnter development task: ").strip()

    if not task:
        print("A task is required.")
        return

    started = time.monotonic()
    selected_agents = []
    final_status = None

    try:
        for event in supervisor_graph.stream(
            {"task": task, "max_revisions": 2},
            stream_mode="updates",
        ):
            for node, update in event.items():
                if node == "supervisor":
                    selected_agents = update["selected_agents"]

                    names = [
                        AGENTS[role].name
                        for role in selected_agents
                    ]

                    print(
                        "\nAlex assigned: " + " → ".join(names),
                        flush=True,
                    )

                elif node == "execute_agent":
                    index = update["current_index"] - 1
                    role = selected_agents[index]

                    if role == "reviewer":
                        continue

                    agent = AGENTS[role]
                    output = update["outputs"][role]

                    print(
                        f"\n[{time.monotonic() - started:.1f}s] "
                        f"{agent.name} ({agent.role}) completed",
                        flush=True,
                    )
                    print(output, flush=True)

                elif node == "review":
                    print(
                        "\nOliver's decision: "
                        f"{update['review_status']}",
                        flush=True,
                    )
                    print(
                        f"Feedback: {update['review_feedback']}",
                        flush=True,
                    )

                elif node == "revise":
                    print(
                        f"\nAlex: Returning work to James "
                        f"(revision {update['revision_count']}/2)",
                        flush=True,
                    )

                elif node in {"complete", "blocked"}:
                    final_status = update["workflow_status"]

        print(
            f"\nWorkflow status: {final_status}",
            flush=True,
        )
        print(
            f"Elapsed: {time.monotonic() - started:.1f}s",
            flush=True,
        )

    except KeyboardInterrupt:
        print("\nWorkflow interrupted.", flush=True)

    except Exception as exc:
        print(
            f"\nWorkflow failed: "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )
        raise


if __name__ == "__main__":
    main()
