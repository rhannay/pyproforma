import pytest
from pyproforma import LineItem, Model

@pytest.fixture
def sample_line_item_list():
    return [
        LineItem(
            name="item1",
            label="Item 1",
            category="revenue",
            values={2020: 100.0, 2021: 150.0}
        ),
        LineItem(
            name="item2",
            label="Item 2",
            category="expense",
            values={2020: 50.0, 2021: 75.0}
        ),
        LineItem(
            name="item3",
            label="Item 3",
            category="revenue",
            values={2020: 200.0, 2021: 250.0}
        )
    ]

@pytest.fixture
def sample_line_item_set():
    li_1 = LineItem(
        name="item1",
        label="Item 1",
        category="revenue",
        values={2020: 100.0, 2021: 150.0}
    )
    li_2 = LineItem(
        name="item2",
        label="Item 2",
        category="expense",
        values={2020: 50.0, 2021: 75.0}
    )
    li_3 = LineItem(
        name="item3",
        label="Item 3",
        category="revenue",
        values={2020: 200.0, 2021: 250.0}
    )
    return Model([li_1, li_2, li_3], years=[2020, 2021])