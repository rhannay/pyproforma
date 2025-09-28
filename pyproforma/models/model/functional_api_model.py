from __future__ import annotations
from ..line_item import LineItem, LaggedLineItem
from types import MethodType

class FunctionalApiModel:
    def __init__(self, line_item_names: list[str] = None):
        self._value_store: dict[str, LineItem] = {}
        if line_item_names:
            for name in line_item_names:
                lineitem = LineItem(name=name)
                self._value_store[name] = lineitem
        
    def value(self, line_item_name: str, year: int | list[int]):
        if isinstance(year, int):        
            return self._value_store[line_item_name].get_value(year)
        else:
            return {y:self._value_store[line_item_name].get_value(y) for y in year}
    
    def define(self, line_item_name, expr: float | LineItem | callable):
        if line_item_name not in self._value_store:
            self._value_store[line_item_name] = LineItem(name=line_item_name)
        if isinstance(expr, float):
            fn = lambda year: expr
        elif isinstance(expr, LineItem) or isinstance(expr, LaggedLineItem):
            fn = lambda year: expr.get_value(year)
        elif callable(expr):
            fn = expr
        else:
            raise ValueError(f'expr of type {type(expr)} not valid.')
        def set_value(obj: LineItem, year):
            obj.values[year] = fn(year)
        self._value_store[line_item_name].set_value = MethodType(set_value, self._value_store[line_item_name])
    
def create_function_api_model(line_item_names):
    model = FunctionalApiModel(line_item_names=line_item_names)
    return model, model._value_store.values()
