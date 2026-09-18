# Hardened container image for termdat-mcp (SEC-007).
# Runs as a non-root user, on the Streamable HTTP transport, bound to 0.0.0.0
# *only* here — the container network namespace is isolated and this is an
# explicit opt-in.
FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
# Non-root user with a high UID (SEC-007).
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin termdat
COPY --from=build /install /usr/local
USER 10001

# Streamable HTTP on /mcp; 0.0.0.0 is deliberate and container-scoped (paired
# with SEC-016). Not `sse`: the SDK's SSE transport has no branch into MCP
# protocol revision 2026-07-28, so that value served a container that could not
# speak the revision this server documents.
ENV TERMDAT_MCP_TRANSPORT=streamable-http \
    HOST=0.0.0.0 \
    PORT=8000 \
    TERMDAT_MCP_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1
EXPOSE 8000
ENTRYPOINT ["termdat-mcp"]
