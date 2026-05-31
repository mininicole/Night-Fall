from __future__ import annotations

import asyncio
import importlib.util
import os
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from night_fall.config import load_config
from night_fall.extension import register_night_fall


def import_ombre_server(ombre_home: Path):
    server_path = ombre_home / "server.py"
    if not server_path.exists():
        raise FileNotFoundError(f"Ombre server.py not found: {server_path}")
    sys.path.insert(0, str(ombre_home))
    spec = importlib.util.spec_from_file_location("ombre_server", server_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import Ombre server from {server_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ombre_server"] = module
    spec.loader.exec_module(module)
    return module


def run_ombre_server(ombre_server) -> None:
    # OMBRE_TRANSPORT env var takes precedence (used by Docker / cloud deployments).
    transport = os.environ.get("OMBRE_TRANSPORT") or ombre_server.config.get("transport", "stdio")
    logger = getattr(ombre_server, "logger", None)
    if logger:
        logger.info(f"Ombre Brain starting with Night Fall | transport: {transport}")

    if transport in ("sse", "streamable-http"):
        import threading
        import httpx
        import uvicorn
        from starlette.middleware.cors import CORSMiddleware

        port = int(getattr(ombre_server, "OMBRE_PORT", os.environ.get("OMBRE_PORT", 8000)))

        async def _keepalive_loop():
            # 起步即触发：第一次 ping 顺手 warmup /mcp/，让 streamable-http
            # 的路由/session-manager 完全加载，避免 boot 后第一个客户端请求
            # 撞上"路径已注册但路由未就绪"的 404 窗口。
            warmed = False
            async with httpx.AsyncClient() as client:
                while True:
                    if not warmed and transport == "streamable-http":
                        try:
                            await client.get(f"http://localhost:{port}/mcp/", timeout=3)
                        except Exception:
                            pass
                        warmed = True
                    try:
                        await client.get(f"http://localhost:{port}/health", timeout=5)
                        if logger:
                            logger.debug("Night Fall keepalive ping OK")
                    except Exception as exc:
                        if logger:
                            logger.warning(f"Night Fall keepalive ping failed: {exc}")
                    await asyncio.sleep(60)

        def _start_keepalive():
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_keepalive_loop())

        threading.Thread(target=_start_keepalive, daemon=True).start()
        if transport == "streamable-http":
            app = ombre_server.mcp.streamable_http_app()
        else:
            app = ombre_server.mcp.sse_app()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

        # FastMCP 的 streamable-http endpoint 挂在 /mcp/（带尾斜杠）。
        # 部分客户端发 /mcp（无斜杠），正常情况返回 307 redirect 但有些客户端
        # 不跟随重定向；wake 瞬间还可能撞上路由未就绪的 404 窗口。
        # 透明改写 path，省一次 round-trip + 避开 wake race。
        if transport == "streamable-http":
            inner_app = app

            class _TrailingSlashMcpMiddleware:
                def __init__(self, asgi_app):
                    self._asgi = asgi_app

                async def __call__(self, scope, receive, send):
                    if scope["type"] == "http" and scope.get("path") == "/mcp":
                        scope = dict(scope)
                        scope["path"] = "/mcp/"
                        if scope.get("raw_path") == b"/mcp":
                            scope["raw_path"] = b"/mcp/"
                    await self._asgi(scope, receive, send)

            app = _TrailingSlashMcpMiddleware(inner_app)

        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        ombre_server.mcp.run(transport=transport)


def main() -> None:
    cfg = load_config(require_ombre=True)
    ombre_server = import_ombre_server(cfg.ombre_home)
    register_night_fall(ombre_server, cfg)
    run_ombre_server(ombre_server)


if __name__ == "__main__":
    main()
