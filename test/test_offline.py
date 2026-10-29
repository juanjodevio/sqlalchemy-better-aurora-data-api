import datetime

from sqlalchemy import create_engine

from sqlalchemy_better_aurora_data_api import (
    _ADA_TIMESTAMP,
    AuroraMySQLDataAPIDialect,
    AuroraPostgresDataAPIDialect,
)


def test_postgresql_dialect_url_resolves_to_the_postgresql_dialect():
    engine = create_engine("postgresql+auroradataapi://:@/offline")

    assert type(engine.dialect) is AuroraPostgresDataAPIDialect
    assert engine.dialect.driver == "aurora_data_api"


def test_mysql_dialect_url_resolves_to_the_mysql_dialect():
    engine = create_engine("mysql+auroradataapi://:@/offline")

    assert type(engine.dialect) is AuroraMySQLDataAPIDialect
    assert engine.dialect.driver == "aurora_data_api"


def test_timestamp_microsecond_padding():
    processor = _ADA_TIMESTAMP.result_processor(_ADA_TIMESTAMP, None, None)

    assert processor("2019-10-31 09:37:17.3186") == datetime.datetime.fromisoformat("2019-10-31 09:37:17.318600")
