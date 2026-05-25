"""Workflow DAG executor."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict, deque
from typing import Any

from core.workflow.models import RetryPolicy, RunContext, WorkflowDefinition, WorkflowNode
from core.workflow.nodes import register_all_handlers
from core.workflow.registry import get_node_handler
from core.workflow.store import workflow_store

logger = logging.getLogger(__name__)

_handlers_registered = False


def _ensure_handlers() -> None:
    global _handlers_registered
    if not _handlers_registered:
        register_all_handlers()
        _handlers_registered = True


class WorkflowExecutor:
    """Execute workflow definitions as a directed acyclic graph."""

    def __init__(self, store=None):
        self.store = store or workflow_store

    def _log(self, run_id: str, ctx: RunContext, node_id: str, event: str, detail: Any = None) -> None:
        """Append log entry and persist incrementally."""
        ctx.log(node_id, event, detail)
        self.store.update_run_logs(run_id, ctx.logs)

    async def run(
        self,
        workflow_id: str,
        trigger_payload: dict[str, Any] | None = None,
        user_id: str | None = None,
        existing_run_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute workflow by ID using BFS with condition branch routing."""
        _ensure_handlers()
        workflow = self.store.get_workflow(workflow_id)
        if not workflow:
            return {"success": False, "error": f"Workflow '{workflow_id}' not found"}

        definition = WorkflowDefinition.from_dict(workflow["definition"])
        if existing_run_id:
            run = {"id": existing_run_id, "workflow_id": workflow_id, "status": "running"}
        else:
            run = self.store.create_run(workflow_id)
        from core.workflow.state import load_state, save_state

        persisted_state = load_state(workflow_id)
        ctx = RunContext(
            run_id=run["id"],
            workflow_id=workflow_id,
            user_id=user_id or workflow.get("owner_id"),
            trigger_payload=trigger_payload or {},
            state=dict(persisted_state),
        )

        try:
            if _has_cycle(definition):
                raise ValueError("Workflow contains a cycle")

            entry_nodes = self._entry_nodes(definition)
            if not entry_nodes:
                entry_nodes = [definition.nodes[0].id] if definition.nodes else []

            queue: deque[str] = deque(entry_nodes)
            executed: set[str] = set()
            last_output: dict[str, Any] = {}

            while queue:
                node_id = queue.popleft()
                if node_id in executed:
                    continue

                node = next((n for n in definition.nodes if n.id == node_id), None)
                if not node:
                    continue

                if not self._should_execute_node(node_id, definition, ctx, executed):
                    self._log(run["id"], ctx, node_id, "skipped", "condition branch not taken")
                    executed.add(node_id)
                    continue

                handler = get_node_handler(node.type)
                if not handler:
                    self._log(run["id"], ctx, node_id, "skipped", f"No handler for {node.type}")
                    executed.add(node_id)
                    continue

                self._log(run["id"], ctx, node_id, "started", node.type)
                policy = node.retry
                output, error = await self._run_with_retry(handler, ctx, node, policy, run["id"])
                if error is not None:
                    error_edges = [
                        e for e in definition.edges
                        if e.from_node == node_id and (e.label or "").lower() == "error"
                    ]
                    if error_edges or node.continue_on_error:
                        ctx.node_outputs[node_id] = {"output": "", "success": False, "error": error}
                        self._log(run["id"], ctx, node_id, "error", error)
                        executed.add(node_id)
                        for edge in error_edges:
                            if edge.to_node not in executed:
                                queue.append(edge.to_node)
                        if not error_edges:
                            for edge in self._outgoing_edges(node, definition, ctx):
                                if edge.to_node not in executed:
                                    queue.append(edge.to_node)
                        continue
                    self._log(run["id"], ctx, node_id, "error", error)
                    self.store.finish_run(run["id"], "failed", ctx.logs)
                    return {
                        "success": False,
                        "run_id": run["id"],
                        "error": error,
                        "logs": ctx.logs,
                    }

                if (
                    isinstance(output, dict)
                    and output.get("success") is False
                    and node.type.startswith("action.")
                    and not node.continue_on_error
                ):
                    error_msg = str(
                        output.get("error")
                        or (
                            output.get("output", {}).get("error")
                            if isinstance(output.get("output"), dict)
                            else None
                        )
                        or "Action returned success=false"
                    )
                    error_edges = [
                        e for e in definition.edges
                        if e.from_node == node_id and (e.label or "").lower() == "error"
                    ]
                    if error_edges:
                        ctx.node_outputs[node_id] = output
                        self._log(run["id"], ctx, node_id, "error", error_msg)
                        executed.add(node_id)
                        for edge in error_edges:
                            if edge.to_node not in executed:
                                queue.append(edge.to_node)
                        continue
                    self._log(run["id"], ctx, node_id, "error", error_msg)
                    self.store.finish_run(run["id"], "failed", ctx.logs)
                    return {
                        "success": False,
                        "run_id": run["id"],
                        "error": error_msg,
                        "logs": ctx.logs,
                    }

                ctx.node_outputs[node_id] = output
                last_output = output
                self._log(run["id"], ctx, node_id, "completed", output)
                executed.add(node_id)
                for edge in self._outgoing_edges(node, definition, ctx):
                    if (edge.label or "").lower() == "error":
                        continue
                    if edge.to_node not in executed:
                        queue.append(edge.to_node)

            self.store.finish_run(run["id"], "success", ctx.logs)
            save_state(workflow_id, ctx.state)
            ws_id = workflow.get("workspace_id")
            if ws_id:
                from core.usage.tracker import usage_tracker
                usage_tracker.track(
                    "workflow_run",
                    team_id=ws_id,
                    user_id=user_id or workflow.get("owner_id"),
                    metadata={"workflow_id": workflow_id, "run_id": run["id"]},
                )
            return {
                "success": True,
                "run_id": run["id"],
                "output": last_output,
                "logs": ctx.logs,
            }
        except ValueError as exc:
            self.store.finish_run(run["id"], "failed", ctx.logs + [{"event": "error", "detail": str(exc)}])
            return {"success": False, "run_id": run["id"], "error": str(exc)}

    async def start_background(
        self,
        workflow_id: str,
        trigger_payload: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Enqueue workflow execution; return run_id without blocking the HTTP worker."""
        workflow = self.store.get_workflow(workflow_id)
        if not workflow:
            return {"success": False, "error": f"Workflow '{workflow_id}' not found"}
        run = self.store.create_run(workflow_id)
        run_id = run["id"]

        async def _execute() -> None:
            try:
                await self.run(
                    workflow_id,
                    trigger_payload=trigger_payload,
                    user_id=user_id,
                    existing_run_id=run_id,
                )
            except Exception as exc:
                logger.exception("Background workflow %s failed: %s", workflow_id, exc)
                self.store.finish_run(
                    run_id,
                    "failed",
                    [{"node_id": "", "event": "error", "detail": str(exc)}],
                )

        asyncio.create_task(_execute())
        return {
            "success": True,
            "run_id": run_id,
            "status": "running",
            "background": True,
        }

    async def _run_with_retry(
        self,
        handler,
        ctx: RunContext,
        node: WorkflowNode,
        policy: RetryPolicy,
        run_id: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Execute handler with retry policy. Returns ``(output, error)``.

        Trade-off: retries are sequential (sleep between attempts). For workflows
        with many parallel nodes, this is acceptable because each node is
        independent; concurrency is not the main bottleneck.
        """
        attempt = 0
        last_error: str | None = None
        while attempt < policy.max_attempts:
            attempt += 1
            try:
                output = await handler(ctx, node.config)
                if attempt > 1:
                    self._log(run_id, ctx, node.id, "retry_success", {"attempt": attempt})
                return output, None
            except Exception as exc:  # noqa: BLE001 — handlers raise diverse types
                last_error = str(exc)
                logger.warning(
                    "Node %s failed (attempt %s/%s): %s",
                    node.id,
                    attempt,
                    policy.max_attempts,
                    exc,
                )
                if attempt < policy.max_attempts:
                    self._log(run_id, ctx, node.id, "retry", {"attempt": attempt, "error": last_error})
                    await asyncio.sleep(policy.backoff_seconds * attempt)
        return None, last_error

    def _entry_nodes(self, definition: WorkflowDefinition) -> list[str]:
        """Nodes with no incoming edges."""
        has_incoming = {e.to_node for e in definition.edges}
        return [n.id for n in definition.nodes if n.id not in has_incoming]

    def _should_execute_node(
        self,
        node_id: str,
        definition: WorkflowDefinition,
        ctx: RunContext,
        executed: set[str],
    ) -> bool:
        """Check if all incoming condition/error edges allow execution.

        Returns True if at least one incoming edge resolves to "this node should run".
        For nodes connected only by error edges, we run them only when the parent
        actually errored.
        """
        incoming = [e for e in definition.edges if e.to_node == node_id]
        if not incoming:
            return True

        only_error_edges = all((e.label or "").lower() == "error" for e in incoming)
        if only_error_edges:
            for edge in incoming:
                parent_out = ctx.node_outputs.get(edge.from_node) or {}
                if edge.from_node in executed and parent_out.get("success") is False:
                    return True
            return False

        for edge in incoming:
            if (edge.label or "").lower() == "error":
                continue
            parent_out = ctx.node_outputs.get(edge.from_node)
            if parent_out is None and edge.from_node not in executed:
                return False
            parent_node = next((n for n in definition.nodes if n.id == edge.from_node), None)
            if parent_node and parent_node.type == "condition" and edge.label:
                branch = (parent_out or {}).get("branch", "true")
                if edge.label != branch:
                    return False
        return True

    def _outgoing_edges(
        self, node: WorkflowNode, definition: WorkflowDefinition, ctx: RunContext
    ) -> list:
        """Get outgoing edges, filtering condition branches."""
        edges = [e for e in definition.edges if e.from_node == node.id]
        if node.type == "condition":
            output = ctx.node_outputs.get(node.id, {})
            branch = output.get("branch", "true")
            return [e for e in edges if not e.label or e.label == branch]
        return edges

    def _topological_sort(self, definition: WorkflowDefinition) -> list[str]:
        """Return node execution order via Kahn's algorithm (for tests/validate)."""
        in_degree: dict[str, int] = defaultdict(int)
        adj: dict[str, list[str]] = defaultdict(list)
        nodes = {n.id for n in definition.nodes}
        for n in nodes:
            in_degree.setdefault(n, 0)
        for edge in definition.edges:
            if edge.from_node in nodes and edge.to_node in nodes:
                adj[edge.from_node].append(edge.to_node)
                in_degree[edge.to_node] += 1
        queue = deque([n for n in nodes if in_degree[n] == 0])
        order: list[str] = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(order) != len(nodes):
            raise ValueError("Workflow contains a cycle")
        return order

    async def sync_all_triggers(self, workflow_id: str) -> list[str]:
        """Unregister old jobs and re-register schedule + email triggers if active."""
        await self.unregister_all_triggers(workflow_id)
        wf = self.store.get_workflow(workflow_id)
        if wf and wf.get("status") == "active":
            schedule_jobs = await self.register_schedule_triggers(workflow_id)
            email_jobs = await self.register_email_triggers(workflow_id)
            return schedule_jobs + email_jobs
        return []

    async def sync_schedule_triggers(self, workflow_id: str) -> list[str]:
        """Backward-compatible alias for sync_all_triggers."""
        return await self.sync_all_triggers(workflow_id)

    async def unregister_all_triggers(self, workflow_id: str) -> None:
        """Remove all scheduler jobs for a workflow."""
        from core.scheduler_manager import scheduler_manager

        wf = self.store.get_workflow(workflow_id)
        if not wf:
            return
        definition = WorkflowDefinition.from_dict(wf["definition"])
        for node in definition.nodes:
            if node.type == "trigger.schedule":
                await scheduler_manager.remove_job(f"wf_{workflow_id}_{node.id}")
            elif node.type == "trigger.email":
                await scheduler_manager.remove_job(f"wf_email_{workflow_id}_{node.id}")

    async def unregister_schedule_triggers(self, workflow_id: str) -> None:
        """Backward-compatible alias."""
        await self.unregister_all_triggers(workflow_id)

    async def register_schedule_triggers(self, workflow_id: str) -> list[str]:
        """Register APScheduler jobs for schedule trigger nodes."""
        from core.scheduler_manager import scheduler_manager

        workflow = self.store.get_workflow(workflow_id)
        if not workflow:
            return []

        definition = WorkflowDefinition.from_dict(workflow["definition"])
        registered: list[str] = []

        for node in definition.nodes:
            if node.type != "trigger.schedule":
                continue
            cron = node.config.get("cron", "0 9 * * *")
            parts = cron.split()
            if len(parts) != 5:
                logger.warning("Invalid cron for node %s: %s", node.id, cron)
                continue
            job_id = f"wf_{workflow_id}_{node.id}"
            trigger_args = {
                "minute": parts[0],
                "hour": parts[1],
                "day": parts[2],
                "month": parts[3],
                "day_of_week": parts[4],
            }
            result = await scheduler_manager.add_workflow_job(job_id, workflow_id, trigger_args)
            if result.get("success"):
                registered.append(job_id)

        return registered

    async def register_email_triggers(self, workflow_id: str) -> list[str]:
        """Register interval poll jobs for email trigger nodes."""
        from core.scheduler_manager import scheduler_manager

        workflow = self.store.get_workflow(workflow_id)
        if not workflow:
            return []

        definition = WorkflowDefinition.from_dict(workflow["definition"])
        registered: list[str] = []

        for node in definition.nodes:
            if node.type != "trigger.email":
                continue
            minutes = int(node.config.get("poll_interval_minutes", 5))
            job_id = f"wf_email_{workflow_id}_{node.id}"
            result = await scheduler_manager.add_email_poll_job(
                job_id, workflow_id, node.id, minutes
            )
            if result.get("success"):
                registered.append(job_id)

        return registered


def _has_cycle(definition: WorkflowDefinition) -> bool:
    """Detect cycle in workflow graph."""
    try:
        WorkflowExecutor()._topological_sort(definition)
        return False
    except ValueError:
        return True


async def rehydrate_all_triggers(store=None) -> int:
    """Re-register all triggers for active workflows on startup."""
    store = store or workflow_store
    executor = WorkflowExecutor(store=store)
    count = 0
    for wf in store.list_active_workflows():
        jobs = await executor.sync_all_triggers(wf["id"])
        count += len(jobs)
    logger.info("Rehydrated %s trigger jobs for active workflows", count)
    return count


async def rehydrate_all_schedules(store=None) -> int:
    """Backward-compatible alias."""
    return await rehydrate_all_triggers(store)
