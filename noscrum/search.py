alltext = """select 'task' label,task value, task.id from task
 union all select 'story',story,story.id from story
 union all select 'epic',epic,epic.id from epic
 union all select 'note',note,sr.id from schedule_task sr"""

magic_search = f"SELECT * from {alltext} WHERE value LIKE '%?%'"