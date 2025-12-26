from admin_panel.schema.table.admin_action import ActionData, ActionMessage, ActionResult, admin_action
from admin_panel.translations import TranslateText as _


class SQLAlchemyDeleteAction:
    @admin_action(
        title=_('delete'),
        confirmation_text=_('delete_confirmation_text'),
        base_color='red-lighten-2',
        variant='outlined',
    )
    async def delete(self, action_data: ActionData):
        return ActionResult(message=ActionMessage(_('deleted_successfully')))
