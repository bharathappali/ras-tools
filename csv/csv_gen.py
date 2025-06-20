import argparse
import csv
import random
import sys
from datetime import datetime, timedelta

# Constants
INTERVAL_MINS = 15
NUM_DAYS = 1


# Parse inputs
def parse_args():
    global INTERVAL_MINS, NUM_DAYS

    parser = argparse.ArgumentParser(description="Calculate number of intervals for reporting.")
    parser.add_argument(
        "-m", "--int_mins",
        type=int,
        default=INTERVAL_MINS,
        help="Interval length in minutes (default: 15, max: 360)"
    )
    parser.add_argument(
        "-d", "--num_days",
        type=int,
        default=NUM_DAYS,
        help="Number of days to calculate for (default: 1, max: 366)"
    )

    args = parser.parse_args()

    # Validations
    if args.int_mins <= 0 or args.int_mins > 360:
        sys.exit("Error: -m / --int_mins must be a positive integer no more than 360.")

    if args.num_days <= 0 or args.num_days > 366:
        sys.exit("Error: -d / --num_days must be a positive integer no more than 366.")

    INTERVAL_MINS = args.int_mins
    NUM_DAYS = args.num_days


parse_args()

print(f"Interval Minutes: {INTERVAL_MINS} | Number of Days: {NUM_DAYS}")

now = datetime.today()
report_period_end = datetime(now.year, now.month, now.day)
report_period_start = report_period_end - timedelta(days=NUM_DAYS)

num_intervals = int((report_period_end - report_period_start).total_seconds() // (INTERVAL_MINS * 60))
print(f"Number of entries: {num_intervals}")

workloads = [
    {
        "workload": "no-gpu-app",
        "workload_type": "deployment",
        "namespace": "default",
        "image": "quay.io/production/no-gpu-app:latest",
        "resource_id": "res-001",
        "has_gpu": False,
        "gpu_partitioned": False,
        "requests": {"cpu": 0.3, "memory": 200_000},
        "limits": {"cpu": 0.8, "memory": 800_000},
    },
    {
        "workload": "gpu-full-app",
        "workload_type": "statefulset",
        "namespace": "ml",
        "image": "quay.io/production/gpu-full-app:latest",
        "resource_id": "res-002",
        "has_gpu": True,
        "gpu_partitioned": False,
        "requests": {"cpu": 0.6, "memory": 600_000},
        "limits": {"cpu": 1.0, "memory": 1200_000},
    },
    {
        "workload": "gpu-partition-app",
        "workload_type": "job",
        "namespace": "cv",
        "image": "quay.io/production/gpu-partition-app:latest",
        "resource_id": "res-003",
        "has_gpu": True,
        "gpu_partitioned": True,
        "requests": {"cpu": 0.4, "memory": 300_000},
        "limits": {"cpu": 0.9, "memory": 1000_000},
    },
]


rows = []
for workload in workloads:
    pod_name = f"{workload['workload']}-pod-0"
    container_name = f"{workload['workload']}-container"

    # Clear existing data
    rows.clear()
    for i in range(num_intervals):
        interval_start = report_period_start + timedelta(minutes=i * INTERVAL_MINS)
        interval_end = interval_start + timedelta(minutes=INTERVAL_MINS)

        # Simulate usage fluctuations
        cpu_usage = round(random.uniform(0.5, 0.95) * workload["limits"]["cpu"], 3)
        cpu_throttle = round(random.uniform(0.01, 0.03), 3)
        mem_usage = int(random.uniform(0.6, 0.95) * workload["limits"]["memory"])
        mem_rss = int(mem_usage * random.uniform(0.4, 0.7))

        row = {
            "report_period_start": report_period_start.isoformat(),
            "report_period_end": report_period_end.isoformat(),
            "interval_start": interval_start.isoformat(),
            "interval_end": interval_end.isoformat(),
            "container_name": container_name,
            "pod": pod_name,
            "owner_name": workload["workload"],
            "owner_kind": workload["workload_type"].capitalize(),
            "workload": workload["workload"],
            "workload_type": workload["workload_type"],
            "namespace": workload["namespace"],
            "image_name": workload["image"],
            "node": "ip-255-255-255-255.ec2.internal",
            "resource_id": workload["resource_id"],
            "cpu_request_container_avg": workload["requests"]["cpu"],
            "cpu_request_container_sum": workload["requests"]["cpu"],
            "cpu_limit_container_avg": workload["limits"]["cpu"],
            "cpu_limit_container_sum": workload["limits"]["cpu"],
            "cpu_usage_container_avg": cpu_usage,
            "cpu_usage_container_min": round(cpu_usage * 0.8, 3),
            "cpu_usage_container_max": round(cpu_usage * 1.05, 3),
            "cpu_usage_container_sum": cpu_usage,
            "cpu_throttle_container_avg": cpu_throttle,
            "cpu_throttle_container_max": round(cpu_throttle * 1.5, 3),
            "cpu_throttle_container_sum": cpu_throttle,
            "memory_request_container_avg": workload["requests"]["memory"],
            "memory_request_container_sum": workload["requests"]["memory"],
            "memory_limit_container_avg": workload["limits"]["memory"],
            "memory_limit_container_sum": workload["limits"]["memory"],
            "memory_usage_container_avg": mem_usage,
            "memory_usage_container_min": int(mem_usage * 0.8),
            "memory_usage_container_max": int(mem_usage * 1.05),
            "memory_usage_container_sum": mem_usage,
            "memory_rss_usage_container_avg": mem_rss,
            "memory_rss_usage_container_min": int(mem_rss * 0.7),
            "memory_rss_usage_container_max": int(mem_rss * 1.2),
            "memory_rss_usage_container_sum": mem_rss,
        }

        # GPU fields
        if workload["has_gpu"]:
            row["accelerator_model_name"] = "NVIDIA-A100-SXM4-40GB"
            row["accelerator_profile_name"] = "3g.20gb" if workload["gpu_partitioned"] else ""

            if not workload["gpu_partitioned"]:
                core_avg = round(random.uniform(50, 75), 2)
                row["accelerator_core_usage_percentage_min"] = round(core_avg * 0.6, 2)
                row["accelerator_core_usage_percentage_max"] = round(core_avg * 1.3, 2)
                row["accelerator_core_usage_percentage_avg"] = core_avg
                mem_avg = round(random.uniform(40, 60), 2)
                row["accelerator_memory_copy_percentage_min"] = round(mem_avg * 0.5, 2)
                row["accelerator_memory_copy_percentage_max"] = round(mem_avg * 1.4, 2)
                row["accelerator_memory_copy_percentage_avg"] = mem_avg
            else:
                row["accelerator_core_usage_percentage_min"] = ""
                row["accelerator_core_usage_percentage_max"] = ""
                row["accelerator_core_usage_percentage_avg"] = ""
                row["accelerator_memory_copy_percentage_min"] = ""
                row["accelerator_memory_copy_percentage_max"] = ""
                row["accelerator_memory_copy_percentage_avg"] = ""

            fb_avg = round(random.uniform(8000, 12000), 2)
            row["accelerator_frame_buffer_usage_min"] = round(fb_avg * 0.7, 2)
            row["accelerator_frame_buffer_usage_max"] = round(fb_avg * 1.3, 2)
            row["accelerator_frame_buffer_usage_avg"] = fb_avg
        else:
            # Fill all GPU fields with empty values
            for field in [
                "accelerator_model_name", "accelerator_profile_name",
                "accelerator_core_usage_percentage_min", "accelerator_core_usage_percentage_max",
                "accelerator_core_usage_percentage_avg",
                "accelerator_memory_copy_percentage_min", "accelerator_memory_copy_percentage_max",
                "accelerator_memory_copy_percentage_avg",
                "accelerator_frame_buffer_usage_min", "accelerator_frame_buffer_usage_max",
                "accelerator_frame_buffer_usage_avg"
            ]:
                row[field] = ""

        rows.append(row)

    # Write data to CSV
    filename = f"{workload['workload']}-results.csv"
    with open(f"csvs/{filename}", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        print(f"CSV written to csvs/{filename}")
