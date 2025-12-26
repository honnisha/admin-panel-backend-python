import logging

from admin_panel import auth, schema
from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.integrations.sqlalchemy.table.base import record_to_dict
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _

logger = logging.getLogger('admin_panel')


class SQLAlchemyAdminListMixin:

    def apply_filters(self, stmt, list_data):
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import or_, String
        from sqlalchemy.orm import InstrumentedAttribute

        # whitelist из schema
        allowed_fields = set(self.table_schema.get_fields().keys())

        # filters
        for name, value in list_data.filters.filters.items():
            if value is None or name not in allowed_fields:
                continue

            column = getattr(self.model, name, None)
            if not isinstance(column, InstrumentedAttribute):
                continue

            if isinstance(value, list):
                stmt = stmt.where(column.in_(value))
            else:
                stmt = stmt.where(column == value)

        # search (только по строковым и только разрешённым)
        if list_data.search:
            search = f"%{list_data.search}%"
            conditions = []

            for name in allowed_fields:
                column = getattr(self.model, name, None)
                if (
                    isinstance(column, InstrumentedAttribute)
                    and isinstance(column.property.columns[0].type, String)
                ):
                    conditions.append(column.ilike(search))

            if conditions:
                stmt = stmt.where(or_(*conditions))

        return stmt

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    async def get_list(
        self,
        list_data: schema.ListData,
        user: auth.UserABC,
        language_manager: LanguageManager,
    ) -> schema.TableListResult:
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import func, select
        from sqlalchemy.orm import selectinload

        # Count
        try:
            async with self.db_async_session() as session:
                total_count = await session.scalar(
                    select(func.count()).select_from(self.model)
                )
        except ConnectionRefusedError as e:
            logger.exception(
                'SQLAlchemy %s get_list db error: %s', type(self).__name__, e,
            )
            msg = _('connection_refused_error') % {'error': str(e)}
            raise AdminAPIException(
                APIError(message=msg, code='connection_refused_error'),
                status_code=500,
            ) from e

        total_count = int(total_count or 0)

        stmt = self.get_queryset()
        stmt = self.apply_filters(stmt, list_data)

        # Eager-load related fields
        for _slug, field in self.table_schema.get_fields().items():
            # pylint: disable=protected-access
            if field._type == "related" and field.rel_name:
                stmt = stmt.options(selectinload(getattr(self.model, field.rel_name)))

        data = []
        async with self.db_async_session() as session:
            records = (await session.execute(stmt)).scalars().all()
            for record in records:
                line = await self.table_schema.serialize(
                    record_to_dict(record),
                    extra={"record": record, "user": user},
                )
                data.append(line)

        return schema.TableListResult(data=data, total_count=total_count)
