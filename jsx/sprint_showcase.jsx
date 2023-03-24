'use strict'
import React from 'react'
import PropTypes from 'prop-types'
import app from './app.jsx'
import { TaskContainerSprint } from './task.jsx'
import { SchedulerConfirm, SchedulerModal } from './scheduling_modal.jsx'
// import ReactDatePicker from 'react-datepicker'

const GetUpdateURL = app.GetUpdateURL
const AjaxUpdateProperty = app.AjaxUpdateProperty
const AjaxDelete = app.AjaxDelete

function NoTask (props) {
  return (
    <div className="Unscheduled-container container ui-droppable"
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
    date: PropTypes.string.isRequired,
    scheduledHours: PropTypes.number,
    tasks: PropTypes.array,
    schedule: PropTypes.array,
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
    oTasks: PropTypes.array,
    oSchedule: PropTypes.array,
    sprint: PropTypes.object.isRequired
  }

  constructor (props) {
    super(props)
    let isStatic
    if (window.location.pathname === '/sprint/active') {
      isStatic = false
    } else {
      const searchParams = new URLSearchParams(window.location.search)
      isStatic = true
      if (searchParams && searchParams.get('static')) {
        isStatic = searchParams.get('static').toLowerCase() !== 'false'
      }
    }
    this.state = {
      static: isStatic,
      tasks: props.oTasks,
      schedule: props.oSchedule ? props.oSchedule : [],
      schedulerOpen: false,
      schedulerConfirm: false,
      scheduleTaskId: 0,
      scheduleDay: 0,
      scheduleHour: 0,
      schedulingTaskObject: {}
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

  getSprintDayComponents (days, schedule, tasks, caller) {
    let totalScheduled = 0
    const dayComponents = days.map(function (day, dindex) {
      let dayScheduled = 0
      let daySchedule = []
      const dayString = day.toISOString().split('T')[0]
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
          date={dayString}
          scheduledHours={dayScheduled}
          tasks={tasks}
          schedule={daySchedule}
          update={(taskID, schedID, s, v, c) => caller.update(taskID, schedID, s, v, c)}
          openScheduler={(hour) => caller.openScheduler(day, hour)}
          />
      )
    })
    return { dayComponents, totalScheduled }
  }

  render () {
    const days = this.getSprintDates()
    const schedule = this.state.schedule
    const tasks = this.state.tasks
    const caller = this
    const { dayComponents, totalScheduled } = this.getSprintDayComponents(days, schedule, tasks, caller)
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
          task={this.state.schedulingTaskObject}
          update={(plan, callback) => this.scheduleTask(plan, callback)}
          close={() => this.setState({ ...this.state, schedulerConfirm: false })}/>
        <SprintLabel scheduledHours={totalScheduled} />
        {dayComponents}
      </div>
    )
  }

  unschedule (callback) {
    if (this.state.static) {
      return
    }
    const day = this.state.scheduleDay
    const hour = this.state.scheduleHour
    const parentObject = this
    if (!(this.state.schedulerOpen && day && hour)) {
      console.error('Erorr: Cannot unschedule task: no schedule element selected')
      return
    }
    console.dir(day)
    console.dir(hour)
    console.dir(this.state.schedule)
    const scheduleItem = this.state.schedule.filter((sched) => { return (sched.sprint_day === day && sched.sprint_hour === hour) })[0]
    if (scheduleItem === undefined) {
      console.error(`Error: cannot find schedule item with day ${day} and hour slot ${hour}`)
      return
    }
    AjaxDelete(GetUpdateURL('sprint/schedule', this.props.sprint.id),
      {
        schedule_id: scheduleItem.id
      }, (resp) => {
        if (!Object.prototype.hasOwnProperty.call(resp.data, 'Success') || !resp.data.Success) {
          console.error('Error: Update request failed')
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
    if (this.state.static) {
      return
    }
    if (this.state.schedulerOpen) {
      return
    }
    const schedDay = day.toISOString().split('T')[0]
    this.setState({
      ...this.state,
      schedulerOpen: true,
      scheduleDay: schedDay,
      scheduleHour: hour
    })
  }

  confirmSchedule (taskId, callback) {
    if (this.state.static) {
      return
    }
    const schedulingTaskObject = this.state.tasks.filter((t) => t.id === taskId)[0]
    if (schedulingTaskObject === undefined) {
      throw Error('Tried to schedule task with invalid ID')
    }
    this.setState({
      ...this.state,
      schedulerOpen: false,
      schedulerConfirm: true,
      scheduleTaskId: taskId,
      schedulingTaskObject
    })
    callback()
  }

  scheduleTask (plan, callback) {
    if (this.state.static) {
      return
    }
    // TODO - see if schedule exists for sprint at day/hour & reschedule
    // ? would it make sense to migrate from a scheduleID to a day/hour lookup?
    this.setState({
      ...this.state,
      schedulerConfirm: false
    })
    const parentObject = this
    AjaxUpdateProperty(GetUpdateURL('sprint/schedule', this.props.sprint.id),
      {
        task_id: parentObject.state.scheduleTaskId,
        sprint_day: parentObject.state.scheduleDay,
        sprint_hour: parentObject.state.scheduleHour,
        schedule_time: plan
      },
      (resp) => {
        const oldSchedule = parentObject.state.schedule ? parentObject.state.schedule : []
        const newSchedule = [...oldSchedule]
        if (!Object.prototype.hasOwnProperty.call(resp.data, 'Success') || !resp.data.Success) {
          console.error('Error: Request to update schedule failed')
          console.dir(resp)
          return
        }
        newSchedule.push({
          sprint_day: parentObject.state.scheduleDay,
          sprint_hour: parentObject.state.scheduleHour,
          schedule_time: Number(plan),
          task_id: parentObject.state.scheduleTaskId,
          work: 0,
          note: '',
          id: resp.data.schedule_task.id
        })

        parentObject.setState({ ...this.state, schedule: newSchedule })
      }, callback)
  }

  update (taskId, scheduleId, stateItem, newValue, callback) {
    if (this.state.static) {
      return
    }
    let updateType, updateID
    let newState = { ...this.state }
    const updateValue = {}
    updateValue[stateItem] = newValue
    // If the item being changed includes "schedule" then it's a schedule object, otherwise task
    if (stateItem.includes('schedule')) {
      updateType = 'sprint/schedule'
      updateValue.schedule_id = scheduleId
      updateID = this.props.sprint.id
      let schedule = this.state.schedule
      schedule = schedule.filter((d) => { return d.schedule.id === scheduleId })[0][stateItem] = newValue
      newState = { ...newState, schedule }
    } else {
      updateType = 'task'
      updateID = taskId
      let tasks = this.state.tasks
      tasks = tasks.filter((t) => { return t.id === taskId })[0][stateItem] = newValue
      newState = { ...newState, tasks }
    }
    AjaxUpdateProperty(GetUpdateURL(updateType, updateID), updateValue, () => {
      this.setState(newState)
      callback()
    })
  }
}

export default { SprintShowcase }
