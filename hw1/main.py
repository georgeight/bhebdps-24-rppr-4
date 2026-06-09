from __future__ import annotations

import ast
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Simple Calculator API")

current_expression: str = ""

ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}

ALLOWED_UNARYOPS = {
    ast.UAdd: lambda a: a,
    ast.USub: lambda a: -a,
}

VALID_OPERATORS = {"+", "-", "*", "/"}


class BinaryOperation(BaseModel):
    a: float = Field(..., description="Первый операнд")
    op: str = Field(..., description="Операция: +, -, *, /")
    b: float = Field(..., description="Второй операнд")


class ExpressionString(BaseModel):
    expression: str = Field(
        ...,
        description=(
            "Арифметическое выражение с числами, скобками и операциями"
        ),
    )


def format_number(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def normalize_operator(op: str) -> str:
    if op not in VALID_OPERATORS:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимая операция: {op}",
        )
    return op


def evaluate_ast(node: ast.AST) -> float:
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_BINOPS:
            raise HTTPException(
                status_code=400,
                detail=f"Недопустимая бинарная операция: {op_type.__name__}",
            )
        left_value = evaluate_ast(node.left)
        right_value = evaluate_ast(node.right)
        return ALLOWED_BINOPS[op_type](left_value, right_value)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_UNARYOPS:
            raise HTTPException(
                status_code=400,
                detail=f"Недопустимая унарная операция: {op_type.__name__}",
            )
        return ALLOWED_UNARYOPS[op_type](evaluate_ast(node.operand))

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise HTTPException(
            status_code=400,
            detail="Только числа допустимы в выражении",
        )

    if isinstance(node, ast.Num):
        return float(node.n)

    raise HTTPException(
        status_code=400,
        detail=f"Недопустимый узел выражения: {type(node).__name__}",
    )


def parse_math_expression(expression: str) -> float:
    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Синтаксическая ошибка в выражении: {exc.text or expression}"
            ),
        )

    return evaluate_ast(parsed.body)


@app.get("/add")
def add(a: float, b: float) -> dict[str, float]:
    return {"result": a + b}


@app.get("/subtract")
def subtract(a: float, b: float) -> dict[str, float]:
    return {"result": a - b}


@app.get("/multiply")
def multiply(a: float, b: float) -> dict[str, float]:
    return {"result": a * b}


@app.get("/divide")
def divide(a: float, b: float) -> dict[str, float]:
    if b == 0:
        raise HTTPException(
            status_code=400, detail="Деление на ноль невозможно"
        )
    return {"result": a / b}


@app.post("/expression/part")
def create_expression_part(operation: BinaryOperation) -> dict[str, str]:
    global current_expression
    normalized_op = normalize_operator(operation.op)
    current_expression = (
        f"{format_number(operation.a)}{normalized_op}"
        f"{format_number(operation.b)}"
    )
    return {"expression": current_expression}


@app.post("/expression/string")
def set_expression(expression_data: ExpressionString) -> dict[str, Any]:
    global current_expression
    expression_text = expression_data.expression.strip()
    result = parse_math_expression(expression_text)
    current_expression = expression_text
    return {"expression": current_expression, "result": result}


@app.get("/expression")
def get_current_expression() -> dict[str, str | None]:
    return {"expression": current_expression or None}


@app.get("/expression/evaluate")
def evaluate_current_expression() -> dict[str, Any]:
    if not current_expression:
        raise HTTPException(status_code=400, detail="Выражение не задано")
    result = parse_math_expression(current_expression)
    return {"expression": current_expression, "result": result}
