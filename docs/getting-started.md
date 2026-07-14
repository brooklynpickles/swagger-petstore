# Getting started with the Petstore API

The Petstore API is a sample implementation used to demonstrate OpenAPI
tooling. It exposes endpoints for managing pets, orders, and user accounts.

## Authentication

Most write operations require an API key, passed in the `api_key` header.
Read operations against the `/pet/findByStatus` endpoint do not require
authentication.

## Making a request

Send requests to the base path shown in the `servers` block of the OpenAPI
document. Each endpoint accepts and returns JSON, and the schema for every
request and response body is described in the spec's `components.schemas`
section.

## Error handling

The API returns standard HTTP status codes. A 404 means the requested pet,
order, or user was not found. A 400 means the request body failed
validation against the schema.
