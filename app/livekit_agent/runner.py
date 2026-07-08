import multiprocessing
import sys


def run_livekit_worker():
    # remove uvicorn arguments
    sys.argv = [
        "worker.py",
        "start"
    ]
    from app.livekit_agent.worker import start_worker
    start_worker()



def start_livekit_process():
    process = multiprocessing.Process(
        target=run_livekit_worker,
        daemon=False
    )
    process.start()
    return process