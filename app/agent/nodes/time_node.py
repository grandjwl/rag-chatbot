import time
import logging

logger = logging.getLogger(__name__)


class TimedNode:

    def __init__(self, name, node):
        self.name = name
        self.node = node

    async def __call__(self, state):

        start = time.perf_counter()

        result = await self.node(state)

        elapsed = (time.perf_counter() - start) * 1000

        logger.info(f"[NODE] {self.name} took {elapsed:.2f} ms")

        # state에 기록하고 싶으면:
        new_state = result.copy()
        timings = new_state.get("_timings", {})
        timings[self.name] = round(elapsed, 2)
        new_state["_timings"] = timings

        return new_state