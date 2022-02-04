import functools
from datetime import date, timedelta, datetime
import json
from re import A
import sched

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)
from flask_user import current_user, login_required

from noscrum.db import get_db, Sprint, Task, ScheduleTask
from noscrum.epic import get_epics
from noscrum.story import get_stories

statuses = ['To-Do','In Progress','Done'] 
bp = Blueprint('sprint', __name__, url_prefix='/sprint')

def get_sprints():
    db = get_db()
    return Sprint.query.filter(Sprint.user_id == current_user.id).all()

def get_sprint(id):
    db = get_db()
    return Sprint.query.filter(Sprint.id == id).filter(Sprint.user_id == current_user.id).first()

def get_sprint_by_date(start_date=None,end_date=None,middle_date=None):
    db = get_db()
    query = Sprint.query.filter(Sprint.start_date != '1969-12-31').filter(Sprint.user_id == current_user.id)
    filter_vars = []
    if start_date is not None:
        query.filter(Sprint.start_date == start_date)
        filter_vars.append(start_date)
    if end_date is not None:
        query.filter(Sprint.end_date == end_date)
        filter_vars.append(end_date)
    if middle_date is not None:
        query.filter(middle_date >= Sprint.start_date).filter(middle_date <= Sprint.end_date)
        filter_vars.append(middle_date)
    if len(filter_vars) == 0:
        raise Exception('No criteria entered for get_sprint_by_date')
    return query.first()

def get_current_sprint():
    date_string = datetime.now().strftime('%Y-%m-%d')
    return get_sprint_by_date(middle_date=date_string)

def get_last_sprint():
    return Sprint.query.filter(Sprint.user_id == current_user.id).order_by(Sprint.end_date).first()

def create_sprint(start_date,end_date):
    db = get_db()
    new_sprint = Sprint(start_date=start_date,
                        end_date=end_date,
                        user_id=current_user.id)
    db.session.add(new_sprint)
    db.session.commit()
    return get_sprint_by_date(start_date=start_date,end_date=end_date)

def update_sprint(id,start_date,end_date):
    db = get_db()
    Sprint.query.filter(Sprint.id == id)\
        .filter(Sprint.user_id == current_user.id)\
        .update({
            start_date:start_date,
            end_date:end_date},
            synchronize_session="fetch"
        )
    db.session.commit()
    return get_sprint(id)

def get_schedules_for_sprint(sprint_id):
    db = get_db()
    return ScheduleTask.query.filter(ScheduleTask.sprint_id == sprint_id).all()

def get_schedule_tasks_filtered(sprint_id,task_id,sprint_day,sprint_hour):
    db = get_db()
    query = ScheduleTask.query.filter(ScheduleTask.sprint_id == sprint_id)
    query.filter(ScheduleTask.user_id == current_user.id)
    if task_id is not None:
        query.filter(ScheduleTask.task_id == task_id)
    if sprint_day is not None:
        query.filter(ScheduleTask.sprint_day == sprint_day)
    if sprint_hour is not None:
        query.filter(ScheduleTask.sprint_hour == sprint_hour)
    return query.all()

def get_schedule(id):
    return ScheduleTask.query\
        .filter(ScheduleTask.id==id)\
        .filter(ScheduleTask.user_id==current_user.id).first()

def get_schedule_by_time(sprint_id,sprint_day,sprint_hour,schedule_id=None):
    db = get_db()
    query = ScheduleTask.query.filter(ScheduleTask.user_id==current_user.id)\
        .filter(ScheduleTask.sprint_day == sprint_day)\
        .filter(ScheduleTask.sprint_hour == sprint_hour)\
        .filter(ScheduleTask.sprint_id == sprint_id)
    if schedule_id is not None:
        query.filter(ScheduleTask.id != schedule_id)
    return query.first()
   

def create_schedule(sprint_id,task_id,sprint_day,sprint_hour,note):
    db = get_db()
    schedule = ScheduleTask(sprint_id = sprint_id,
        task_id = task_id,
        sprint_day = sprint_day,
        sprint_hour = sprint_hour,
        note = note,
        user_id = current_user.id)
    db.session.add(schedule)
    db.session.commit()
    return get_schedule_by_time(sprint_id,sprint_day,sprint_hour)
   

def update_schedule(id,task_id,sprint_day,sprint_hour,note):
    db = get_db()
    ScheduleTask.query.filter(ScheduleTask.user_id == current_user.id)\
        .filter(ScheduleTask.id == id).update({
            task_id:task_id,
            sprint_day:sprint_day,
            sprint_hour:sprint_hour,
            note:note},synchronize_session="fetch")
   

def delete_schedule(id):
    db = get_db()
    ScheduleTask.query.filter(ScheduleTask.id == id)\
            .filter(ScheduleTask.user_id == current_user.id)\
            .delete()
    db.session.commit()


def get_sprint_details(sprint_id):
    db = get_db()
    stories = get_stories(sprint_view=True,sprint_id=sprint_id)
    epics = get_epics(sprint_view=True,sprint_id=sprint_id)
    #tasks = #get_tasks().filter(Task.sprint_id == sprint_id)
    tasks = db.session.execute(
        'SELECT task.id, task, estimate, status, story_id, '+
        'epic_id, actual, task.deadline, task.recurring, coalesce(hours_worked,0) hours_worked, ' +
        'coalesce(sum_sched,0) sum_sched, ' +
        '(task.sprint_ID = sched.sprint_id) single_sprint_task '+
        'FROM task ' +
        'JOIN story ON task.story_id = story.id ' +
        'LEFT OUTER JOIN (SELECT task_id, sum(hours_worked) hours_worked '+
                        'FROM work group by task_id) woik '+
        'ON woik.task_id = task.id '+
        'LEFT OUTER JOIN (select task_id, sprint_id, count(1) * 2 sum_sched '+
                        'FROM schedule_task group by task_id, sprint_id) sched '+
        'ON task.id = sched.task_id AND sched.sprint_id = :sprint_id ' + 
        'WHERE task.user_id = :user_id '+
        'AND (task.sprint_ID = :sprint_id or task.recurring or '+
        'task.id in (select task_id from schedule_task where sprint_id = sprint_id))',
        {'sprint_id':sprint_id,'user_id':current_user.id}).fetchall()
    sprint_days = Sprint.query.filter(Sprint.id == sprint_id).filter(Sprint.user_id==current_user.id).first()
    schedule_records_std = ScheduleTask.query.filter(ScheduleTask.sprint_id == sprint_id).filter(ScheduleTask.user_id==current_user.id)
    schedule_records_recurring = ScheduleTask.query.join(Task).filter(Task.recurring == True).filter(ScheduleTask.user_id==current_user.id)
    schedule = dict([(f'{x.sprint_day}T{x.sprint_hour}:00',x) for x in schedule_records_recurring])
    for r in schedule_records_std:
        key = f'{r.sprint_day}T{r.sprint_hour}:00'
        schedule[key] = r
    schedule_records = list(schedule.values())

    current_day = sprint_days.start_date
    i = 0;
    schedule = []
    while current_day <= sprint_days.end_date:
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
        story_id = task['story_id']
        epic_id = task['epic_id']
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
@login_required
def schedule(sprint_id):
    """
    Get or set scheduling information for a given sprint.
    """
    is_json = request.args.get('is_json',False)
    # TODO: Change POST INSERT reqs to PUT? 
    if request.method == 'POST':
        schedule = get_schedules_for_sprint(sprint_id)
        sprint = get_sprint(sprint_id) 
        sprint_days = (sprint.end_date-sprint.start_date).days
        task_id = request.form.get('task_id',None)
        sprint_day = request.form.get('sprint_day',None)
        if isinstance(sprint_day,str):
            sprint_day = datetime.strptime(sprint_day,'%Y-%m-%d').date()
        sprint_hour = request.form.get('sprint_hour',None)
        schedule_id = request.form.get('schedule_id',None)
        note = request.form.get('note')
        recurring = request.form.get('recurring',0) 
        print(f'recurring value {recurring}')
        if recurring == '1' :
            # TODO: Validate that task is actually recurring
            sprint_id = 0;
        error = None
        if task_id is None:
            error = f'No Task ID Found in Request'
        elif sprint_day is None:
            error = f'No Sprint Day Found in Request'
        elif sprint_hour is None:
            error = f'No Sprint Hour Found in Request'
        elif sprint_day > sprint.end_date:
            error = f'Scheduled day is after sprint end'
        elif int(sprint_hour) > 24:
            error = f'Sprint Hour is > 24'
        if error is None:
            old_record = get_schedule_by_time(sprint_id,sprint_day,sprint_hour,schedule_id=schedule_id) 
            if old_record is not None:
                if old_record.id == schedule_id:
                    raise Exception("Old schedule flagged as duplicate")
                delete_schedule(old_record.id)
                schedule_id = None
                #error = f'Day {sprint_day} at {sprint_hour} is already scheduled. Delete the existing task before scheduling another'
            if schedule_id is None:
                schedule_task = create_schedule(sprint_id,task_id,sprint_day,sprint_hour,note)
            else:
                schedule_task = update_schedule(schedule_id,task_id,sprint_day,sprint_hour,note)
            
            print(f'Adding schedule for task {task_id} to sprint {sprint_id} on {sprint_day} {sprint_hour}:00')
            if is_json:
                #schedule_task = dict(zip(schedule_task.keys(), schedule_task))
                #for key,value in schedule_task.items():
                #    if isinstance(value,date):
                #        schedule_task[key] = str(value)
                return {'Success':True,'schedule_task':schedule_task.to_dict()}
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
            schedule = get_schedule(schedule_id)
            delete_schedule(schedule_id)
            if is_json:
                return json.dumps({'Success':True,'task_id':schedule.task_id,'schedule_id':schedule.id})
            return f'Schedule {schedule_id} deleted.'
        abort(500,error)
    elif is_json and request.method == 'GET':
        task_id = request.args.get('task_id',None)
        sprint_day = request.args.get('sprint_day',None)
        sprint_hour = request.args.get('sprint_hour',None)
        schedule_tasks = get_schedule_tasks_filtered(sprint_id,task_id,sprint_day,sprint_hour)
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
@login_required
def create_next():
    "Create next sprint (currently assuming 7 day sprints)"
    #TODO: Get user sprint length & start day
    is_json = request.args.get('is_json',False)
    if is_json:
        abort(405,'Method not supported for AJAX mode')
    if request.method == 'POST':
        error = None
        last_sprint = get_last_sprint()
        if last_sprint is None:
            error = f'No sprint found for user. Next sprint can only be created after initial sprint'
        if error is None:
            start_date, end_date = (last_sprint.end_date+timedelta(1), last_sprint.end_date+timedelta(8))
            sprint = create_sprint(start_date,end_date)
            if is_json:
                return json.dumps({'Success':True,'sprint_id':sprint.id})
            return redirect(url_for('sprint.show',sprint_id = sprint.id))
        if is_json:
            abort(500,error)
        flash(error,'error')
    final_sprint = get_last_sprint()
    start_date = date.today() if final_sprint is None else final_sprint.end_date
    end_date = start_date + timedelta(7)
    return render_template('sprint/create.html', start_date = start_date, end_date = end_date)


@bp.route('/create', methods=('GET','POST'))
@login_required
def create():
    "Create a New Sprint (should default to week following last sprint)"
    is_json = request.args.get('is_json',False)
    if is_json and request.method == 'GET':
        abort(405,'Method not supported for AJAX mode')
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        force_create = request.form.get('force_create',None)
        error = None
        start_sprint = get_sprint_by_date(start_date = start_date)
        end_sprint = get_sprint_by_date(end_date = end_date)
        if not start_date:
            error = "Unable to create sprint without a Start Date"
        elif not end_date:
            error = "Unable to create sprint without an End Date"
        elif end_sprint is not None:
            error = f"Sprint Ends same day as Existing Sprint {end_sprint.id}"
        elif start_sprint is not None: 
            error = f"Sprint Starts same day as Existing Sprint {start_sprint.id}"
        elif force_create is False and (
                get_sprint_by_date(middle_date=start_date) is not None or
                get_sprint_by_date(middle_date=end_date) is not None):
            error = "Sprint overlaps existing Sprint"

        if error is None:
            if isinstance(start_date,str):
                start_date = datetime.strptime(start_date,'%Y-%m-%d').date()
            if isinstance(end_date,str):
                end_date = datetime.strptime(end_date,'%Y-%m-%d').date()
            sprint = create_sprint(start_date,end_date)
            if is_json:
                return json.dumps({'Success':True,'sprint_id':sprint.id})
            return redirect(url_for('sprint.show', sprint_id = sprint.id))
        if is_json:
            abort(500,error)
        flash(error,'error')
    final_sprint = get_last_sprint()
    start_date = date.today() if final_sprint is None else final_sprint.end_date
    end_date = start_date + timedelta(7)
    return render_template('sprint/create.html', start_date = start_date, end_date = end_date)


@bp.route('/', methods=('GET',))
@login_required
def list_all():
    "List all Sprints"
    is_json = request.args.get('is_json',False)
    sprints = get_sprints()
    current_sprint = get_current_sprint()
    if not sprints:
        abort(404, "No Sprints Exist Yet: Create your First Sprint " + 
                    url_for('sprint.create'))
    if is_json:
        return json.dumps({'Success':True,
                           'sprints':[dict(x) for x in sprints],
                           'has_current_sprint':current_sprint is not None}) 
    return render_template('sprint/list.html',sprints = sprints)


@bp.route('/<int:sprint_id>', methods=('GET', 'POST'))
@login_required
def show(sprint_id):
    "Show the Details of Sprint sprint_id"
    is_json = request.args.get('is_json',False)
    sprint = get_sprint(sprint_id)
    if not sprint:
        abort(404, f"Sprint with ID {sprint_id} was not found.")
    if request.method == 'POST':
        start_date = request.form.get('start_date',None)
        end_date = request.form.get('end_date',None)
        error = None
        start_sprint = get_sprint_by_date(start_date=start_date)
        end_sprint = get_sprint_by_date(end_date=end_date)
        if not start_date:
            error = "Sprint Requires Start date"
        elif not end_date:
            error = "Sprint Requires End Date"
        elif start_sprint is not None:
            error = f"New start date is shared by sprint {start_sprint.id}"
        elif end_sprint is not None:
            error = f"New end date is shared by sprint {end_sprint.id}"
        if error is None:
            sprint = update_sprint(id, start_date, end_date)
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
@login_required
def active():
    "See the Active Sprint - if two sprints overlap, pick the one with the higher endDate"
    is_json = request.args.get('is_json',False)
    current_sprint = get_current_sprint()
    if not current_sprint:
        return redirect(url_for('sprint.list_all'))

    sprint_id = current_sprint.id    
    if is_json:
         return json.dumps({'Success':True,'sprint_id':sprint_id,'sprint':dict(current_sprint)})
    return get_sprint_board(sprint_id, current_sprint, isStatic=False)