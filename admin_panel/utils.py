from pydantic import TypeAdapter


class DeserializeAction:
    CREATE = 0
    UPDATE = 1
    TABLE_ACTION = 2


class DataclassBase:
    def model_dump(self, *args, **kwargs) -> dict:
        adapter = TypeAdapter(type(self))
        return adapter.dump_python(self, *args, **kwargs)
