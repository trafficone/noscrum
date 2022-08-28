'use strict'
import React from 'react'
import PropTypes from 'prop-types'
import { $ } from 'jquery'
import { EditableHandleClick, AjaxUpdateProperty, TaskNameLabel, TaskStatusButton, TaskEstimateLabel, GetUpdateURL } from './app.jsx'

function TaskWorkLabel (props) {
  return (
    <div className="small-6 columns float-right">
      Worked This Day:
      <span className="hours-worked">
        {props.scheduleWork ? props.scheduleWork : 0}
      </span>
    </div>
  )
}
TaskWorkLabel.propTypes = {
  scheduleWork: PropTypes.number
}

class TaskEpicLabel extends React.Component {
  static propTypes = {
    color: PropTypes.string.isRequired,
    epic: PropTypes.string.isRequired
  }

  render () {
    return (
      <div className={'columns small-2 epic-label ' + this.props.color}>
        {this.props.epic}
      </div>
    )
  }
}

class TaskStoryLabel extends React.Component {
  static propTypes = {
    story: PropTypes.string.isRequired
  }

  render () {
    return (
      <div className="columns small-2 story-label">{this.props.story}</div>
    )
  }
}

class TaskWorkButton extends React.Component {
  static propTypes = {
    scheduleWork: PropTypes.number,
    update: PropTypes.func.isRequired
  }

  render () {
    return (
      <div
        title="Click to Log Work"
        className="columns small-2 label float-right log-work"
        onClick={(t) => this.handleClick(t)}
      >
        Log Work
      </div>
    )
  }

  handleClick (t) {
    // TODO: Handle Work Logging Modal
    console.log('Work Log for T:' + t)
    const newWorkVal = this.props.scheduleWork
      ? this.props.scheduleWork + 2
      : 2
    this.props.update(newWorkVal, () => {
      console.log('You worked 2 hours & closed modal')
    })
  }
}

class TaskScheduleNote extends React.Component {
  static propTypes = {
    scheduleNote: PropTypes.string,
    update: PropTypes.func
  }

  render () {
    return (
      <div title="Click to Edit Note" className="small-8 columns">
        <span
          className="note"
          title="Schedule-specific Note"
          onClick={this.props.update ? (t) => this.handleClick(t) : () => {}}
        >
          {this.props.scheduleNote
            ? this.props.scheduleNote
            : 'Schedule-Specific Note'}
        </span>
      </div>
    )
  }

  handleClick (t) {
    if ($(t.target).text() === 'Schedule-Specific Note') {
      $(t.target).text('')
    }
    EditableHandleClick(t, this)
  }
}
class TaskScheduleHours extends React.Component {
  static propTypes = {
    scheduleHours: PropTypes.number
  }

  render () {
    return (
      <span>
        Scheduled: {this.props.scheduleHours}
      </span>
    )
  }
}

class TaskContainerSprint extends React.Component {
  static propTypes = {
    status: PropTypes.string,
    scheduleWork: PropTypes.number,
    scheduleNote: PropTypes.string,
    scheduleHours: PropTypes.number,
    epic: PropTypes.string,
    story: PropTypes.string,
    color: PropTypes.string,
    task: PropTypes.string,
    estimate: PropTypes.number,
    update: PropTypes.func
  }

  constructor (props) {
    super(props)
    this.state = {
      status: props.status,
      scheduleWork: props.scheduleWork,
      scheduleNote: props.scheduleNote
    }
  }

  render () {
    return (
      <div className="task-container container">
        <div className="row">
          <TaskEpicLabel epic={this.props.epic} color={this.props.color} />
          <TaskStoryLabel story={this.props.story} />
          <TaskNameLabel task={this.props.task} />
          <TaskStatusButton
            status={this.state.status}
            update={(v, c) => this.handleClick('status', v, c)}
          />
        </div>
        <div className="row">
          <TaskEstimateLabel estimate={this.props.estimate} />
          <TaskScheduleHours scheduleHours={this.props.scheduleHours} />
          <TaskWorkLabel scheduleWork={this.state.scheduleWork} />
          <TaskScheduleNote
            scheduleNote={this.state.scheduleNote}
            update={(v, c) => this.handleClick('status_note', v, c)}
          />
          <TaskWorkButton
            scheduleWork={this.state.scheduleWork}
            update={(v, c) => this.handleClick('schedule_work', v, c)}
          />
        </div>
      </div>
    )
  }

  handleClick (target, newValue, callback) {
    this.props.update(target, newValue, callback)
  }
}

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
      schedule: props.oSchedule
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
