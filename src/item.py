# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import GObject, Graphs

from graphs import misc


def new_from_dict(dictionary: dict):
    match dictionary["type"]:
        case "GraphsDataItem":
            cls = DataItem
        case "GrapsTextItem":
            cls = TextItem
        case "GrapsFillItem":
            cls = FillItem
        case _:
            pass
    dictionary.pop("type")
    return cls(**dictionary)


def to_dict(item):
    dictionary = {key: item.get_property(key) for key in dir(item.props)}
    dictionary["type"] = item.__gtype_name__
    return dictionary


class DataItem(Graphs.Item):
    __gtype_name__ = "GraphsDataItem"

    xdata = GObject.Property(type=object)
    ydata = GObject.Property(type=object)
    linestyle = GObject.Property(type=int, default=1)
    linewidth = GObject.Property(type=float, default=3)
    markerstyle = GObject.Property(type=int, default=0)
    markersize = GObject.Property(type=float, default=7)

    @classmethod
    def new(cls, params, xdata=None, ydata=None, **kwargs):
        return cls(
            linestyle=misc.LINESTYLES.index(params["lines.linestyle"]),
            linewidth=params["lines.linewidth"],
            markerstyle=misc.MARKERSTYLES.index(params["lines.marker"]),
            markersize=params["lines.markersize"],
            xdata=xdata, ydata=ydata, **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for prop in ("xdata", "ydata"):
            if self.get_property(prop) is None:
                self.set_property(prop, [])

    def reset(self, params):
        self.props.linestyle = misc.LINESTYLES.index(params["lines.linestyle"])
        self.props.linewidth = params["lines.linewidth"]
        self.props.markerstyle = \
            misc.MARKERSTYLES.index(params["lines.marker"])
        self.props.markersize = params["lines.markersize"]
        self.color = "000000"


class TextItem(Graphs.Item):
    __gtype_name__ = "GraphsTextItem"

    xanchor = GObject.Property(type=float, default=0)
    yanchor = GObject.Property(type=float, default=0)
    text = GObject.Property(type=str, default="")
    size = GObject.Property(type=float, default=12)
    rotation = GObject.Property(type=int, default=0, minimum=0, maximum=360)

    @classmethod
    def new(cls, params, xanchor=0, yanchor=0, text="", **kwargs):
        return cls(
            size=params["font.size"], color=params["text.color"],
            xanchor=xanchor, yanchor=yanchor, text=text, **kwargs,
        )

    def reset(self, params):
        self.props.size = params["font.size"]
        self.props.color = params["text.color"]


class FillItem(Graphs.Item):
    __gtype_name__ = "GraphsFillItem"

    data = GObject.Property(type=object)

    @classmethod
    def new(cls, _params, data, **kwargs):
        return cls(data=data, **kwargs)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.data is None:
            self.props.data = (None, None, None)

    def reset(self):
        pass
