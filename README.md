# sqlalchemy-aurora-data-api - An AWS Aurora Serverless Data API dialect for SQLAlchemy

## Context

This package is the [SQLAlchemy](https://www.sqlalchemy.org) dialect for the
[Aurora Data API](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/data-api.html).
It is not the HTTP client that carries statements. That client is
[aurora-data-api](https://github.com/chanzuckerberg/aurora-data-api), which this package depends on.

The dialect has two halves. The PostgreSQL dialect is registered as `postgresql+auroradataapi://`.
The MySQL dialect is registered as `mysql+auroradataapi://`.

A connection names three things:

* **Cluster**: the Aurora cluster, identified by its ARN. The Aurora Data API calls this ARN `resourceArn`.
* **Database**: a named database inside the Cluster. This is the path of the connection URL.
* **Secret**: the Secrets Manager object that holds the username and password used to enter the Cluster.

The dialect and the Database name are the only parts of the connection URL that select a target.
The Cluster ARN and the Secret ARN are passed beside the URL.

## Installation

```
pip install sqlalchemy-aurora-data-api
```

## Prerequisites

* Set up an
  [AWS Aurora Serverless cluster](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless.html)
  and enable the Aurora Data API for it. If you have previously set up an Aurora Serverless cluster, you can enable the Aurora Data API
  with the following [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html) command:

```
aws rds modify-db-cluster --db-cluster-identifier DB_CLUSTER_NAME --enable-http-endpoint --apply-immediately
```

* Save the username and password in a Secret in
  [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html),
  as a JSON object with the keys `username` and `password`:

```
aws secretsmanager create-secret --name rds-db-credentials/MY_DB
aws secretsmanager put-secret-value --secret-id rds-db-credentials/MY_DB --secret-string "$(jq -n '.username=env.PGUSER | .password=env.PGPASSWORD')"
```

* Configure your AWS command line credentials using
  [standard AWS conventions](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html).
  You can verify that everything works correctly by running a test query via the AWS CLI:

```
aws rds-data execute-statement --resource-arn RESOURCE_ARN --secret-arn SECRET_ARN --sql "select * from pg_catalog.pg_tables"
```

  * Here, RESOURCE_ARN is the Cluster ARN, which can be found in the
    [AWS RDS Console](https://console.aws.amazon.com/rds/home#databases:) (click on your Cluster, then "Configuration")
    or in the CLI by running `aws rds describe-db-clusters`. SECRET_ARN is the Secret
    created above. The `--resource-arn` flag is the AWS CLI name for the Cluster ARN.

  * When running deployed code (on an EC2 instance, ECS/EKS container, or Lambda), you can use the managed IAM policy
    **AmazonRDSDataFullAccess** to grant your IAM role permissions to access the Aurora Data API (while this policy is
    convenient for testing, we recommend that you create your own scoped down least-privilege policy for production
    applications).

## Usage

Pass the Cluster ARN and the Secret ARN as
`sqlalchemy.create_engine()` [`connect_args`](https://docs.sqlalchemy.org/en/13/core/engines.html#custom-dbapi-args).
The Database name is the URL path (`my_db_name` in the example below). Every other part of the URL is ignored.

* `aurora_cluster_arn` is the Cluster ARN. The
  [Aurora Data API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds-data.html)
  calls the same value `resourceArn`. If omitted here, `AURORA_CLUSTER_ARN` is used.

* `secret_arn` is the Secret ARN. If omitted here, `AURORA_SECRET_ARN` is used.

```python
from sqlalchemy import create_engine

cluster_arn = "arn:aws:rds:us-east-1:123456789012:cluster:my-aurora-serverless-cluster"
secret_arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:rds-db-credentials/MY_DB"

engine = create_engine('postgresql+auroradataapi://:@/my_db_name',
                       echo=True,
                       connect_args=dict(aurora_cluster_arn=cluster_arn, secret_arn=secret_arn))

with engine.connect() as conn:
    for result in conn.execute("select * from pg_catalog.pg_tables"):
        print(result)
```

## Motivation

The [Aurora Data API](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/data-api.html) is the link between the
AWS Lambda serverless environment and the sophisticated features provided by PostgreSQL and MySQL. The Aurora Data API tunnels
SQL over HTTP, which has advantages in the context of AWS Lambda:

* It eliminates the need to open database ports to the AWS Lambda public IP address pool
* It uses stateless HTTP connections instead of stateful internal TCP connection pools used by most database drivers
  (the stateful pools become invalid after going through
  [AWS Lambda freeze-thaw cycles](https://docs.aws.amazon.com/lambda/latest/dg/running-lambda-code.html), causing
  connection errors and burdening the database server with abandoned invalid connections)
* It uses AWS role-based authentication, eliminating the need for the Lambda to handle database credentials directly

## Debugging

This package uses standard Python logging conventions. To enable debug output, set the package log level to DEBUG:

```python
logging.basicConfig()

logging.getLogger("aurora_data_api").setLevel(logging.DEBUG)
```

## Links

* [Project home page (GitHub)](https://github.com/chanzuckerberg/sqlalchemy-aurora-data-api)
* [Documentation (Read the Docs)](https://sqlalchemy-aurora-data-api.readthedocs.io/en/latest/)
* [Package distribution (PyPI)](https://pypi.python.org/pypi/sqlalchemy-aurora-data-api)
* [Change log](CHANGES.md)
* [aurora-data-api](https://github.com/chanzuckerberg/aurora-data-api), the Python DB-API 2.0 client that
  sqlalchemy-aurora-data-api depends on

### Bugs

Please report bugs, issues, feature requests, etc. on
[GitHub](https://github.com/chanzuckerberg/sqlalchemy-aurora-data-api/issues).

## License

Licensed under the terms of the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

[![Build status](https://travis-ci.org/chanzuckerberg/sqlalchemy-aurora-data-api.png)](https://travis-ci.org/chanzuckerberg/sqlalchemy-aurora-data-api)
[![Coverage](https://codecov.io/github/chanzuckerberg/sqlalchemy-aurora-data-api/coverage.svg?branch=master)](https://codecov.io/github/chanzuckerberg/sqlalchemy-aurora-data-api?branch=master)
[![PyPI version](https://img.shields.io/pypi/v/sqlalchemy-aurora-data-api.svg)](https://pypi.python.org/pypi/sqlalchemy-aurora-data-api)
[![PyPI license](https://img.shields.io/pypi/l/sqlalchemy-aurora-data-api.svg)](https://pypi.python.org/pypi/sqlalchemy-aurora-data-api)
[![Documentation status](https://readthedocs.org/projects/sqlalchemy-aurora-data-api/badge/?version=latest)](https://sqlalchemy-aurora-data-api.readthedocs.org/)
