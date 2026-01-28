import pytest

from pyproforma.charts.chart_class import Chart, ChartDataSet

try:
    import matplotlib

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class TestChartDataSet:
    """Test cases for ChartDataSet initialization."""

    def test_init_with_defaults(self):
        """Test ChartDataSet initialization with default values."""
        data = [1.0, 2.0, 3.0]
        dataset = ChartDataSet(label="Test Dataset", data=data)

        assert dataset.label == "Test Dataset"
        assert dataset.data == data
        assert dataset.color is None  # Color defaults to None, assigned by Chart class
        assert dataset.type == "line"
        assert dataset.dashed is False

    def test_init_with_custom_values(self):
        """Test ChartDataSet initialization with custom values."""
        data = [10.5, None, 15.2, 8.7]
        dataset = ChartDataSet(
            label="Revenue", data=data, color="red", type="bar", dashed=True
        )

        assert dataset.label == "Revenue"
        assert dataset.data == data
        assert dataset.color == "red"
        assert dataset.type == "bar"
        assert dataset.dashed is True

    def test_init_with_all_chart_types(self):
        """Test ChartDataSet initialization with all valid chart types."""
        data = [1, 2, 3]

        # Test line type
        line_dataset = ChartDataSet("Line", data, type="line")
        assert line_dataset.type == "line"

        # Test bar type
        bar_dataset = ChartDataSet("Bar", data, type="bar")
        assert bar_dataset.type == "bar"

        # Test scatter type
        scatter_dataset = ChartDataSet("Scatter", data, type="scatter")
        assert scatter_dataset.type == "scatter"

    def test_init_with_invalid_chart_type(self):
        """Test ChartDataSet initialization with invalid chart type raises ValueError."""  # noqa: E501
        data = [1, 2, 3]

        with pytest.raises(ValueError, match="Invalid chart type 'pies'"):
            ChartDataSet("Test", data, type="pies")

        with pytest.raises(ValueError, match="Invalid chart type 'histogram'"):
            ChartDataSet("Test", data, type="histogram")

    def test_init_with_empty_data(self):
        """Test ChartDataSet initialization with empty data list."""
        dataset = ChartDataSet("Empty", [])
        assert dataset.data == []

    def test_init_with_none_values_in_data(self):
        """Test ChartDataSet initialization with None values in data."""
        data = [1.0, None, 3.0, None, 5.0]
        dataset = ChartDataSet("With Nones", data)
        assert dataset.data == data

    def test_repr(self):
        """Test ChartDataSet string representation."""
        dataset = ChartDataSet("Test", [1, 2, 3], color="green", type="bar")
        expected = "ChartDataSet(label='Test', type='bar', color='green')"
        assert repr(dataset) == expected


class TestChart:
    """Test cases for Chart initialization."""

    def test_init_with_defaults(self):
        """Test Chart initialization with default values."""
        labels = ["Q1", "Q2", "Q3", "Q4"]
        dataset = ChartDataSet("Revenue", [100, 200, 150, 300])
        data_sets = [dataset]

        chart = Chart(labels=labels, data_sets=data_sets)

        assert chart.id == "chart"
        assert chart.title == "Chart"
        assert chart.labels == labels
        assert chart.data_sets == data_sets
        assert chart.value_format is None

    def test_init_with_custom_values(self):
        """Test Chart initialization with custom values."""
        labels = ["Jan", "Feb", "Mar"]
        dataset1 = ChartDataSet("Sales", [1000, 1200, 1100])
        dataset2 = ChartDataSet("Costs", [800, 900, 850])
        data_sets = [dataset1, dataset2]

        chart = Chart(
            labels=labels,
            data_sets=data_sets,
            id="revenue_chart",
            title="Monthly Revenue",
            value_format="two_decimals",
        )

        assert chart.id == "revenue_chart"
        assert chart.title == "Monthly Revenue"
        assert chart.labels == labels
        assert chart.data_sets == data_sets
        assert chart.value_format == "two_decimals"

    def test_init_with_all_chart_types(self):
        """Test Chart initialization with datasets of different chart types."""
        labels = ["A", "B", "C"]

        # Test line type dataset
        line_dataset = ChartDataSet("Data", [1, 2, 3], type="line")
        line_chart = Chart(labels, [line_dataset])
        assert line_chart.data_sets[0].type == "line"

        # Test bar type dataset
        bar_dataset = ChartDataSet("Data", [1, 2, 3], type="bar")
        bar_chart = Chart(labels, [bar_dataset])
        assert bar_chart.data_sets[0].type == "bar"

        # Test scatter type dataset
        scatter_dataset = ChartDataSet("Data", [1, 2, 3], type="scatter")
        scatter_chart = Chart(labels, [scatter_dataset])
        assert scatter_chart.data_sets[0].type == "scatter"

    def test_init_with_mixed_chart_types(self):
        """Test Chart initialization with mixed chart types in datasets."""
        labels = ["A", "B", "C"]
        line_dataset = ChartDataSet("Line Data", [1, 2, 3], type="line")
        bar_dataset = ChartDataSet("Bar Data", [4, 5, 6], type="bar")
        data_sets = [line_dataset, bar_dataset]

        chart = Chart(labels, data_sets)
        assert chart.data_sets[0].type == "line"
        assert chart.data_sets[1].type == "bar"

    def test_init_with_single_dataset(self):
        """Test Chart initialization with single dataset."""
        labels = ["X", "Y", "Z"]
        dataset = ChartDataSet("Single", [10, 20, 30])

        chart = Chart(labels, [dataset])
        assert len(chart.data_sets) == 1
        assert chart.data_sets[0] == dataset

    def test_init_with_multiple_datasets(self):
        """Test Chart initialization with multiple datasets."""
        labels = ["Period 1", "Period 2", "Period 3"]
        dataset1 = ChartDataSet("Series A", [10, 15, 12])
        dataset2 = ChartDataSet("Series B", [8, 18, 14])
        dataset3 = ChartDataSet("Series C", [12, 10, 16])
        data_sets = [dataset1, dataset2, dataset3]

        chart = Chart(labels, data_sets)
        assert len(chart.data_sets) == 3
        assert chart.data_sets == data_sets

    def test_init_with_empty_labels(self):
        """Test Chart initialization with empty labels list."""
        dataset = ChartDataSet("Data", [])
        chart = Chart([], [dataset])
        assert chart.labels == []

    def test_init_with_empty_datasets(self):
        """Test Chart initialization with empty datasets list."""
        labels = ["A", "B", "C"]
        chart = Chart(labels, [])
        assert chart.data_sets == []

    def test_init_with_various_value_formats(self):
        """Test Chart initialization with different value formats."""
        labels = ["A", "B"]
        dataset = ChartDataSet("Data", [1, 2])
        data_sets = [dataset]

        formats = [
            "no_decimals",
            "two_decimals",
            "percent",
            "percent_one_decimal",
            "percent_two_decimals",
        ]

        for fmt in formats:
            chart = Chart(labels, data_sets, value_format=fmt)
            assert chart.value_format == fmt

    def test_repr(self):
        """Test Chart string representation."""
        labels = ["A", "B"]
        line_dataset = ChartDataSet("Line Data", [1, 2], type="line")
        bar_dataset = ChartDataSet("Bar Data", [3, 4], type="bar")
        chart = Chart(
            labels, [line_dataset, bar_dataset], id="test_chart", title="Test Chart"
        )

        expected = "Chart(id='test_chart', title='Test Chart', types=['line', 'bar'])"
        assert repr(chart) == expected

    def test_init_preserves_dataset_references(self):
        """Test that Chart initialization preserves references to dataset objects."""
        labels = ["X", "Y"]
        dataset = ChartDataSet("Original", [1, 2])
        chart = Chart(labels, [dataset])

        # Modify the original dataset
        dataset.label = "Modified"

        # Chart should reflect the change since it holds a reference
        assert chart.data_sets[0].label == "Modified"
        assert chart.data_sets[0] is dataset


@pytest.mark.skipif(
    not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed"
)
class TestChartMatplotlib:
    """Test cases for Chart.to_matplotlib() method."""

    def test_to_matplotlib_returns_figure_and_axes(self):
        """Test that to_matplotlib returns a figure and axes object."""
        labels = ["Q1", "Q2", "Q3", "Q4"]
        dataset = ChartDataSet("Revenue", [100, 200, 150, 300])
        chart = Chart(labels=labels, data_sets=[dataset])

        fig, ax = chart.to_matplotlib()

        assert fig is not None
        assert ax is not None
        assert hasattr(fig, "savefig")  # Check it's a matplotlib figure
        import matplotlib.pyplot as plt

        plt.close(fig)  # Clean up

    def test_to_matplotlib_line_chart(self):
        """Test creating a line chart with matplotlib."""
        labels = ["A", "B", "C", "D"]
        dataset = ChartDataSet("Line Data", [10, 20, 15, 25], type="line")
        chart = Chart(labels, [dataset], title="Line Chart Test")

        fig, ax = chart.to_matplotlib()

        assert ax.get_title() == "Line Chart Test"
        assert len(ax.lines) == 1  # One line
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_to_matplotlib_bar_chart(self):
        """Test creating a bar chart with matplotlib."""
        labels = ["A", "B", "C"]
        dataset = ChartDataSet("Bar Data", [5, 10, 7], type="bar")
        chart = Chart(labels, [dataset], title="Bar Chart Test")

        fig, ax = chart.to_matplotlib()

        assert ax.get_title() == "Bar Chart Test"
        assert len(ax.patches) == 3  # Three bars
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_to_matplotlib_scatter_chart(self):
        """Test creating a scatter chart with matplotlib."""
        labels = ["X", "Y", "Z"]
        dataset = ChartDataSet("Scatter Data", [1, 3, 2], type="scatter")
        chart = Chart(labels, [dataset], title="Scatter Chart Test")

        fig, ax = chart.to_matplotlib()

        assert ax.get_title() == "Scatter Chart Test"
        assert len(ax.collections) == 1  # One scatter collection
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_to_matplotlib_pie_chart(self):
        """Test creating a pie chart with matplotlib."""
        labels = ["A", "B", "C"]
        dataset = ChartDataSet("Pie Data", [30, 40, 30], type="pie")
        chart = Chart(labels, [dataset], title="Pie Chart Test")

        fig, ax = chart.to_matplotlib()

        assert ax.get_title() == "Pie Chart Test"
        assert len(ax.patches) == 3  # Three pie slices
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_to_matplotlib_mixed_chart_types(self):
        """Test creating a chart with mixed line and bar types."""
        labels = ["Q1", "Q2", "Q3"]
        line_dataset = ChartDataSet("Revenue", [100, 150, 130], type="line")
        bar_dataset = ChartDataSet("Costs", [80, 90, 85], type="bar")
        chart = Chart(labels, [line_dataset, bar_dataset], title="Mixed Chart")

        fig, ax = chart.to_matplotlib()

        assert ax.get_title() == "Mixed Chart"
        assert len(ax.lines) == 1  # One line
        assert len(ax.patches) == 3  # Three bars
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_to_matplotlib_with_custom_size(self):
        """Test creating a chart with custom width and height."""
        labels = ["A", "B"]
        dataset = ChartDataSet("Data", [1, 2])
        chart = Chart(labels, [dataset])

        fig, ax = chart.to_matplotlib(width=12, height=8)

        width, height = fig.get_size_inches()
        assert width == 12
        assert height == 8
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_to_matplotlib_with_legend(self):
        """Test that legend is shown when requested."""
        labels = ["A", "B"]
        dataset1 = ChartDataSet("Series 1", [1, 2])
        dataset2 = ChartDataSet("Series 2", [3, 4])
        chart = Chart(labels, [dataset1, dataset2])

        fig, ax = chart.to_matplotlib(show_legend=True)

        legend = ax.get_legend()
        assert legend is not None
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_to_matplotlib_without_legend(self):
        """Test that legend is hidden when not requested."""
        labels = ["A", "B"]
        dataset = ChartDataSet("Data", [1, 2])
        chart = Chart(labels, [dataset])

        fig, ax = chart.to_matplotlib(show_legend=False)

        legend = ax.get_legend()
        assert legend is None
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_to_matplotlib_dashed_line(self):
        """Test that dashed lines are rendered correctly."""
        labels = ["A", "B", "C"]
        dataset = ChartDataSet("Dashed", [1, 2, 3], type="line", dashed=True)
        chart = Chart(labels, [dataset])

        fig, ax = chart.to_matplotlib()

        # Check that the line has a dashed style
        line = ax.lines[0]
        assert line.get_linestyle() == "--"
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_to_matplotlib_with_value_format(self):
        """Test that value formatting is applied to the y-axis."""
        labels = ["A", "B", "C"]
        dataset = ChartDataSet("Data", [1000, 2000, 1500])
        chart = Chart(labels, [dataset], value_format="no_decimals")

        fig, ax = chart.to_matplotlib()

        # The formatter should be set
        formatter = ax.yaxis.get_major_formatter()
        assert formatter is not None
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_to_matplotlib_multiple_bars(self):
        """Test creating a chart with multiple bar datasets (grouped bars)."""
        labels = ["Q1", "Q2", "Q3"]
        dataset1 = ChartDataSet("2023", [100, 150, 130], type="bar")
        dataset2 = ChartDataSet("2024", [110, 160, 140], type="bar")
        chart = Chart(labels, [dataset1, dataset2], title="Grouped Bars")

        fig, ax = chart.to_matplotlib()

        assert ax.get_title() == "Grouped Bars"
        assert len(ax.patches) == 6  # Six bars total (2 datasets * 3 labels)
        import matplotlib.pyplot as plt

        plt.close(fig)

