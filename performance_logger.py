import time
import logging

# Setup logging to file
LOG_FILE = "chess_load_test.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

def log_event(message, level="info"):
    """Logs events with timestamps to a file."""
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)

def track_api_response_time(start_time, api_name, user):
    """Calculates response time and logs it."""
    response_time = time.time() - start_time
    log_event(f"{user['username']} - {api_name} Response Time: {response_time:.2f}s")

def log_final_stats(user, successful_moves, failed_moves, total_response_time, session_start):
    """Logs performance summary at the end of a session."""
    total_time = time.time() - session_start
    avg_response_time = total_response_time / max(1, (successful_moves + failed_moves))
    log_event(f"{user['username']} Stats: {successful_moves} Moves, {failed_moves} Failures, Avg API Response Time: {avg_response_time:.2f}s, Session Duration: {total_time:.2f}s")
