"""
Batch process all pending images through the vision + embedding pipeline.
Provides live progress output and a final summary.
"""

import time
from app.database import run_query, run_execute, run_execute_returning
from app.jobs import process_image_record


def run_batch_all():
    pending = run_query("SELECT id, filename FROM images WHERE status = 'pending' ORDER BY id")
    total = len(pending)

    if total == 0:
        print("No pending images found. All images already processed.")
        return

    print(f"Starting batch processing of {total} pending images...")
    print("-" * 60)

    # Create a tracking job
    job = run_execute_returning(
        "INSERT INTO jobs (status, total, processed, failed) VALUES ('running', %s, 0, 0) RETURNING id",
        (total,),
    )
    job_id = job["id"]
    print(f"Job ID: {job_id}")
    print()

    processed_count = 0
    failed_count = 0
    t_start = time.time()

    for i, img in enumerate(pending, start=1):
        t_img = time.time()
        success = process_image_record(img["id"])
        elapsed = time.time() - t_img

        if success:
            processed_count += 1
            run_execute("UPDATE jobs SET processed = processed + 1 WHERE id = %s", (job_id,))
            print(f"[{i:02d}/{total}] [OK] {img['filename']} ({elapsed:.1f}s)")
        else:
            failed_count += 1
            run_execute("UPDATE jobs SET failed = failed + 1 WHERE id = %s", (job_id,))
            print(f"[{i:02d}/{total}] [!!] {img['filename']} FAILED ({elapsed:.1f}s)")

    run_execute("UPDATE jobs SET status = 'completed' WHERE id = %s", (job_id,))
    total_elapsed = time.time() - t_start

    print()
    print("=" * 60)
    print(f"Batch complete in {total_elapsed / 60:.1f} minutes")
    print(f"  Processed : {processed_count}")
    print(f"  Failed    : {failed_count}")
    print(f"  Total     : {total}")
    print(f"  Job ID    : {job_id}")

    # Print final DB summary
    counts = run_query("SELECT status, COUNT(*) as n FROM images GROUP BY status ORDER BY status")
    print()
    print("Image status summary:")
    for row in counts:
        print(f"  {row['status']:20s} {row['n']}")


if __name__ == "__main__":
    run_batch_all()
