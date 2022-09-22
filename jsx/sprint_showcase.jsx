'use strict'
import React from 'react'
import PropTypes from 'prop-types'
import app from './app.jsx'
import { TaskContainerSprint } from './task.jsx'

const GetUpdateURL = app.GetUpdateURL
const AjaxUpdateProperty = app.AjaxUpdateProperty

class SprintDayLabel extends React.Component {
  static propTypes = {
    date: PropTypes.string,
    scheduledHours: PropTypes.number
  }

  render () {
    return (
      <span>
      {this.props.date};
      <em>{this.props.scheduledHours} Hours Scheduled for Day</em>
      </span>
    )
  }
}

function NoTask () {
  return (
    <div className="Unscheduled-container container scheduled ui-droppable">
      <div>No Task Scheduled - click to schedule</div>
      <div>&nbsp;</div>
    </div>
  )
}

class SprintDayContainer extends React.Component {
  static propTypes = {
    date: PropTypes.string.isRequired,
    scheduledHours: PropTypes.number,
    tasks: PropTypes.object,
    schedule: PropTypes.object,
    update: PropTypes.func
  }

  render () {
    const tasks = this.props.tasks
    const schedule = this.props.schedule
    let scheduledHours = 0
    const taskObjects = schedule.map((sched) => {
      const task = tasks.filter((t) => t.id === sched.taskId)[0]
      scheduledHours += sched.hours ? sched.hours : 0
      return (
        <TaskContainerSprint
          key={sched.id}
          status={task.status}
          scheduleWork={sched.work}
          scheduleNote={sched.note}
          epic={task.epic}
          story={task.story}
          color={task.color}
          task={task.task}
          estimate={task.estimate}
          update={(s, v, c) => this.props.update(task.id, sched.id, s, v, c)}
          />
      )
    })

    return (
      <div className={'day ' + this.getDayColor(this.props.date)}>
        <SprintDayLabel date={this.props.date} scheduledHours={scheduledHours} />
        {taskObjects}
        <NoTask />
      </div>
    )
  }

  getDayColor (dateString) {
    return 'yellow' // TODO: Fix Day Color Calculator
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
    oSchedule: PropTypes.object
  }

  constructor (props) {
    super(props)
    this.state = {
      tasks: props.oTasks,
      schedule: props.oSchedule ? props.oSchedule : []
    }
  }

  render () {
    const days = this.state.schedule
    const tasks = this.state.tasks
    let totalScheduled = 0
    const dayComponents = days.map((day) => {
      let dayScheduled = 0
      const dayTaskIDs = day.schedule.map((s) => {
        dayScheduled += s.hours ? s.hours : 0
        totalScheduled += s.hours ? s.hours : 0
        return s.taskId
      })
      const dayTasks = tasks.filter((task) => { return dayTaskIDs.includes(task.id) })
      return (
        <SprintDayContainer
          key={day.date}
          date={day.date}
          scheduledHours={dayScheduled}
          tasks={dayTasks}
          schedule={day.schedule}
          update={(taskID, schedID, s, v, c) => this.update(taskID, schedID, s, v, c)} />
      )
    })
    return (
      <div>
        <SprintLabel scheduledHours={totalScheduled} />
        {dayComponents}
      </div>
    )
  }

  update (taskId, scheduleId, stateItem, newValue, callback) {
    let updateType, updateID, newState
    const updateValue = {}
    updateValue[stateItem] = newValue
    if (stateItem.includes('schedule')) {
      updateType = 'sprint/schedule'
      updateID = scheduleId
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
