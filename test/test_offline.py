import datetime
import re
import tomllib
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import Column, Enum, create_engine

from sqlalchemy_better_aurora_data_api import (
    _ADA_TIMESTAMP,
    AuroraMySQLDataAPIDialect,
    AuroraPostgresDataAPIDialect,
)

_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("url", "dialect_class"),
    [
        ("postgresql+auroradataapi://:@/offline", AuroraPostgresDataAPIDialect),
        ("mysql+auroradataapi://:@/offline", AuroraMySQLDataAPIDialect),
    ],
    ids=["PostgreSQL dialect", "MySQL dialect"],
)
def test_url_resolves_to_the_dialect(url, dialect_class):
    engine = create_engine(url)

    assert type(engine.dialect) is dialect_class
    assert engine.dialect.driver == "aurora_data_api"


def test_timestamp_microsecond_padding():
    processor = _ADA_TIMESTAMP.result_processor(_ADA_TIMESTAMP, None, None)

    assert processor("2019-10-31 09:37:17.3186") == datetime.datetime.fromisoformat("2019-10-31 09:37:17.318600")


def test_mysql_dialect_charset_probe_returns_the_client_charset():
    class _StandInConnection:
        def __init__(self):
            self.sql = None

        def exec_driver_sql(self, sql):
            self.sql = sql
            row = ("character_set_client", "utf8mb4")

            class _Row:
                def fetchone(self):
                    return row

            return _Row()

    connection = _StandInConnection()

    charset = AuroraMySQLDataAPIDialect()._detect_charset(connection)

    assert (connection.sql, charset) == (
        "SHOW VARIABLES LIKE 'character_set_client'",
        "utf8mb4",
    )


def test_enum_in_list_compiles_to_one_cast_per_value():
    column = Column("color", Enum("red", "green", name="socks"))

    compiled = str(
        column.in_(["red", "green"]).compile(
            dialect=AuroraPostgresDataAPIDialect(),
            compile_kwargs={"render_postcompile": True},
        )
    )

    assert len(re.findall(r"CAST\(.*? AS socks\)", compiled)) == 2 and "CAST((" not in compiled, compiled


def test_package_depends_on_sqlalchemy_2_and_the_lock_resolves_2_1_6():
    with (_ROOT / "pyproject.toml").open("rb") as project_file:
        dependencies = tomllib.load(project_file)["project"]["dependencies"]
    with (_ROOT / "uv.lock").open("rb") as lock_file:
        packages = tomllib.load(lock_file)["package"]

    project = next(package for package in packages if package["name"] == "sqlalchemy-better-aurora-data-api")
    sqlalchemy = next(package for package in packages if package["name"] == "sqlalchemy")
    requirement = next(item for item in project["metadata"]["requires-dist"] if item["name"] == "sqlalchemy")

    assert "sqlalchemy>=2,<3" in dependencies
    assert requirement.get("specifier") == ">=2,<3"
    assert sqlalchemy["version"] == "2.1.6"


def test_readme_prerequisites_require_sqlalchemy_2():
    readme = (_ROOT / "README.md").read_text()
    _before, _marker, rest = readme.partition("## Prerequisites")
    section, _next_marker, _after = rest.partition("\n## ")

    assert "This package requires SQLAlchemy >= 2 and < 3." in section


def test_readme_quickstart_imports_text_and_executes_it():
    readme = (_ROOT / "README.md").read_text()
    _before, _marker, rest = readme.partition("## Usage")
    section, _next_marker, _after = rest.partition("\n## ")

    assert "from sqlalchemy import create_engine, text" in section
    assert 'conn.execute(text("select * from pg_catalog.pg_tables"))' in section


def test_readme_connect_args_link_points_at_sqlalchemy_2_docs():
    readme = (_ROOT / "README.md").read_text()

    assert "[`connect_args`](https://docs.sqlalchemy.org/en/20/core/engines.html#custom-dbapi-args)" in readme


def test_mysql_and_postgresql_dialect_comments_cite_sqlalchemy_2_internals():
    source = (_ROOT / "sqlalchemy_better_aurora_data_api" / "__init__.py").read_text()
    mysql = source.split("class AuroraMySQLDataAPIDialect", 1)[1].split("class AuroraPostgresDataAPIDialect", 1)[0]
    postgres = source.split("class AuroraPostgresDataAPIDialect", 1)[1].split("def register_dialects", 1)[0]
    url = "https://docs.sqlalchemy.org/en/20/core/internals.html#sqlalchemy.engine.interfaces.Dialect"

    assert url in mysql
    assert url in postgres
    assert "en/13/core/internals.html" not in mysql
    assert "en/13/core/internals.html" not in postgres


def test_mysql_live_example_executes_text():
    source = (_ROOT / "test" / "test.py").read_text()
    mysql = source.split("class TestAuroraDataAPIMySQLDialect", 1)[1]

    assert 'conn.execute(text("select * from information_schema.tables"))' in mysql


def test_ci_runs_offline_tests_without_a_sqlalchemy_version_matrix():
    workflow = (_ROOT / ".github" / "workflows" / "ci.yml").read_text()

    assert "uv run pytest test/test_offline.py" in workflow
    assert "sqlalchemy" not in workflow

def test_classifiers_readme_label_and_ci_matrix_list_the_declared_python_versions():
    declared = ("3.11", "3.12", "3.13", "3.14", "3.15")

    assert (
        _classifier_python_versions(),
        _readme_label_python_versions(),
        _ci_test_matrix_python_versions(),
    ) == (declared, declared, declared)


def _classifier_python_versions():
    with (_ROOT / "pyproject.toml").open("rb") as project_file:
        classifiers = tomllib.load(project_file)["project"]["classifiers"]
    prefix = "Programming Language :: Python :: "
    return tuple(
        classifier.removeprefix(prefix)
        for classifier in classifiers
        if classifier.startswith(prefix) and re.fullmatch(r"\d+\.\d+", classifier.removeprefix(prefix))
    )


def _readme_label_python_versions():
    lines = (_ROOT / "README.md").read_text().splitlines()
    title_index = next(index for index, line in enumerate(lines) if line.startswith("# "))
    badge_line = next(line.strip() for line in lines[title_index + 1 :] if line.strip())
    badge = re.fullmatch(r"!\[([^\]]+)\]\(([^)]+)\)", badge_line)
    if badge is None:
        return ()
    alt_text, badge_url = badge.groups()
    alt_versions = tuple(re.findall(r"\d+\.\d+", alt_text))
    message = parse_qs(urlparse(badge_url).query)["message"][0]
    message_versions = tuple(part.strip() for part in message.split("|"))
    if alt_versions != message_versions:
        return ()
    return message_versions


def _ci_test_matrix_python_versions():
    versions = []
    in_test_job = False
    collecting = False
    for line in (_ROOT / ".github" / "workflows" / "ci.yml").read_text().splitlines():
        if re.fullmatch(r"  [A-Za-z0-9_-]+:", line):
            if collecting:
                break
            in_test_job = line == "  test:"
            continue
        if not in_test_job:
            continue
        if line.strip() == "python-version:":
            collecting = True
            continue
        if not collecting:
            continue
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if not stripped.startswith("-"):
            break
        payload = stripped[1:].strip()
        version = re.fullmatch(
            r"(?:\"(\d+\.\d+)\"|'(\d+\.\d+)'|(\d+\.\d+))\s*(?:#.*)?",
            payload,
        )
        if version is None:
            versions.append(payload)
            continue
        versions.append(next(group for group in version.groups() if group is not None))
    return tuple(versions)
