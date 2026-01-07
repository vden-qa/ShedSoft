import re
from sqlalchemy.orm import MappedAsDataclass, DeclarativeBase, declared_attr, Mapped, mapped_column


class Base(MappedAsDataclass, DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Преобразуем CamelCase в snake_case
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        
        # Применяем правила множественного числа
        if name.endswith('y') and len(name) > 1 and name[-2] not in 'aeiou':
            return name[:-1] + 'ies'
        elif name.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return name + 'es'
        else:
            return name + 's'

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True, init=False)
