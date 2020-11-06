import functools
from datetime import date, timedelta, datetime
import json
from re import A
import sched

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)

from notscrum.db import get_db

statuses = ['To-Do','In Progress','Done'] #list(set([x['status'] for x in tasks]))
bp = Blueprint('sprint', __name__, url_prefix='/sprint')


def get_sprint_details(sprint_id):
    """Get all tasks, stories, and epics associated with a given sprint"""
    db = get_db()
    stories = db.execute(
        'SELECT DISTINCT story.id, epicID, story, story.deadline, prioritization FROM story '+
        'JOIN task on task.storyID = story.id '+
        'WHERE (task.sprintID = ? or task.recurring)'+
        'ORDER BY prioritization DESC',
        (sprint_id,)
    ).fetchall()
    epics = db.execute(
        'SELECT DISTINCT epic.id, epic, color, epic.deadline FROM epic '+
        'JOIN story ON story.epicID = epic.id '+
        'JOIN task on task.storyID = story.id '+
        'WHERE (task.sprintID = ? OR task.recurring)',
        (sprint_id,)
    ).fetchall()
    tasks = db.execute(
        'SELECT task.id, task, estimate, status, storyID, '+
        'epicID, actual, task.deadline, task.recurring, coalesce(hours_worked,0) hours_worked, ' +
        'coalesce(sum_sched,0) sum_sched ' +
        'FROM task ' +
        'JOIN story ON task.storyID = story.id ' +
        'LEFT OUTER JOIN (SELECT taskid, sum(hours_worked) hours_worked '+
                        'from work group by taskid) woik '+
        'ON woik.taskID = task.id '+
        'LEFT OUTER JOIN (select taskid, sprintid, count(1) * 2 sum_sched '+
                        'FROM schedule_task group by taskid, sprintid) sched '+
        'ON task.id = sched.taskid AND task.sprintid = sched.sprintid ' + 
        'WHERE task.sprintID = ? or task.recurring',
        (sprint_id,)
    ).fetchall()
    sprint_days = db.execute(
        'SELECT startDate, endDate from sprint where id = ?',
        (sprint_id,)
    ).fetchone()
    # FIXME: Window functionS? You've got ot be kidding me.
    schedule_records = db.execute(
        "select DISTINCT first_value(id) OVER (PARTITION BY part ORDER BY sched_heirarch RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as id, "+ 
        "first_value(taskid)  OVER (PARTITION BY part ORDER BY sched_heirarch RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)as taskid, " + 
        'sprint_day, sprint_hour, '+
        "first_value(coalesce(note,'')) OVER (PARTITION BY part ORDER BY sched_heirarch RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as note, "+ 
        "first_value(recurring_schedule) OVER (PARTITION BY part ORDER BY sched_heirarch RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as recurring_schedule "+ 
        "FROM (SELECT *, false as recurring_schedule, 0 as sched_heirarch, sprint_day ||'T'|| sprint_hour as part from schedule_task WHERE sprintid = ? "+
        'UNION ALL '+
        "SELECT *, true as recurring_schedule, 0 as sched_heirarch, sprint_day ||'T'|| sprint_hour as part FROM schedule_task WHERE sprintid = 0) schedrecs " +
        "ORDER BY sched_heirarch", 
        (sprint_id,)
    ).fetchall()
    current_day = sprint_days['startDate']
    i = 0;
    schedule = []
    while current_day <= sprint_days['endDate']:
        schedule.append((i,current_day,range(9,22,2)))
        i+=1
        current_day += timedelta(1)
    return stories, epics, tasks, schedule, schedule_records


def get_sprint_board(sprint_id, sprint, isStatic=False):
    stories, epics, tasks, schedule, schedule_records = get_sprint_details(sprint_id)
    tasks = dict([(x['id'],dict(x)) for x in tasks])
    stories = dict([(x['id'],dict(x)) for x in stories])
    epics = dict([(x['id'],dict(x)) for x in epics])
    # Get Estimate Totals by story/epic at each status level
    totals = {}
    # sum up totals btw I don't like how this is implemented
    # this will appear in your next annual review >:-(
    for task in tasks.values():
        estimate = task['estimate']
        estimate = 0 if estimate is None else estimate
        story_id = task['storyID']
        epic_id = task['epicID']
        status = task['status']
        cuts = [status, f'e{epic_id}', f'e{epic_id}_{status}',f's{story_id}',f's{story_id}_{status}']
        for c in cuts:
            totals[c] = totals.get(c,0)+estimate
    return render_template('sprint/board.html',
                            sprint = sprint,
                            sprint_id = sprint_id,
                            stories = stories,
                            epics = epics,
                            tasks = tasks,
                            totals = totals,
                            statuses = statuses,
                            static = isStatic,
                            schedule = schedule,
                            schedule_records = schedule_records)


@bp.route('/schedule/<int:sprint_id>',methods=('GET','POST','DELETE'))
def schedule(sprint_id):
    """
    Get or set scheduling information for a given sprint.
    """
    db = get_db()
    is_json = request.args.get('is_json',False)
    if request.method == 'POST':
        schedule = db.execute(
            'SELECT * FROM schedule_task WHERE sprintid = ?',
            (sprint_id,)
        ).fetchall()
        sprint = db.execute(
            'SELECT startDate, endDate from sprint where id = ?',
                (sprint_id,)
        ).fetchone()
        sprint_days = (sprint['endDate']-sprint['startDate']).days
        task_id = request.form.get('task_id',None)
        sprint_day = request.form.get('sprint_day',None)
        sprint_hour = request.form.get('sprint_hour',None)
        schedule_id = request.form.get('schedule_id',None)
        note = request.form.get('note')
        if request.form.get('recurring',0) == 1 :
            # TODO: Validate that task is actually recurring
            sprint_id = 0;
        error = None
        if task_id is None:
            error = f'No Task ID Found in Request'
        elif sprint_day is None:
            error = f'No Sprint Day Found in Request'
        elif sprint_hour is None:
            error = f'No Sprint Hour Found in Request'
        elif datetime.strptime(sprint_day,'%Y-%m-%d').date() > sprint['endDate']:
            error = f'Scheduled day is after sprint end'
        elif int(sprint_hour) > 24:
            error = f'Sprint Hour is > 24'
        if error is None:
            old_record =  db.execute(
                'SELECT id FROM schedule_task WHERE sprintid = ? AND sprint_day = ? AND sprint_hour = ? AND (? is NULL or id != ?)',
                (sprint_id,sprint_day,sprint_hour,schedule_id,schedule_id)
            ).fetchone() 
            if old_record is not None:
                db.execute(
                    'DELETE FROM schedule_task WHERE id = ?',
                    (old_record['id'],)
                )
                #error = f'Day {sprint_day} at {sprint_hour} is already scheduled. Delete the existing task before scheduling another'
            if schedule_id is None:
                db.execute(
                    'INSERT INTO schedule_task (sprintid, taskid, sprint_day, sprint_hour, note) '+
                    'VALUES (?, ?, ?, ?, ?)',
                    (sprint_id, task_id, sprint_day, sprint_hour, note)
                )
            else:
                db.execute(
                    'UPDATE schedule_task SET taskid = ?, sprint_day = ?, '+
                    'sprint_hour = ?, note = ? WHERE id = ?',
                    (task_id, sprint_day, sprint_hour, note, schedule_id)
                )
            db.commit()
            schedule_task = db.execute(
                'SELECT * FROM schedule_task WHERE (sprintid IN (?,0)) AND '+
                'sprint_day = ? and sprint_hour = ?',
                (sprint_id, sprint_day, sprint_hour)
            ).fetchone()
            print('Adding schedule for ',task_id,'on',sprint_day,sprint_hour)
            if is_json:
                schedule_task = dict(zip(schedule_task.keys(), schedule_task))
                for key,value in schedule_task.items():
                    if isinstance(value,date):
                        schedule_task[key] = str(value)
                return json.dumps({'Success':True,'schedule_task':schedule_task})
            return redirect(url_for('sprint.show',sprint_id=sprint_id))
        else:
            if is_json:
                abort(500,error)
            flash(error,'error')
    elif request.method == 'DELETE':
        print(f'{request.method} and {request.method == "DELETE"}')
        schedule_id = request.form.get('schedule_id',None)
        if request.form.get('recurring',0) == 1:
            sprint_id = 0;
        error = None
        if schedule_id is None:
            error = f'No Schedule ID Requested to Delete'
        if error is None: 
            schedule = db.execute(
                'SELECT id,taskid FROM schedule_task WHERE id = ?',
                (schedule_id,)
            ).fetchone()
            db.execute(
                'DELETE FROM schedule_task WHERE id = ? AND sprintid = ?',
                (schedule_id,sprint_id)
            )
            db.commit()
            if is_json:
                return json.dumps({'Success':True,'task_id':schedule['taskid'],'schedule_id':schedule['id']})
            return f'Schedule {schedule_id} deleted.'
        abort(500,error)
    elif is_json and request.method == 'GET':
        task_id = request.args.get('task_id',None)
        sprint_day = request.args.get('sprint_day',None)
        sprint_hour = request.args.get('sprint_hour',None)
        crit = 'sprintid = ? '
        crit_val = [sprint_id]
        if task_id is not None:
            crit += 'AND taskid = ? '
            crit_val.append(task_id)
        if sprint_day is not None:
            crit += 'AND sprint_day = ? '
            crit_val.append(sprint_day)
        if sprint_hour is not None:
            crit += 'AND sprint_hour = ? '
            crit_val.append(sprint_hour)
        schedule_tasks = db.execute(
            'SELECT * FROM schedule_task WHERE ' + crit,
            crit_val
        ).fetchall()
        if len(schedule_tasks) == 0:
            #NOTE: This section is only run if is_json is true
            return abort(404, 'No Schedules Found')
        keys = schedule_tasks[0].keys()
        schedule_tasks_out = []
        for task in schedule_tasks:
            schedule_tasks_out.append(dict(zip(keys,[str(task[k]) if isinstance(task[k],date) else task[k] for k in keys])))
        return json.dumps({'Success':True,'schedule_tasks':schedule_tasks_out})
    return redirect(url_for('sprint.show',sprint_id=sprint_id))


@bp.route('/create/next', methods=('POST',))
def create_next():
    "Create next sprint (currently assuming 7 day sprints)"
    #TODO: Get user sprint length & start day
    db = get_db()
    is_json = request.args.get('is_json',False)
    if is_json:
        abort(405,'Method not supported for AJAX mode')
    if request.method == 'POST':
        error = None
        last_sprint = db.execute(
            'SELECT * FROM sprint ORDER BY endDate DESC limit 1'
        ).fetchone()
        if last_sprint is None:
            error = f'No sprint found for user. Next sprint can only be created after initial sprint'
        if error is None:
            start_date, end_date = (last_sprint['endDate']+timedelta(1), last_sprint['endDate']+timedelta(8))
            db.execute(
                'INSERT INTO sprint (startDate, endDate) values (?,?)',
                (start_date, end_date)
            )
            db.commit()
            sprint = db.execute(
                'SELECT id FROM sprint WHERE startDate = ? and endDate = ?',
                (start_date, end_date)
            ).fetchone()
            if is_json:
                return json.dumps({'Success':True,'sprint_id':sprint['id']})
            return redirect(url_for('sprint.show',sprint_id = sprint['id']))
        if is_json:
            abort(500,error)
        flash(error,'error')
    final_sprint = db.execute(
        'SELECT id, startDate, endDate FROM sprint WHERE endDate = (SELECT max(endDate) FROM sprint)'
    ).fetchone()
    start_date = date.today() if final_sprint is None else final_sprint['endDate']
    end_date = start_date + timedelta(7)
    return render_template('sprint/create.html', start_date = start_date, end_date = end_date)


@bp.route('/create', methods=('GET','POST'))
def create():
    "Create a New Sprint (should default to week following last sprint)"
    db = get_db()
    is_json = request.args.get('is_json',False)
    if is_json and request.method == 'GET':
        abort(405,'Method not supported for AJAX mode')
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        force_create = request.form.get('force_create',None)
        error = None
        start_sprint = db.execute(
            'SELECT * FROM sprint WHERE startDate = ?',
            (start_date, )
        ).fetchone() 
        end_sprint = db.execute(
            'SELECT * FROM sprint WHERE endDate = ?',
            (end_date, )
        ).fetchone()
        if not start_date:
            error = "Unable to create sprint without a Start Date"
        elif not end_date:
            error = "Unable to create sprint without an End Date"
        elif end_sprint is not None:
            error = f"Sprint Ends same day as Existing Sprint {end_sprint['id']}"
        elif start_sprint is not None: 
            error = f"Sprint Starts same day as Existing Sprint {start_sprint['id']}"
        elif force_create is False and db.execute(
            'SELECT * FROM sprint WHERE (startDate between ? and ? OR endDate between ? and ?) AND startDate <> ? AND endDate <> ?',
            (start_date, end_date, start_date, end_date, end_date, start_date)
        ).fetchone() is not None:
            error = "Sprint overlaps existing Sprint"
        
        if error is None:
            db.execute(
                'INSERT INTO sprint (startDate, endDate) VALUES (?,?)',
                (start_date, end_date)
            )
            db.commit()
            sprint = db.execute(
                'SELECT id FROM sprint where startDate = ? AND endDate = ?',
                (start_date, end_date)
            ).fetchone()
            if is_json:
                return json.dumps({'Success':True,'sprint_id':sprint['id']})
            return redirect(url_for('sprint.show', sprint_id = sprint['id']))
        if is_json:
            abort(500,error)
        flash(error,'error')
    final_sprint = db.execute(
        'SELECT id, startDate, endDate FROM sprint WHERE endDate = (SELECT max(endDate) FROM sprint)'
    ).fetchone()
    if not start_date or start_date is None:
        start_date = date.today() if final_sprint is None else final_sprint['endDate']
    if not end_date:
        end_date = start_date + timedelta(7)
    return render_template('sprint/create.html', start_date = start_date, end_date = end_date)


@bp.route('/', methods=('GET',))
def list_all():
    "List all Sprints"
    db = get_db()
    is_json = request.args.get('is_json',False)
    sprints = db.execute(
        'SELECT sprint.id, startDate, endDate, '+
        'COUNT(DISTINCT story.id) as stories, COUNT(DISTINCT task.id) as tasks, '+
        'COUNT(DISTINCT epic.id) as epics, sum(task.estimate) total_estimate '+
        'FROM sprint '+
        'LEFT OUTER JOIN task ON task.sprintid = sprint.id '+
        'LEFT OUTER JOIN story ON story.id = task.storyID '+
        'LEFT OUTER JOIN epic ON epic.id = story.epicID '+
        'GROUP BY sprint.id, startDate, endDate ' + 
        'ORDER BY startDate DESC'
    ).fetchall()
    current_sprint = db.execute(
        'SELECT sprint.id FROM sprint WHERE current_date between startDate and endDate'
    ).fetchone()
    if not sprints:
        abort(404, "No Sprints Exist Yet: Create your First Sprint " + 
                    url_for('sprint.create'))
    if is_json:
        return json.dumps({'Success':True,
                           'sprints':[dict(x) for x in sprints],
                           'has_current_sprint':current_sprint is not None}) 
    return render_template('sprint/list.html',sprints = sprints)


@bp.route('/<int:sprint_id>', methods=('GET', 'POST'))
def show(sprint_id):
    "Show the Details of Sprint sprint_id"
    db = get_db()
    is_json = request.args.get('is_json',False)
    sprint = db.execute(
        'SELECT id, startDate, endDate FROM sprint WHERE id = ?',
        (sprint_id,)
    ).fetchone()
    if not sprint:
        abort(404, f"Sprint with ID {sprint_id} was not found.")
    if request.method == 'POST':
        start_date = request.form.get('start_date',None)
        end_date = request.form.get('end_date',None)
        error = None
        start_sprint = db.execute(
            'SELECT * FROM sprint WHERE startDate = ?',
            (start_date, )
        ).fetchone() 
        end_sprint = db.execute(
            'SELECT * FROM sprint WHERE endDate = ?',
            (end_date, )
        ).fetchone()
        if not start_date:
            error = "Sprint Requires Start date"
        elif not end_date:
            error = "Sprint Requires End Date"
        elif start_sprint is not None:
            error = f"New start date is shared by sprint {start_sprint['id']}"
        elif end_sprint is not None:
            error = f"New end date is shared by sprint {end_sprint['id']}"
        if error is None:
            db.execute(
                'UPDATE sprint SET '+
                'start_date = ?, end_date = ? '+
                'WHERE id = ?',
                (start_date, end_date, id)
            )
            db.commit()
            if is_json:
                return json.dumps({'Success':True,'sprint_id':sprint_id})
            return redirect(url_for('sprint.list_all', sprint_id = sprint_id))
        if is_json:
            abort(500,error)
        flash(error,'error')
    if is_json:
        return json.dumps({'Success':True,'sprint_id':sprint_id,'sprint':dict(sprint)})
    return get_sprint_board(sprint_id, sprint, isStatic=True)


@bp.route('/active', methods=('GET',))
def active():
    "See the Active Sprint - if two sprints overlap, pick the one with the higher endDate"
    db = get_db()
    is_json = request.args.get('is_json',False)
    current_sprint = db.execute(
        'SELECT id, startDate, endDate FROM sprint WHERE CURRENT_DATE between startDate and endDate '+
        'ORDER BY endDate DESC'
    ).fetchone()
    if not current_sprint:
        return redirect(url_for('sprint.list_all'))

    sprint_id = current_sprint['id']    
    if is_json:
         return json.dumps({'Success':True,'sprint_id':sprint_id,'sprint':dict(current_sprint)})
    return get_sprint_board(sprint_id, current_sprint, isStatic=False)