
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(
    page_title="Disk Scheduling Simulator",
    page_icon="💽",
    layout="wide"
)

st.title("Disk Scheduling Simulator")
st.write(
    "An interactive Operating Systems project to visualize "
    "and compare FCFS, SSTF, SCAN, and C-SCAN algorithms."
)

st.sidebar.header("Disk Configuration")

disk_size = st.sidebar.number_input(
    "Number of cylinders",
    min_value=10,
    max_value=10000,
    value=200,
    step=10
)

head = st.sidebar.number_input(
    "Initial head position",
    min_value=0,
    max_value=int(disk_size) - 1,
    value=min(53, int(disk_size) - 1)
)

request_text = st.sidebar.text_input(
    "Disk requests (comma-separated)",
    value="98, 183, 37, 122, 14, 124, 65, 67"
)

direction = st.sidebar.selectbox(
    "Initial direction for SCAN and C-SCAN",
    ["Right", "Left"]
)


def calculate_movement(sequence):
    return sum(
        abs(sequence[i] - sequence[i - 1])
        for i in range(1, len(sequence))
    )


def calculate_steps(sequence):
    return [
        {
            "Step": i,
            "From Cylinder": sequence[i - 1],
            "To Cylinder": sequence[i],
            "Distance": abs(sequence[i] - sequence[i - 1])
        }
        for i in range(1, len(sequence))
    ]


def fcfs(requests, head):
    sequence = [head] + requests
    return sequence, calculate_movement(sequence)


def sstf(requests, head):
    pending = requests.copy()
    sequence = [head]
    current = head

    while pending:
        nearest = min(
            pending,
            key=lambda request: abs(request - current)
        )
        sequence.append(nearest)
        current = nearest
        pending.remove(nearest)

    return sequence, calculate_movement(sequence)


def scan(requests, head, disk_size, direction):
    lower = 0
    upper = disk_size - 1

    left = sorted(
        [r for r in requests if r < head],
        reverse=True
    )
    right = sorted(
        [r for r in requests if r >= head]
    )

    sequence = [head]

    if direction == "Right":
        sequence.extend(right)

        if sequence[-1] != upper:
            sequence.append(upper)

        sequence.extend(sorted(left))

    else:
        sequence.extend(left)

        if sequence[-1] != lower:
            sequence.append(lower)

        sequence.extend(sorted(right))

    return sequence, calculate_movement(sequence)


def c_scan(requests, head, disk_size, direction):
    lower = 0
    upper = disk_size - 1

    left = sorted(
        [r for r in requests if r < head]
    )
    right = sorted(
        [r for r in requests if r >= head]
    )

    sequence = [head]

    if direction == "Right":
        sequence.extend(right)

        if sequence[-1] != upper:
            sequence.append(upper)

        if left:
            sequence.append(lower)
            sequence.extend(left)

    else:
        sequence.extend(reversed(left))

        if sequence[-1] != lower:
            sequence.append(lower)

        if right:
            sequence.append(upper)
            sequence.extend(reversed(right))

    return sequence, calculate_movement(sequence)


if st.button("Run Simulation", type="primary"):
    try:
        requests = [
            int(item.strip())
            for item in request_text.split(",")
            if item.strip()
        ]

        if not requests:
            st.error("Please enter at least one disk request.")

        elif any(r < 0 or r >= disk_size for r in requests):
            st.error(
                f"Requests must be between 0 and {disk_size - 1}."
            )

        elif not 0 <= head < disk_size:
            st.error("The initial head position is outside the disk.")

        else:
            results = {
                "FCFS": fcfs(requests, head),
                "SSTF": sstf(requests, head),
                "SCAN": scan(requests, head, disk_size, direction),
                "C-SCAN": c_scan(
                    requests, head, disk_size, direction
                )
            }

            comparison = []

            for name, (sequence, movement) in results.items():
                comparison.append({
                    "Algorithm": name,
                    "Total Head Movement": movement,
                    "Average Movement per Request": round(
                        movement / len(requests), 2
                    ),
                    "Service Sequence": " → ".join(
                        map(str, sequence)
                    )
                })

            comparison.sort(
                key=lambda item: item["Total Head Movement"]
            )

            best = comparison[0]
            fcfs_movement = results["FCFS"][1]

            if fcfs_movement > 0:
                improvement = (
                    (fcfs_movement - best["Total Head Movement"])
                    / fcfs_movement
                ) * 100
            else:
                improvement = 0

            st.divider()
            st.subheader("Performance Dashboard")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Best Algorithm",
                best["Algorithm"]
            )

            col2.metric(
                "Lowest Head Movement",
                f"{best['Total Head Movement']} cylinders"
            )

            col3.metric(
                "Improvement vs FCFS",
                f"{improvement:.2f}%"
            )

            st.caption(
                "Improvement compares the lowest movement result "
                "with FCFS. A negative value means the best result "
                "is worse than FCFS."
            )

            st.subheader("Algorithm Comparison")

            display_df = pd.DataFrame(comparison)

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            csv_data = display_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download Results as CSV",
                data=csv_data,
                file_name="disk_scheduling_results.csv",
                mime="text/csv"
            )

            st.subheader("Total Head Movement Comparison")

            names = [
                item["Algorithm"] for item in comparison
            ]
            movements = [
                item["Total Head Movement"]
                for item in comparison
            ]

            fig, ax = plt.subplots(figsize=(9, 4))
            bars = ax.bar(names, movements)

            ax.set_xlabel("Scheduling Algorithm")
            ax.set_ylabel("Total Head Movement (cylinders)")
            ax.set_title("Algorithm Performance")
            ax.bar_label(bars, padding=3)
            ax.grid(axis="y", alpha=0.25)
            plt.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

            st.subheader("Head Movement Paths")

            for name, (sequence, movement) in results.items():
                with st.expander(
                    f"{name} — {movement} cylinders"
                ):
                    st.write("Service sequence:")
                    st.code(" → ".join(map(str, sequence)))

                    step_data = calculate_steps(sequence)

                    if step_data:
                        st.write("Step-by-step movement:")
                        st.dataframe(
                            pd.DataFrame(step_data),
                            use_container_width=True,
                            hide_index=True
                        )

                    fig, ax = plt.subplots(figsize=(9, 3))

                    ax.plot(
                        range(len(sequence)),
                        sequence,
                        marker="o"
                    )

                    ax.set_xlabel("Movement Step")
                    ax.set_ylabel("Cylinder Number")
                    ax.set_title(f"{name} Movement Path")
                    ax.grid(True, alpha=0.3)

                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)

            st.info(
                "Note: Head movement is measured in cylinders. "
                "The wrap-around movement in C-SCAN is included "
                "in the total using the absolute distance between "
                "consecutive positions."
            )

    except ValueError:
        st.error(
            "Invalid input. Enter whole-number disk requests "
            "separated by commas."
        )

st.divider()
st.caption("Operating Systems | Unit V: Storage Management")
