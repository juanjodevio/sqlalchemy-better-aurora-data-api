import datetime

import pytest
from sqlalchemy import create_engine

from sqlalchemy_better_aurora_data_api import (
    _ADA_TIMESTAMP,
    AuroraMySQLDataAPIDialect,
    AuroraPostgresDataAPIDialect,
)


@pytest.mark.parametrize(
    ("url", "dialect_class"),
    [
        ("postgresql+auroradataapi://:@/offline", AuroraPostgresDataAPIDialect),
        ("mysql+auroradataapi://:@/offline", AuroraMySQLDataAPIDialect),
    ],
    ids=["PostgreSQL dialect", "MySQL dialect"],
)
def test_url_resolves_to_the_postgresql_dialect_and_the_mysql_dialect(url, dialect_class):
    engine = create_engine(url)

    assert type(engine.dialect) is dialect_class
    assert engine.dialect.driver == "aurora_data_api"


def test_timestamp_microsecond_padding():
    processor = _ADA_TIMESTAMP.result_processor(_ADA_TIMESTAMP, None, None)

    assert processor("2019-10-31 09:37:17.3186") == datetime.datetime.fromisoformat("2019-10-31 09:37:17.318600")
