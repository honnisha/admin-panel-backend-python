from admin_panel.schema.base import UserABC
from admin_panel.schema.sqlalchemy.autocomplete import SQLAlchemyAdminAutocompleteMixin
from admin_panel.schema.table.admin_action import ActionData, ActionMessage, ActionResult, admin_action
from admin_panel.schema.table.category_table import CategoryTable
from admin_panel.schema.table.fields_schema import FieldsSchema
from admin_panel.schema.table.table_models import CreateResult, ListData, TableListResult, UpdateResult


class SQLAlchemyFieldsSchema(FieldsSchema):
    pass


class SQLAlchemyDeleteAction:
    @admin_action(title='Delete', confirmation_text='Are you sure?')
    async def delete(self, action_data: ActionData):
        return ActionResult(message=ActionMessage('test'))


class SQLAlchemyAdminBase(SQLAlchemyAdminAutocompleteMixin, CategoryTable):
    async def get_list(self, list_data: ListData, user: UserABC) -> TableListResult:
        return TableListResult(
            data=[],
            total_count=0,
        )


class SQLAlchemyAdminCreate:
    async def create(self, data: dict, user: UserABC) -> CreateResult:
        return CreateResult(pk=0)


class SQLAlchemyAdminUpdate:
    async def update(self, pk, data: dict, user: UserABC) -> UpdateResult:
        return UpdateResult(pk=0)
