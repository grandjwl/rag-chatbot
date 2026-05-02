# llmServer/app/services/retry_decision_service.py

class RetryDecisionService:

    MAX_RETRY = 3

    def decide(self, state: dict) -> str:
        """
        return:
            - "RETRY"
            - "ANSWER"
            - "FAIL"
        """

        retry_count = state.get("retry_count", 0)
        error_type = state.get("error_type")
        anomalies = state.get("result_anomalies", [])

        if retry_count >= self.MAX_RETRY:
            return "FAIL"

        if error_type:
            return "RETRY"

        if anomalies:
            return "RETRY"

        return "ANSWER"