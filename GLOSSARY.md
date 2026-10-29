# Aurora Data API dialect

The SQLAlchemy vocabulary for reaching Aurora PostgreSQL or Aurora MySQL through the Aurora Data API. This context is the dialect. It is not the HTTP client that carries statements.

## Language

**Aurora Data API**:
The stateless HTTP front door of an Aurora cluster, used instead of a database port.
_Avoid_: RDS Data API, Data API

**PostgreSQL dialect**:
This package's PostgreSQL-speaking half, aimed at the Aurora Data API.
_Avoid_: postgres driver, psycopg

**MySQL dialect**:
This package's MySQL-speaking half, aimed at the Aurora Data API.
_Avoid_: mysql driver, mysqlclient

**Cluster**:
An Aurora cluster, identified by its ARN, that holds one or more Databases.
_Avoid_: resource, resourceArn, database ARN

**Database**:
A named database inside a Cluster.
_Avoid_: schema, catalog, cluster

**Secret**:
The Secrets Manager object that holds the username and password used to enter a Cluster.
_Avoid_: password, credentials, connection string
