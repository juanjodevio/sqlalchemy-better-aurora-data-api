# Copyright 2019 Andrey Kislyuk
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modified in sqlalchemy-better-aurora-data-api, a derivative of
# sqlalchemy-aurora-data-api. See NOTICE.
"""
sqlalchemy-better-aurora-data-api
"""

import datetime
import json
import re

import aurora_data_api
import sqlalchemy.sql.sqltypes as sqltypes
from sqlalchemy import cast, func, util
from sqlalchemy.dialects.mysql.base import MySQLDialect
from sqlalchemy.dialects.postgresql import ARRAY, DATE, ENUM, JSON, JSONB, TIME, TIMESTAMP, UUID
from sqlalchemy.dialects.postgresql.base import PGDialect


class _ADA_SA_JSON(sqltypes.JSON):
    def bind_expression(self, value):
        return cast(value, sqltypes.JSON)


class _ADA_JSON(JSON):
    def bind_expression(self, value):
        return cast(value, JSON)


class _ADA_JSONB(JSONB):
    def bind_expression(self, value):
        return cast(value, JSONB)


class _ADA_UUID(UUID):
    def bind_expression(self, value):
        return cast(value, UUID)


class _ADA_ENUM(ENUM):
    def bind_expression(self, value):
        return cast(value, self)


# TODO: is TZ awareness needed here?
class _ADA_DATETIME_MIXIN:
    iso_ts_re = re.compile(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+")

    @staticmethod
    def ms(value):
        # Three digit fractional second component, truncated and zero padded. This is what the data api requires.
        return str(value.microsecond).zfill(6)[:-3]

    def bind_processor(self, dialect):
        def process(value):
            return value.isoformat() if isinstance(value, self.py_type) else value

        return process

    def bind_expression(self, value):
        return cast(value, self.sa_type)

    def result_processor(self, dialect, coltype):
        def process(value):
            # When the microsecond component ends in zeros, they are omitted from the return value,
            # and datetime.datetime.fromisoformat can't parse the result (example: '2019-10-31 09:37:17.31869
            # '). Pad it.
            if isinstance(value, str) and self.iso_ts_re.match(value):
                value = self.iso_ts_re.sub(lambda match: match.group(0).ljust(26, "0"), value)
            if isinstance(value, str):
                try:
                    return self.py_type.fromisoformat(value)
                except AttributeError:  # fromisoformat not supported on Python < 3.7
                    if self.py_type == datetime.date:
                        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
                    if self.py_type == datetime.time:
                        return datetime.datetime.strptime(value, "%H:%M:%S").time()
                    if "." in value:
                        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                    return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return value

        return process


class _ADA_DATE(_ADA_DATETIME_MIXIN, DATE):
    py_type = datetime.date
    sa_type = sqltypes.Date

    def bind_processor(self, dialect):
        def process(value):
            return value.strftime("%Y-%m-%d") if isinstance(value, self.py_type) else value

        return process


class _ADA_TIME(_ADA_DATETIME_MIXIN, TIME):
    py_type = datetime.time
    sa_type = sqltypes.Time

    def bind_processor(self, dialect):
        def process(value):
            return value.strftime("%H:%M:%S.") + self.ms(value) if isinstance(value, self.py_type) else value

        return process


class _ADA_TIMESTAMP(_ADA_DATETIME_MIXIN, TIMESTAMP):
    py_type = datetime.datetime
    sa_type = sqltypes.DateTime

    def bind_processor(self, dialect):
        def process(value):
            return value.strftime("%Y-%m-%d %H:%M:%S.") + self.ms(value) if isinstance(value, self.py_type) else value

        return process


class _ADA_ARRAY(ARRAY):
    def bind_processor(self, dialect):
        def process(value):
            # FIXME: escape strings properly here
            return "\v".join(value) if isinstance(value, list) else value

        return process

    def bind_expression(self, value):
        return func.string_to_array(value, "\v")


class AuroraMySQLDataAPIDialect(MySQLDialect):
    # See https://docs.sqlalchemy.org/en/13/core/internals.html#sqlalchemy.engine.interfaces.Dialect
    driver = "aurora_data_api"
    default_schema_name = None
    supports_native_decimal = True
    colspecs = util.update_copy(
        MySQLDialect.colspecs,
        {
            sqltypes.Date: _ADA_DATE,
            sqltypes.Time: _ADA_TIME,
            sqltypes.DateTime: _ADA_TIMESTAMP,
        },
    )
    supports_statement_cache = True

    @classmethod
    def import_dbapi(cls):
        return aurora_data_api

    def _detect_charset(self, connection):
        return connection.execute("SHOW VARIABLES LIKE 'character_set_client'").fetchone()[1]

    def _extract_error_code(self, exception):
        return exception.args[0].value


class AuroraPostgresDataAPIDialect(PGDialect):
    # See https://docs.sqlalchemy.org/en/13/core/internals.html#sqlalchemy.engine.interfaces.Dialect
    driver = "aurora_data_api"
    default_schema_name = None
    colspecs = util.update_copy(
        PGDialect.colspecs,
        {
            sqltypes.JSON: _ADA_SA_JSON,
            JSON: _ADA_JSON,
            JSONB: _ADA_JSONB,
            UUID: _ADA_UUID,
            sqltypes.Date: _ADA_DATE,
            sqltypes.Time: _ADA_TIME,
            sqltypes.DateTime: _ADA_TIMESTAMP,
            sqltypes.Enum: _ADA_ENUM,
            ARRAY: _ADA_ARRAY,
        },
    )
    supports_sane_multi_rowcount = False
    supports_statement_cache = True

    @classmethod
    def import_dbapi(cls):
        return aurora_data_api

    def _extract_error_code(self, exception):
        return exception.args[0].value


def register_dialects():
    from sqlalchemy.dialects import registry

    registry.register("mysql.auroradataapi", __name__, AuroraMySQLDataAPIDialect.__name__)
    registry.register("postgresql.auroradataapi", __name__, AuroraPostgresDataAPIDialect.__name__)
