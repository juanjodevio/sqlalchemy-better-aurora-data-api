import datetime
import re
import tomllib
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from sqlalchemy import create_engine

from sqlalchemy_better_aurora_data_api import (
    _ADA_TIMESTAMP,
    AuroraMySQLDataAPIDialect,
    AuroraPostgresDataAPIDialect,
)

_ROOT = Path(__file__).resolve().parents[1]


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
        version = re.fullmatch(r" +- [\"'](\d+\.\d+)[\"']", line)
        if version is None:
            break
        versions.append(version.group(1))
    return tuple(versions)
