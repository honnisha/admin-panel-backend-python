from typing import Any

from pydantic.dataclasses import dataclass

from admin_panel.schema.table.fields.base import TableField


@dataclass
class SQLAlchemyRelatedField(TableField):
    queryset: Any = None
    many: bool = False
    _type: str = 'related'
