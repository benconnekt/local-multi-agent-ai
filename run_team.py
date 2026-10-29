
import time
from app.graphs.software_team import software_team


def main():
    print("\nRebalanc Local Agent Studio", flush=True)
    print("==================", flush=True)

    task = input("\nEnter development task: ").strip()

    if not task:
        print("Please enter a task.")
        return

    print("\nStarting multi-agent workflow...", flush=True)

    start = time.monotonic()

    try:
        for event in software_team.stream(
            {"task": task},
            stream_mode="updates",
        ):
            for agent_name, output in event.items():
                elapsed = time.monotonic() - start

                print(
                    f"\n[{elapsed:.1f}s] "
                    f"Completed: {agent_name}",
                    flush=True,
                )

                for key, value in output.items():
                    print(
                        f"\n--- {key.upper()} ---\n{value}",
                        flush=True,
                    )

        print(
            f"\nWorkflow completed in "
            f"{time.monotonic() - start:.1f}s",
            flush=True,
        )

    except Exception as exc:
        print(
            f"\nWorkflow failed: "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )
        raise


if __name__ == "__main__":
    main()
