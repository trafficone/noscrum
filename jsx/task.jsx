'use strict;'
import { PropTypes } from 'prop-types'
import React from 'react'
import app from './app.jsx'

const DeadlineLabel = app.DeadlineLabel
const EditableHandleClick = app.EditableHandleClick

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
          'columns small-2 label status ' +
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
    task: PropTypes.string.isRequired
  }

  render () {
    return (
      <div className="columns large-6 task-name">
        <span
          className={this.props.update ? 'editable' : ''}
          title={this.props.update ? 'Click to Edit' : 'Task Name'}
          update_key="task"
          onClick={
            this.props.update
              ? (t) => {
                  EditableHandleClick(t, this)
                }
              : () => {}
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
      <div className="columns small-2">
        E:&nbsp;
        <span
          title="Click to Edit Estimate"
          className={'note estimate ' + this.props.update ? 'editable' : ''}
          onClick={
            this.props.update ? (t) => EditableHandleClick(t, this) : () => {}
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
          'oneOver columns small-2 label recurring ' +
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
    <div className="columns small-2">
      <span className="float-right">
        A:&nbsp;{props.actual ? props.actual : 'None'}
      </span>
    </div>
  )
}
TaskActualLabel.propTypes = { actual: PropTypes.number }

function TaskSchedulingButton (props) {
  return (
    <button className="button"
      onClick={() => props.handleClick('schedule')}
    >Schedule Task</button>
  )
}
TaskSchedulingButton.propTypes = { handleClick: PropTypes.func }

class TaskSchedulingWidget extends React.Component {
  static propTypes = {
    deadline: PropTypes.string,
    recurring: PropTypes.bool,
    status: PropTypes.string,
    sprint: PropTypes.object,
    handleClick: PropTypes.func,
    update: PropTypes.func
  }

  render () {
    return (
      <div className="columns large-6">
        <DeadlineLabel
          deadline={this.props.deadline}
          recurring={this.props.recurring}
          update={(v, c) => this.props.update('deadline', v, c)}
        />
        <button className="float-right button sprintPlan hidden">
          Plan Task
        </button>
        <span className="float-right">{this.get_status_message()}</span>
      </div>
    )
  }

  get_status_message () {
    if (this.props.status === 'Done') {
      return 'Task Complete'
    } else if (this.props.sprint === 'scheduling') {
      return (
        <TaskSchedulingButton handleClick={this.props.handleClick('schedule')}
        />
      )
    } else if (this.props.sprint !== null && this.props.sprint !== undefined) {
      return 'Task In Sprint of ' + this.props.sprint
    } else {
      return 'Task Not in Sprint'
    }
  }
}

class TaskContainerShowcase extends React.Component {
  static propTypes = {
    id: PropTypes.number.isRequired,
    task: PropTypes.string.isRequired,
    update: PropTypes.func,
    estimate: PropTypes.number,
    status: PropTypes.string,
    actual: PropTypes.number,
    deadline: PropTypes.string,
    recurring: PropTypes.bool,
    sprint: PropTypes.object
  }

  render () {
    return (
      <div
        className="container task-container"
        task={this.props.id}
      >
        <div className="row task-header">
          <TaskNameLabel
            task={this.props.task}
            update={(v, c) => this.props.update('task', v, c)}
            update_key="task"
          />
          <div className="columns small-4"></div>
          <TaskStatusButton
            status={this.props.status}
            update={(v, c) => this.props.update('status', v, c)}
          />
        </div>
        <div className="row task-work">
          <TaskEstimateLabel
            estimate={this.props.estimate}
            update={(v, c) => this.props.update('estimate', v, c)}
            update_key="estimate"
          />
          <TaskActualLabel actual={this.props.actual} />
          <TaskSchedulingWidget
            sprint={this.props.sprint}
            status={this.props.status}
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

export default {
  TaskContainerShowcase
}
