"""Модуль представляет собой утилиту для разработки, которая позволяет автоматически
генерировать схемы Pydantic для словарей (Dict) на Python."""

from typing import Any, Dict


def generate_pydantic_models(  # noqa C901
    data: Dict[str, Any],
    depth: int,
    prfix_class_name: str = "RootModel",
    parent_class: str = "BaseModel",
) -> str:
    """
    - data: Словарь на Python
    - depth: Уровень глубины анализа словаря для создания моделей Pydantic
    - prfix_class_name: Начальное название для моделей Pydantic
    - parent_class: Модель, от которой будет происходить наследование
    """

    def get_type(value: Any) -> str:
        if isinstance(value, str):
            return "str"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, list):
            if value:
                return f"List[{get_type(value[0])}]"
            else:
                return "List"
        elif isinstance(value, dict):
            return "Dict"
        else:
            return "Any"

    def generate_model(
        data: Dict[str, Any], class_name: str, current_depth: int
    ) -> str:
        if current_depth > depth:
            return ""

        fields = []
        sub_models = []

        for key, value in data.items():
            if isinstance(value, dict) and current_depth < depth:
                sub_class_name = f"{class_name}_{key.capitalize()}"
                fields.append(f"    {key}: {sub_class_name}")
                sub_models.append(
                    generate_model(value, sub_class_name, current_depth + 1)
                )
            elif (
                isinstance(value, list)
                and value
                and isinstance(value[0], dict)
                and current_depth < depth
            ):
                sub_class_name = f"{class_name}_{key.capitalize()}Item"
                fields.append(f"    {key}: List[{sub_class_name}]")
                sub_models.append(
                    generate_model(value[0], sub_class_name, current_depth + 1)
                )
            else:
                fields.append(f"    {key}: {get_type(value)} = None")

        model = f"class {class_name}({parent_class}):\n"
        model += "\n".join(fields)
        model += "\n\n"
        model += "\n".join(sub_models)

        return model

    res = generate_model(data, prfix_class_name, 1)
    # Вернуть классы в обратном порядке
    s = "class "
    return s + s.join(x for x in reversed(res.split(s)) if x)
