from __future__ import annotations

import datetime
import json
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from task_manager import TaskManager

from notion_client import Client


class NotionTaskDatabase:

    def __init__(self, main: TaskManager):
        self.main = main

    def save_database(self):
        notion = Client(auth=self.main.config["notion"]["api_key"])
        # query database. The function only returns 100 results, so if the full_database is true, we need to query multiple times
        final_data = []
        date_pointer = datetime.datetime.now() + datetime.timedelta(days=7)
        for x in range(10):
            data = notion.databases.query(
                database_id=self.main.config["notion"]["task_database_id"],
                filter={
                    "and": [
                        {
                            "property": "ステータス",
                            "status": {
                                "equals": "未完了"
                            }
                        },
                        {
                            "property": "作成日時",
                            "date": {
                                "before": date_pointer.strftime("%Y-%m-%d")
                            }
                        }
                    ]
                }
            )
            if len(data["results"]) == 0:
                break
            final_data.extend(data["results"])
            # get last data's created time and set it as the pointer
            date_pointer = datetime.datetime.strptime(data["results"][-1]["created_time"], "%Y-%m-%dT%H:%M:%S.%f%z")

        # save json data to file
        with open("data/notion_task_database.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(final_data, ensure_ascii=False))
        return True

    def load_database(self, formatted: bool=True):
        with open("data/notion_task_database.json", "r", encoding="utf-8") as f:
            data = json.loads(f.read())
        if not formatted:
            return data

        # format json into simpler format
        tasks = {}

        for task in data:
            date = task["properties"]["日付"]

            start = date["date"]["start"] if date["date"] is not None else None
            end = date["date"]["end"] if date["date"] is not None else None

            if start is not None and len(start) == 10: start += "T00:00:00.000+09:00"
            if end is not None and len(end) == 10: end += "T00:00:00.000+09:00"

            if start is not None: start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.%f%z")
            if end is not None: end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S.%f%z")
            task_data = {
                "id": task["id"],
                "name": [x["text"]["content"] for x in task["properties"]["名前"]["title"]],
                "start": start,
                "end": end,
                "depth": 0,
                "status": str(task["properties"]["ステータス"]["status"]["name"]),
                "childrenTasks": [x["id"] for x in task["properties"]["完了必須タスク"]["relation"]],
                "parentTasks": [x["id"] for x in task["properties"]["親タスク"]["relation"]]
            }
            if len(task_data["name"]) == 0:
                continue
            task_data["name"] = task_data["name"][0]
            tasks[task["id"]] = task_data

        def add_depth_to_all_linked_tasks(task):
            task["depth"] += 1
            for parent_task_id in task["parentTasks"]:
                if parent_task_id not in tasks:
                    continue
                add_depth_to_all_linked_tasks(tasks[parent_task_id])

        # calculate depth
        for task_id in tasks:
            add_depth_to_all_linked_tasks(tasks[task_id])

        # assign project id
        def add_project_id_to_all_linked_tasks(task, project_id):
            task["project_id"] = project_id
            for child_task_id in task["parentTasks"]:
                if child_task_id not in tasks:
                    continue
                add_project_id_to_all_linked_tasks(tasks[child_task_id], project_id)

        for task_id in tasks:
            if tasks[task_id]["depth"] != 1:
                continue
            project_id = str(uuid.uuid4())
            add_project_id_to_all_linked_tasks(tasks[task_id], project_id)

        tasks = sorted(tasks.values(), key=lambda x: (x["end"] is None, x["end"], x["depth"]))
        # convert to dictionary
        tasks = {x["id"]: x for x in tasks}
        return tasks
