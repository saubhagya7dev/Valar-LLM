from valar_llm.contracts.requests import REQUEST
from valar_llm.contracts.validation import validate_output
from valar_llm.data.fixtures import fixture_images, load_cases
from valar_llm.runtime.prompts import messages_for


def check_fixtures():
    checked = []
    for case in load_cases():
        request = REQUEST.validate_python(case["request"])
        images = fixture_images(case)
        try:
            messages_for(request, images)
            validate_output(request, case["expected"])
        finally:
            for image in images:
                image.close()
        checked.append({"id": case["id"], "task": request.task, "contract_valid": True})
    return {"kind": "offline_fixture_validation", "model_executed": False, "cases": checked}
