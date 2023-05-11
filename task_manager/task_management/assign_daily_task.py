from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from task_manager import TaskManager
from notion_client import Client


class NotionAssignDailyTask:

    def __init__(self, main: TaskManager):
        self.main = main

    def assign_daily_tasks(self) -> list[dict]:
        tasks = self.main.notion_task_database.load_database()
        # only get tasks that are not completed
        tasks = {k: v for k, v in tasks.items() if v["status"] == "未完了"}

        # calculate daily tasks
        daily_tasks = 0
        free_hours_per_day_definition = 3
        time_buffer = 1
        project_max_depth = {}
        last_task_in_project = {}
        minimum_max_depth = 2

        # initialize project max depth
        for task in tasks.values():
            project_max_depth[task["project_id"]] = 0

        for task in tasks.values():
            if task["start"] is not None and task["end"] is not None:
                # if task does not start even adding 24 hours, skip
                if task["start"] > datetime.datetime.now().astimezone(
                        datetime.timezone(datetime.timedelta(hours=9))) + datetime.timedelta(days=1):
                    continue

                seconds_elapsed = (
                        datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=9))) - task[
                    "start"]).total_seconds()
                # add 24 hours
                seconds_elapsed += 24 * 60 * 60
                if seconds_elapsed < 0:
                    seconds_elapsed = 0
                task_duration = (task["end"] - task["start"]).total_seconds()
                task_duration *= time_buffer
                if task_duration < 1:
                    task_duration = 1
                task_urgency_score = seconds_elapsed / task_duration

                if task_urgency_score > 1:
                    task_urgency_score = 1
                project_id = task["project_id"]
                if project_id not in last_task_in_project:
                    last_task_in_project[project_id] = task
                if last_task_in_project[project_id]["depth"] < task["depth"]:
                    last_task_in_project[project_id] = task
                daily_tasks += task_urgency_score
            else:
                daily_tasks += 0

        # adjust project max depth so that there would be at least minimum_max_depth
        for project_id in last_task_in_project.keys():
            project_max_depth[project_id] = minimum_max_depth
            task = last_task_in_project[project_id]
            current_time = datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=9)))
            time_remaining_until_last_task = (task["end"] - current_time).total_seconds()
            # remove 24 hours
            time_remaining_until_last_task -= 24 * 60 * 60
            if time_remaining_until_last_task < 1:
                time_remaining_until_last_task = 1
            time_remaining_until_last_task /= (24 * 60 * 60)
            if time_remaining_until_last_task < 1:
                time_remaining_until_last_task = 1

            depth_score = round(task["depth"] / (time_remaining_until_last_task * time_buffer))
            if depth_score < minimum_max_depth:
                depth_score = minimum_max_depth
            project_max_depth[project_id] = depth_score

        minimum_tasks_per_day = 3
        if daily_tasks < minimum_tasks_per_day:
            daily_tasks = minimum_tasks_per_day

        daily_tasks = round(daily_tasks)

        assigned_tasks = []

        for task in tasks.values():
            if task["start"] is not None and task["start"] > datetime.datetime.now().astimezone(
                    datetime.timezone(datetime.timedelta(hours=9))) + datetime.timedelta(days=1):
                continue
            if task["depth"] > project_max_depth[task["project_id"]]:
                continue
            assigned_tasks.append(task)
            if len(assigned_tasks) >= daily_tasks:
                break
        for task in assigned_tasks:
            print(task["name"])

        return assigned_tasks

    def apply_assigned_tasks(self, assigned_tasks: list[dict]):
        notion = Client(auth=self.main.config["notion"]["api_key"])
        assign_data = notion.databases.query(
            database_id=self.main.config["notion"]["task_database_id"],
            filter={
                "property": "アサイン内部",
                "checkbox": {
                    "equals": True
                }
            }
        )

        for task in assign_data["results"]:
            checkbox = task["properties"]["アサイン内部"]["checkbox"]
            if checkbox is False:
                continue
            notion.pages.update(page_id=task["id"], properties={"アサイン内部": {"checkbox": False}})

        # assign tasks

        for task in assigned_tasks:
            notion.pages.update(page_id=task["id"], properties={"アサイン内部": {"checkbox": True}})
