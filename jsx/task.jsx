'use strict;'
import { PropTypes } from 'prop-types'
import React from 'react'
import axios from 'axios'
import app from './app.jsx'

const DeadlineLabel = app.DeadlineLabel
const EditableHandleClick = app.EditableHandleClick

class CreateTask extends React.Component {
  static propTypes = {
    story: PropTypes.number.isRequired,
    addTask: PropTypes.func.isRequired,
    notOpen: PropTypes.func
  }

  constructor (props) {
    super(props)
    this.state = {
      task: '',
      estimate: 0
    }
  }

  async createTask () {
    if (this.state.task === undefined) {
      app.PrettyAlert('Cannot Create Unnamed Task')
      return
    }
    await axios.put(`/task/create/${this.props.story}?is_json=true`, this.state)
      .then((response) => {
        const task = response.data.task
        this.props.addTask(task)
        this.props.notOpen()
      })
  }

  render () {
    return (
      <div id="TaskCreate">
        <label>Task:<input
          type="text"
          placeholder="Task Name"
          aria-describedby="exampleHelpTask"
          onChange={(v) => this.setState({ ...this.state, task: v.target.value })}
          required />
        </label>
        <label htmlFor="estimate">
            Estimate:
            <input type="text"
              name="estimate"
              pattern="\d+\.?\d*"
              placeholder="3.5"
              aria-describedby="exampleHelpEstimate"
              onChange={(v) => {
                const val = v.target.value
                if (!isNaN(Number(val))) {
                  this.setState({ ...this.state, estimate: Number(val) })
                }
              }}
              />
            <span className="form-error">
                Expecting a number. Use partial hours to estimate minutes.<br />
                30m for .5, 15m for .25, etc.
            </span>
        </label>
        <div>
            <button className="button float-left" onClick={() => this.createTask()}>Create</button>
            <button type="button" className="button float-right cancel" onClick={() => this.props.notOpen()}>Cancel</button>
        </div>
      </div>
    )
  }
}

class CreateTaskButton extends React.Component {
  static propTypes = {
    addTask: PropTypes.func.isRequired,
    story: PropTypes.number.isRequired
  }

  constructor (props) {
    super(props)
    this.state = {
      open: false
    }
  }

  notOpen () {
    this.setState({ open: false })
  }

  render () {
    let content = (
      <button
        className="button create create-task"
        onClick={() => { this.setState({ open: true }) }}
      >
        Create Task
      </button>)
    if (this.state.open) {
      content = (<CreateTask story={this.props.story} addTask={(v) => this.props.addTask(v)} notOpen={() => this.notOpen()} />)
    }
    return (
      <div>
        {content}
      </div>
    )
  }
}

class TaskStatusButton extends React.Component {
  static propTypes = {
    status: PropTypes.string,
    update: PropTypes.func
  }

  render () {
    this.status = this.props.status ? this.props.status : 'To-Do'
    return (
      <div
        className={
          'cell small-2 label status ' +
          this.getStatusClass()
        }
        onClick={
          this.props.update
            ? () => {
                this.handleClick()
              }
            : () => {}
        }
      >
        {this.status}
      </div>
    )
  }

  getStatusClass () {
    return this.status.toLowerCase().replaceAll(' ', '-')
  }

  handleClick () {
    const statusList = ['To-Do', 'In Progress', 'Done']
    const status = this.props.status ? this.props.status : 'To-Do'
    const nextStatus =
      status === 'Done'
        ? 'To-Do'
        : statusList[statusList.indexOf(status) + 1]
    this.props.update(nextStatus, () => {})
  }
}

class TaskNameLabel extends React.Component {
  static propTypes = {
    update: PropTypes.func,
    task: PropTypes.string.isRequired,
    sprint: PropTypes.bool
  }

  render () {
    const sizeClass = this.props.sprint ? 'large-5' : 'large-9'
    return (
      <div className={'cell task-name ' + sizeClass}>
        <span
          className={this.props.update ? 'editable' : ''}
          title={this.props.update ? 'Click to Edit' : 'Task Name'}
          onClick={
            this.props.update
              ? (t) => {
                  EditableHandleClick(t, this)
                }
              : () => { return false }
          }
        >
          {this.props.task}
        </span>
      </div>
    )
  }
}

class TaskEstimateLabel extends React.Component {
  static propTypes = {
    update: PropTypes.func,
    estimate: PropTypes.number
  }

  render () {
    return (
      <div className=" cell small-2">
        E:&nbsp;
        <span
          title="Click to Edit Estimate"
          className={'note estimate ' + this.props.update ? 'editable' : ''}
          onClick={
            this.props.update ? (t) => EditableHandleClick(t, this, true) : () => {}
          }
        >
          { this.props.estimate ? this.props.estimate : 'None' }
        </span>
      </div>
    )
  }
}

class TaskRecurringButton extends React.Component {
  static propTypes = {
    update: PropTypes.func,
    recurring: PropTypes.bool.isRequired
  }

  render () {
    return (
      <div
        className={
          'oneOver  cell small-2 label recurring ' +
          (this.props.recurring ? 'recur_color' : '')
        }
        onClick={this.props.update ? () => this.handleClick() : () => {}}
      >
        {this.props.recurring ? 'Recurring' : 'One-Time'}
      </div>
    )
  }

  handleClick () {
    const newRecurring = !this.props.recurring
    this.props.update(newRecurring, () => {})
  }
}

function TaskActualLabel (props) {
  return (
    <div className="cell small-2">
      <span>
        A:&nbsp;{props.actual ? props.actual : 'None'}
      </span>
    </div>
  )
}
TaskActualLabel.propTypes = { actual: PropTypes.number }

function TaskSchedulingButton (props) {
  return (
    <button className="button small"
      onClick={() => props.handleClick()}
    >Schedule Task</button>
  )
}
TaskSchedulingButton.propTypes = { handleClick: PropTypes.func }

class TaskSchedulingWidget extends React.Component {
  static propTypes = {
    deadline: PropTypes.string,
    recurring: PropTypes.bool,
    status: PropTypes.string,
    sprint: PropTypes.number,
    update: PropTypes.func
  }

  render () {
    return (
      <div className="grid-x cell small-5">
        <DeadlineLabel
          deadline={this.props.deadline}
          recurring={this.props.recurring}
          update={(v, c) => this.props.update('deadline', v, c)}
        />
        <span className="float-right">{this.get_status_message()}</span>
      </div>
    )
  }

  get_status_message () {
    const sprintPlanning = this.context.sprintPlanning
    const pageContext = this.context.context
    if (this.props.status === 'Done') {
      return 'Task Complete'
    } else if (pageContext === 'TaskShowcase' && sprintPlanning !== 0 && this.props.update) {
      if (this.props.sprint !== sprintPlanning) {
        return (
          <TaskSchedulingButton
            handleClick={() => this.props.update('sprint_id', sprintPlanning, () => {})}
          />
        )
      } else {
        return 'Task in Sprint'
      }
    } else if (this.props.sprint !== null && this.props.sprint !== undefined) {
      return 'Task In Sprint of ' + this.props.sprint
    } else {
      return 'Task Not in Sprint'
    }
  }
}
TaskSchedulingWidget.contextType = app.contextObject

class TaskContainerShowcase extends React.Component {
  static propTypes = {
    id: PropTypes.number.isRequired,
    task: PropTypes.string.isRequired,
    sprint: PropTypes.number,
    update: PropTypes.func,
    estimate: PropTypes.number,
    status: PropTypes.string,
    actual: PropTypes.number,
    deadline: PropTypes.string,
    recurring: PropTypes.bool
  }

  render () {
    // planningSprint is now a context item of TaskContainerShowcase
    // as well as filterObject
    const filterObject = this.context.filter
    console.log(this.context)
    const isFilteredStatus = filterObject.status[this.props.status]
    const deadline = new Date(this.props.deadline)
    const isFilteredDateStart = filterObject.startDate ? new Date(filterObject.startDate) > deadline : false
    const isFilteredDateEnd = filterObject.endDate ? new Date(filterObject.endDate) < deadline : false
    if (isFilteredStatus || isFilteredDateEnd || isFilteredDateStart) {
      return/// (<div className="container task-container">Task Filtered</div>)
    }
    return (
      <div
        className="container task-container"
      >
        <div className="grid-x task-header">
          <TaskNameLabel
            task={this.props.task}
            update={(v, c) => this.props.update('task', v, c)}
            update_key="task"
          />
          <TaskStatusButton
            status={this.props.status}
            update={(v, c) => this.props.update('status', v, c)}
          />
        </div>
        <div className="grid-x task-work">
          <TaskEstimateLabel
            estimate={this.props.estimate}
            update={(v, c) => this.props.update('estimate', v, c)}
            update_key="estimate"
          />
          <TaskActualLabel actual={this.props.actual} />
          <TaskSchedulingWidget
            status={this.props.status}
            sprint={this.props.sprint}
            deadline={this.props.deadline}
            recurring={this.props.recurring}
            update={(t, v, c) => this.props.update(t, v, c)}
          />
          <TaskRecurringButton
            recurring={this.props.recurring}
            update={(v, c) => this.props.update('recurring', v, c)}
          />
        </div>
      </div>
    )
  }
}
TaskContainerShowcase.contextType = app.contextObject

function TaskWorkLabel (props) {
  return (
    <div className="small-6  cell float-right">
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
      <div className={'cell small-2 epic-label ' + this.props.color}>
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
      <div className="cell small-2 story-label">{this.props.story}</div>
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
        className="cell small-2 label float-right log-work"
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

  constructor (props) {
    super(props)

    this.state = { noteComment: this.props.scheduleNote ? this.props.scheduleNote : 'Schedule-Specific Note' }
  }

  render () {
    return (
      <div title="Click to Edit Note" className="small-8  cell">
        <span
          className="note"
          title="Schedule-specific Note"
          onClick={(t) => this.handleClick(t)}
        >
          {this.state.noteComment}
        </span>
      </div>
    )
  }

  handleClick (t) {
    if (!this.props.update) {
      return
    }
    if (this.state.noteComment === 'Schedule-Specific Note') {
      this.setState({ noteComment: '' })
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
    task: PropTypes.string.isRequired,
    estimate: PropTypes.number,
    update: PropTypes.func,
    click: PropTypes.func,
    deadline: PropTypes.object,
    scheduler: PropTypes.bool
  }

  constructor (props) {
    super(props)
    this.state = {
      status: props.status,
      scheduleWork: props.scheduleWork,
      scheduleNote: props.scheduleNote
    }
  }

  click () {
    this.props.click()
  }

  render () {
    let scheduled
    if (this.props.scheduler && this.props.deadline) {
      scheduled = <div className="col">Due: {this.props.deadline}</div>
    } else if (this.props.scheduler) {
      scheduled = <div className="col">No Due Date</div>
    } else {
      scheduled = (
        <div>
          <TaskWorkLabel scheduleWork={this.state.scheduleWork} />
          <TaskScheduleNote
            scheduleNote={this.state.scheduleNote}
            update={(v, c) => this.handleClick('status_note', v, c)}
          />
          <TaskWorkButton
            scheduleWork={this.state.scheduleWork}
            update={(v, c) => this.handleClick('schedule_work', v, c)}
            />
        </div>)
    }
    return (
      <div className="task-container container" onClick={() => this.click()}>
        <div className="grid-x">
          <TaskEpicLabel epic={this.props.epic} color={this.props.color} />
          <TaskStoryLabel story={this.props.story} />
          <TaskNameLabel task={this.props.task} sprint={true} />
          <TaskStatusButton
            status={this.state.status}
            update={(v, c) => this.handleClick('status', v, c)}
          />
        </div>
        <div className="grid-x">
          <TaskEstimateLabel estimate={this.props.estimate} />
          <TaskScheduleHours scheduleHours={this.props.scheduleHours} />
          {scheduled}
        </div>
      </div>
    )
  }

  handleClick (target, newValue, callback) {
    this.props.update(target, newValue, callback)
  }
}

export {
  TaskContainerShowcase,
  TaskContainerSprint,
  CreateTaskButton
}
