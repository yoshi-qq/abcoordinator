from typing import Union


JSONBaseType = Union[str, int, float, bool, None]
JSONDict = dict[str, "JSONType"]
JSONList = list["JSONType"]
JSONType = Union[JSONBaseType, JSONList, JSONDict]

Content = JSONDict | None