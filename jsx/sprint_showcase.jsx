'use strict'
import React from 'react'
import ReactModal from 'react-modal'
import PropTypes from 'prop-types'
import app from './app.jsx'
import { TaskContainerSprint } from './task.jsx'
// import ReactDatePicker from 'react-datepicker'

const GetUpdateURL = app.GetUpdateURL
const AjaxUpdateProperty = app.AjaxUpdateProperty
const AjaxDelete = app.AjaxDelete

class SchedulerModal extends React.Component {
  static propTypes = {
    tasks: PropTypes.object.isRequired,
    schedule: PropTypes.object,
    update: PropTypes.func,
    unschedule: PropTypes.func,
    open: PropTypes.bool,
    close: PropTypes.func
  }

  constructor (props) {
    super(props)
    this.state = {
      recurring: false
    }
  }

  render () {
    return (
    <ReactModal isOpen={this.props.open}
      style={{
        content: {
          width: '50%',
          minwidth: '20em'
        }
      }}>
      <button className="button"
              id="unschedule-task"
              title="Unschedule Task Clicked (if any)"
              onClick={() => {
                console.log('Unschedule Clicked')
                this.props.unschedule()
              }}
              data-close>Unschedule Task</button>
      <button className="button" id="unplanned-task" title="Create or Add Task to Sprint" data-open="UnplannedTask">Add Unplanned Task</button>
      <ul className="tabs" data-tabs id="task-tabs">
        <li className="tabs-title is-active">
          <button aria-selected="true" className="button" onClick={() => this.setState({ ...this.state, recurring: false })}>Planned Tasks</button>
        </li>
        <li className="tabs-title">
          <button className="button" onClick={() => this.setState({ ...this.state, recurring: true })}>Recurring Tasks</button>
        </li>
      </ul>
      <div className="tabs-content" data-tabs-content="task-tabs">
      <div className="tabs-panel is-active">
        <PlanTaskForm
          tasks={this.props.tasks}
          update={(taskId, callback) => this.props.update(taskId, callback)}
          recurring={this.state.recurring}/>
      </div>
      <button className="close-button" data-close aria-label="Close" onClick={() => this.props.close()} > <span aria-hidden="true">&times;</span></button>
      </div>
    </ReactModal>
    )
  }
}

class SchedulerConfirm extends React.Component {
  static propTypes = {
    open: PropTypes.bool,
    close: PropTypes.func,
    task: PropTypes.object,
    update: PropTypes.func
  }

  constructor (props) {
    super(props)
    this.state = {
      inputValue: ''
    }
  }

  render () {
    const task = this.props.task
    return (
      <ReactModal isOpen={this.props.open}
        style={{
          content: {
            width: '50%',
            minwidth: '20em'
          }
        }}>
          <TaskContainerSprint
            key={task.id}
            task={task.task}
            estimate={task.estimate}
            status={task.status}
            epic={'epic not found'}
            story={'story not found'}
            scheduleHours={0}
            deadline={task.deadline}
            scheduler={true}
           />
           <label>Hours Planned
           <input type="text" value={this.state.inputValue} onChange={evt => this.updateInputValue(evt)}/>
           </label>
           <button className="button" onClick={() => this.props.update(this.state.inputValue)}>Plan</button>

      <button className="close-button" data-close aria-label="Close" onClick={() => this.props.close()} > <span aria-hidden="true">&times;</span></button>
      </ReactModal>
    )
  }

  updateInputValue (event) {
    this.setState({ ...this.state, inputValue: event.target.value })
  }
}

class PlanTaskForm extends React.Component {
  static propTypes = {
    tasks: PropTypes.object.isRequired,
    update: PropTypes.func,
    recurring: PropTypes.bool
  }

  render () {
    const tasksFiltered = this
      .props
      .tasks
      .filter((t) => { return t.recurring === this.props.recurring })
      .map((t) => {
        return (
          <TaskContainerSprint
            key={t.id}
            task={t.task}
            estimate={t.estimate}
            status={t.status}
            epic={'epic not found'}
            story={'story not found'}
            scheduleHours={0}
            deadline={t.deadline}
            scheduler={true}
            click={() => this.props.update(t.id, () => {})}
           />
        )
      })

    return (
      <div>
        {tasksFiltered}

      </div>
    )
  }
}

function NoTask (props) {
  return (
    <div className="Unscheduled-container container scheduled ui-droppable"
      onClick={props.click}>
      <div>No Task Scheduled - click to schedule</div>
      <div>&nbsp;</div>
    </div>
  )
}
NoTask.propTypes = {
  click: PropTypes.func
}

class SprintDayContainer extends React.Component {
  static propTypes = {
    ikey: PropTypes.number.isRequired,
    date: PropTypes.object.isRequired,
    scheduledHours: PropTypes.number,
    tasks: PropTypes.object,
    schedule: PropTypes.object,
    update: PropTypes.func,
    openScheduler: PropTypes.func
  }

  render () {
    const tasks = this.props.tasks
    const schedule = this.props.schedule
    const openScheduler = this.props.openScheduler
    const updateSched = this.props.update
    const key = this.props.ikey
    let scheduledHours = 0
    let maxHours = 1
    const taskObjects = schedule.map(function (sched) {
      const task = tasks.filter((t) => t.id === sched.task_id)[0]
      scheduledHours += sched.schedule_time ? sched.schedule_time : 0
      maxHours = sched.sprint_hour + 1 > maxHours ? sched.sprint_hour + 1 : maxHours
      if (task === undefined) {
        return <NoTask click={() => this.props.openScheduler(sched.sprint_hour)} />
      }
      return (
        <TaskContainerSprint
          key={sched.id}
          status={task.status}
          scheduleWork={sched.work}
          scheduleNote={sched.note}
          scheduleHours={Number(sched.schedule_time)}
          epic={task.epic}
          story={task.story}
          color={task.color}
          task={task.task}
          estimate={task.estimate}
          update={(s, v, c) => updateSched(task.id, sched.id, s, v, c)}
          click={() => openScheduler(sched.sprint_hour)}
          />
      )
    })

    return (
      <div className={'day ' + (key % 2 === 0 ? 'green' : 'yellow')}>
        <span>
        {this.props.date} <em>{scheduledHours} Hours Scheduled for Day</em>
        </span>
        {taskObjects}
        <NoTask click={() => this.props.openScheduler(maxHours)}/>
      </div>
    )
  }
}

class SprintLabel extends React.Component {
  static propTypes = {
    totalHours: PropTypes.number
  }

  render () {
    return (
      <span>Total Hours Scheduled for Sprint {this.props.totalHours}</span>
    )
  }
}

class SprintShowcase extends React.Component {
  static propTypes = {
    oTasks: PropTypes.object,
    oSchedule: PropTypes.object,
    sprint: PropTypes.object.isRequired
  }

  constructor (props) {
    super(props)
    this.state = {
      tasks: props.oTasks,
      schedule: props.oSchedule ? props.oSchedule : [],
      schedulerOpen: false,
      schedulerConfirm: false,
      scheduleTask: 0,
      scheduleDay: 0,
      scheduleHour: 0
    }
  }

  getSprintDates () {
    const dates = []
    const current = new Date(this.props.sprint.start_date)
    const end = new Date(this.props.sprint.end_date)
    // eslint-disable-next-line no-unmodified-loop-condition
    while (current <= end) {
      dates.push(new Date(current))
      current.setTime(current.getTime() + (3600 * 24 * 1000))
    }
    return dates
  }

  render () {
    const days = this.getSprintDates()
    const schedule = this.state.schedule
    // console.log('Schedule')
    // console.dir(schedule)
    const tasks = this.state.tasks
    const caller = this
    let totalScheduled = 0
    const dayComponents = days.map(function (day, dindex) {
      let dayScheduled = 0
      // let dayTasks = []
      let daySchedule = []
      const dayString = day.toLocaleDateString('ja-JP').replaceAll('/', '-')
      if (schedule !== undefined) {
        daySchedule = schedule.filter((sched) => { return sched.sprint_day === dayString })
        daySchedule = daySchedule
          .map(function (s) {
            dayScheduled += s.hours ? s.hours : 0
            totalScheduled += s.hours ? s.hours : 0
            return s // FIXME: I'm leaving a note here:
            // The full schedule object needs to be passed to the day
            // But I think it's ok to also send all tasks to all day containers
          })
        // dayTasks = tasks.filter((task) => { return daySchedule.includes(task.id) })
      }
      return (
        <SprintDayContainer
          key={dindex}
          ikey={dindex}
          date={`${day.getFullYear()}-${day.getMonth() + 1}-${day.getDate()}`}
          scheduledHours={dayScheduled}
          tasks={tasks}
          schedule={daySchedule}
          update={(taskID, schedID, s, v, c) => caller.update(taskID, schedID, s, v, c)}
          openScheduler={(hour) => caller.openScheduler(day, hour)}
          />
      )
    })
    return (
      <div>
        <SchedulerModal
          open={this.state.schedulerOpen}
          schedule={this.state.schedule}
          tasks={this.state.tasks}
          update={(taskId, callback) => this.confirmSchedule(taskId, callback)}
          unschedule={() => this.unschedule(this.setState({ ...this.state, schedulerOpen: false }))}
          close={() => this.setState({ ...this.state, schedulerOpen: false })}/>
        <SchedulerConfirm
          open={this.state.schedulerConfirm}
          task={this.state.scheduleTask}
          update={(plan, callback) => this.scheduleTask(plan, callback)}
          close={() => this.setState({ ...this.state, schedulerConfirm: false })}/>
        <SprintLabel scheduledHours={totalScheduled} />
        {dayComponents}
      </div>
    )
  }

  unschedule (callback) {
    const day = this.state.scheduleDay
    const hour = this.state.scheduleHour
    const parentObject = this
    if (!(this.state.schedulerOpen && day && hour)) {
      console.log('Cannot unschedule task: no schedule element selected')
      return
    }
    console.dir(day)
    console.dir(hour)
    console.dir(this.state.schedule)
    const scheduleItem = this.state.schedule.filter((sched) => { return (sched.sprint_day === day && sched.sprint_hour === hour) })[0]
    if (scheduleItem === undefined) {
      console.log(`cannot find schedule item with day ${day} and hour slot ${hour}`)
      return
    }
    AjaxDelete(GetUpdateURL('sprint/schedule', this.props.sprint.id),
      {
        schedule_id: scheduleItem.id
      }, (resp) => {
        if (!Object.prototype.hasOwnProperty.call(resp.data, 'Success') || !resp.data.Success) {
          console.log('Request failed')
          console.dir(resp)
          return
        }
        const newSchedule = parentObject.state.schedule.filter((sched) => sched.id !== scheduleItem.id)
        parentObject.setState({ ...parentObject.state, schedule: newSchedule })
        if (callback) {
          callback(resp)
        }
      }
    )
  }

  openScheduler (day, hour) {
    if (this.state.schedulerOpen) {
      return
    }
    day = day.toLocaleString('ja-JP').replaceAll('/', '-').substring(0, 10)
    this.setState({
      ...this.state,
      schedulerOpen: true,
      scheduleDay: day,
      scheduleHour: hour
    })
  }

  confirmSchedule (taskId, callback) {
    this.setState({
      ...this.state,
      schedulerOpen: false,
      schedulerConfirm: true,
      scheduleTask: this.state.tasks.filter((t) => { return t.id === taskId })[0]
    })
    callback()
  }

  scheduleTask (plan, callback) {
    // TODO - see if schedule exists for sprint at day/hour & reschedule
    // ? would it make sense to migrate from a scheduleID to a day/hour lookup?
    this.setState({
      ...this.state,
      schedulerConfirm: false
    })
    const parentObject = this
    AjaxUpdateProperty(GetUpdateURL('sprint/schedule', this.props.sprint.id),
      {
        task_id: parentObject.state.scheduleTask.id,
        sprint_day: parentObject.state.scheduleDay,
        sprint_hour: parentObject.state.scheduleHour,
        schedule_time: plan
      },
      (resp) => {
        const oldSchedule = parentObject.state.schedule ? parentObject.state.schedule : []
        const newSchedule = [...oldSchedule]
        if (!Object.prototype.hasOwnProperty.call(resp.data, 'Success') || !resp.data.Success) {
          console.log('Request failed')
          console.dir(resp)
          return
        }
        newSchedule.push({
          sprint_day: parentObject.state.scheduleDay,
          sprint_hour: parentObject.state.scheduleHour,
          schedule_time: Number(plan),
          task_id: parentObject.state.scheduleTask.id,
          work: 0,
          note: '',
          id: resp.data.schedule_task.id
        })

        parentObject.setState({ ...this.state, schedule: newSchedule })
      }, callback)
  }

  update (taskId, scheduleId, stateItem, newValue, callback) {
    let updateType, updateID, newState
    const updateValue = {}
    updateValue[stateItem] = newValue
    // If the item being changed includes "schedule" then it's a schedule object, otherwise task
    if (stateItem.includes('schedule')) {
      updateType = 'sprint/schedule'
      updateValue.schedule_id = scheduleId
      updateID = this.props.sprint.id
      newState = { schedule: this.state.schedule }
      newState.filter((d) => { return d.schedule.id === scheduleId })[0][stateItem] = newValue
    } else {
      updateType = 'task'
      updateID = taskId
      newState = { tasks: this.state.tasks }
      newState.filter((t) => { return t.id === taskId })[0][stateItem] = newValue
    }
    AjaxUpdateProperty(GetUpdateURL(updateType, updateID), updateValue, () => {
      this.setState(newState)
      callback()
    })
  }
}

export default { SprintShowcase }
