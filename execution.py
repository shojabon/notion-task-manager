from task_manager import TaskManager

if __name__ == '__main__':
    task = TaskManager()
    print(task.notion_task_database.save_database())
    tasks = task.notion_assign_daily_task.assign_daily_tasks()
    task.notion_assign_daily_task.apply_assigned_tasks(tasks)