def present_result(question_type, params, generated_code, final_result):
    print("\n==============================")
    print(" FINAL RESULT PRESENTATION")
    print("==============================")

    print("\nQuestion Type:")
    print(question_type)

    print("\nUser Parameters:")
    print(params)

    print("\nGenerated / Corrected Code:")
    print(generated_code)

    print("\nExecution Status:")
    print(final_result.get("execution", {}).get("status"))

    print("\nValidation Status:")
    print(final_result.get("validation", {}).get("message"))

    print("\nCorrection Applied:")
    print(final_result.get("correction_applied"))

    print("\nFinal Result:")
    result = final_result.get("result")

    if result is None:
        print("No result returned.")
    else:
        print(result)

    print("\nOverall Status:")
    print(final_result.get("status"))