# llmServer/app/services/test/services/test_result_validation_service.py
# PYTHONPATH=. python -m app.services.test.services.test_result_validation_service

import pandas as pd
from app.services.result_validation_service import ResultValidationService


def run_test():

    service = ResultValidationService()

    print("\n🚀 ResultValidationService 테스트 시작\n")

    # ----------------------------
    # 1️⃣ 정상 데이터
    # ----------------------------
    df_normal = pd.DataFrame({"revenue": [1000, 2000, 1500]})

    result = service.validate({"df": df_normal, "retry_count": 0, "error_history": []})

    print("정상 데이터 결과:", result)

    # ----------------------------
    # 2️⃣ 음수 매출
    # ----------------------------
    df_negative = pd.DataFrame({"revenue": [1000, -500, 2000]})

    result2 = service.validate(
        {"df": df_negative, "retry_count": 0, "error_history": []}
    )

    print("음수 매출 결과:", result2)

    # ----------------------------
    # 3️⃣ NULL 과다
    # ----------------------------
    df_null = pd.DataFrame({"amount": [None, None, None, 100]})

    result3 = service.validate({"df": df_null, "retry_count": 0, "error_history": []})

    print("NULL 과다 결과:", result3)

    print("\n🎉 테스트 완료\n")


if __name__ == "__main__":
    run_test()
