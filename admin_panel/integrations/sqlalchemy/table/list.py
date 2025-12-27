import logging

from admin_panel import auth, schema
from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.integrations.sqlalchemy.table.base import record_to_dict
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _

logger = logging.getLogger('admin_panel')


class SQLAlchemyAdminListMixin:
    def apply_ordering(self, stmt, list_data):
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import asc, desc
        from sqlalchemy.orm import InstrumentedAttribute

        if not list_data.ordering:
            return stmt

        ordering = list_data.ordering
        direction = asc

        if ordering.startswith("-"):
            ordering = ordering[1:]
            direction = desc

        if ordering not in self.ordering_fields:
            msg = f'Ordering "{ordering}" is not allowed; available options: {self.ordering_fields}'
            raise ValueError(msg)

        column = getattr(self.model, ordering, None)
        if not isinstance(column, InstrumentedAttribute):
            raise AttributeError(
                f'{type(self).__name__} ordering field "{ordering}" not found in model {self.model}'
            )

        return stmt.order_by(direction(column))

    def apply_search(self, stmt, list_data: schema.ListData):
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import String, cast, or_
        from sqlalchemy.orm import InstrumentedAttribute

        if not self.search_fields or not list_data.filters.search:
            return stmt

        search = f"%{list_data.filters.search}%"
        conditions = []

        for field_slug in self.search_fields:
            column = getattr(self.model, field_slug, None)
            if not isinstance(column, InstrumentedAttribute):
                msg = f'{type(self).__name__} filter "{field_slug}" not found as field inside model {self.model}'
                raise AttributeError(msg)

            conditions.append(cast(column, String).ilike(search))

        if conditions:
            stmt = stmt.where(or_(*conditions))

        return stmt

    def apply_filters(self, stmt, list_data: schema.ListData):
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import String, cast
        from sqlalchemy.orm import InstrumentedAttribute

        if not self.table_filters or not list_data.filters.filters:
            return stmt

        # filters
        for field_slug, value in list_data.filters.filters.items():
            available_filters = list(self.table_filters.get_fields().keys())
            if field_slug not in available_filters:
                msg = f'{type(self).__name__} filter "{field_slug}" not found inside table_filters fields: {available_filters}'
                raise AttributeError(msg)

            column = getattr(self.model, field_slug, None)
            if not isinstance(column, InstrumentedAttribute):
                msg = f'{type(self).__name__} filter "{field_slug}" not found as field inside model {self.model}'
                raise AttributeError(msg)

            if isinstance(value, list):
                stmt = stmt.where(column.in_(value))

            elif isinstance(value, str):
                stmt = stmt.where(
                    cast(column, String).like(f"%{value}%")
                )

            else:
                stmt = stmt.where(column == value)

        return stmt

    def apply_pagination(self, stmt, list_data: schema.ListData):
        page = max(1, list_data.page or 1)
        limit = min(150, max(1, list_data.limit or 25))

        offset = (page - 1) * limit

        return stmt.limit(limit).offset(offset)

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

        stmt = self.get_queryset()
        stmt = self.apply_filters(stmt, list_data)
        stmt = self.apply_search(stmt, list_data)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        stmt = self.apply_pagination(stmt, list_data)

        # Count
        try:
            async with self.db_async_session() as session:
                total_count = await session.scalar(count_stmt)

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
