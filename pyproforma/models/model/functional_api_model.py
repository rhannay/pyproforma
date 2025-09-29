from __future__ import annotations
from ..line_item import LineItem
from types import MethodType
from typing import Union
from ..expression import Expression
from pyproforma.tables import Tables
from pyproforma.charts import Charts

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
    
    def define(self, line_item_name, expr: LineItem | float | Expression = None) -> LineItem:
        if line_item_name not in self._value_store:
            self._value_store[line_item_name] = LineItem(name=line_item_name)

        if expr is None:
            return self._value_store[line_item_name]
        
        if not isinstance(expr, (int, float, LineItem, Expression)):
            raise ValueError(f'Unsupported type for defining expression: {type(expr)}')
        
        expression = expr
        if isinstance(expr, (int, float)):
            expression = Expression(lambda year: expr)
        elif isinstance(expr, LineItem):
            expression = Expression(lambda year: expr.get_value(year))

        fn = expression.fn
        def set_value(obj: LineItem, year):
            obj.values[year] = fn(year) 
        self._value_store[line_item_name].set_value = MethodType(set_value, self._value_store[line_item_name])
        return self._value_store[line_item_name]
    


    @property
    def tables(self):
        """Tables namespace"""
        return Tables(self)

    @property
    def charts(self):
        """Charts namespace"""
        return Charts(self)
    
def create_functional_api_model(line_item_names):
    model = FunctionalApiModel(line_item_names=line_item_names)
    return model, model._value_store.values()
