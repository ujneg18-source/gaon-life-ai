"""Information Extract 전용 변환. Solar Chat의 nullable 규칙과 혼용하지 않는다."""

from copy import deepcopy

from pydantic import BaseModel


def to_extract_schema(model: type[BaseModel]) -> dict:
    """참조를 펼치고 날짜·nullable·검증 전용 키를 제거한다. 검증은 원본 Pydantic이 맡는다."""
    original = model.model_json_schema()
    defs = original.get("$defs", {})

    def convert(node: dict, in_array: bool = False) -> dict:
        node = deepcopy(node)
        if "$ref" in node:
            node = {**deepcopy(defs[node.pop("$ref").split("/")[-1]]), **node}
        if "anyOf" in node:
            choices = [v for v in node.pop("anyOf") if v.get("type") != "null"]
            if len(choices) != 1:
                raise ValueError("Extract는 다중 타입 선택을 받지 않습니다.")
            node = {**convert(choices[0], in_array), **node}
        result = {k: v for k, v in node.items() if k in {"type", "description", "enum"}}
        if node.get("type") == "object":
            result["properties"] = {k: convert(v, in_array) for k, v in node["properties"].items()}
        if node.get("type") == "array":
            if in_array:
                raise ValueError("Extract는 배열 안 배열을 받지 않습니다.")
            result["items"] = convert(node["items"], True)
        return result

    schema = convert(original)
    if any(
        v["type"] not in {"string", "integer", "number", "array"}
        for v in schema["properties"].values()
    ):
        raise ValueError("Extract 1단계 속성 타입 제약 위반")
    return schema
