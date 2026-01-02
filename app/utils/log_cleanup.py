"""
定期日志清理任务
"""
import asyncio
from typing import Optional
from app.utils.logger import cleanup_old_logs, logger
from app.config import settings


class LogCleanupTask:
    """日志清理任务管理器"""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def _cleanup_worker(self):
        """定期清理日志的后台任务"""
        interval_seconds = settings.log_cleanup_interval_hours * 3600

        while self._running:
            try:
                if settings.log_cleanup_enabled:
                    logger.info("开始执行日志清理任务...")
                    cleanup_old_logs(max_size_mb=settings.log_cleanup_max_size_mb)

                # 等待下次执行
                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                logger.info("日志清理任务被取消")
                break
            except Exception as e:
                logger.error(f"日志清理任务执行出错: {e}")
                # 出错后等待1小时再重试
                await asyncio.sleep(3600)

    async def start(self):
        """启动日志清理任务"""
        if self._running:
            logger.warning("日志清理任务已在运行")
            return

        self._running = True
        self._task = asyncio.create_task(self._cleanup_worker())
        logger.info(f"日志清理任务已启动，执行间隔: {settings.log_cleanup_interval_hours}小时")

    async def stop(self):
        """停止日志清理任务"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("日志清理任务已停止")

    def is_running(self) -> bool:
        """检查任务是否运行中"""
        return self._running


# 全局任务实例
log_cleanup_task = LogCleanupTask()
