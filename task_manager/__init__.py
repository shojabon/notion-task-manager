import json

from task_manager.notion_database.notion_task_database import NotionTaskDatabase
from task_manager.task_management.assign_daily_task import NotionAssignDailyTask


class TaskManager:

    def __init__(self):
        # load json config file
        with open("config.json", "r", encoding="utf-8") as f:
            self.config = json.loads(f.read())

        self.notion_task_database = NotionTaskDatabase(self)
        self.notion_assign_daily_task = NotionAssignDailyTask(self)
