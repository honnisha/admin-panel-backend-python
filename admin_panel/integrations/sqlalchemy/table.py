import logging
from typing import Any

from admin_panel import auth, schema
from admin_panel.auth import UserABC
from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.integrations.sqlalchemy.fields_schema import SQLAlchemyFieldsSchema
from admin_panel.schema.table.admin_action import ActionData, ActionMessage, ActionResult, admin_action
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _
from admin_panel.utils import DeserializeAction

from .autocomplete import SQLAlchemyAdminAutocompleteMixin

logger = logging.getLogger('admin_panel')







