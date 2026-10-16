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


def to_chat_schema(model: type[BaseModel]) -> dict:
    """Solar strict 규약: 모든 키 required, nullable 단일 타입 배열, 모든 객체 extra 금지."""
    schema = deepcopy(model.model_json_schema())

    def visit(node):
        if isinstance(node, list):
            return [visit(v) for v in node]
        if not isinstance(node, dict):
            return node
        result = {
            k: visit(v)
            for k, v in node.items()
            if k
            not in {"default", "format", "maxLength", "minLength", "maxItems", "minItems", "title"}
        }
        if "anyOf" in result:
            choices = result.pop("anyOf")
            nonnull = [v for v in choices if v.get("type") != "null"]
            if len(nonnull) != 1 or "type" not in nonnull[0]:
                raise ValueError("지원하지 않는 nullable 스키마")
            result.update(nonnull[0])
            result["type"] = [nonnull[0]["type"], "null"]
        if result.get("type") == "object":
            result["required"] = list(result.get("properties", {}))
            result["additionalProperties"] = False
        return result

    return visit(schema)
