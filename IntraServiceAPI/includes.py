class BasicInlcude:
    priority = 'priority'
    service = 'service'
    status = 'status'
    user = 'user'


class TasksInclude(BasicInlcude):
    asset_ids = 'assetids'
    category_ids = 'categoryids'


class TaskInclude(BasicInlcude):
    task_type = 'tasktype'
    task_type_settings = 'tasktypesettings'
    user_task_rights = 'usertaskrights'