# Simple rate limiter for portfolio requests
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(deque)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        client_requests = self.requests[client_ip]

        # Remove old requests outside the time window
        while client_requests and client_requests[0] < now - self.time_window:
            client_requests.popleft()

        # Check if under limit
        if len(client_requests) < self.max_requests:
            client_requests.append(now)
            return True

        return False


# Global rate limiter instance
portfolio_rate_limiter = RateLimiter(
    max_requests=20, time_window=60
)  # 20 requests per minute

