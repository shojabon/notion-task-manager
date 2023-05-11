from task_manager import TaskManager

task_manager = TaskManager()
task_manager.notion_task_database.save_database()
tasks = task_manager.notion_assign_daily_task.assign_daily_tasks()
quit()
task_manager.notion_assign_daily_task.apply_assigned_tasks(tasks)