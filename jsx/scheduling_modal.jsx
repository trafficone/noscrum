import PropTypes from 'prop-types'
import ReactModal from 'react-modal'
import React from 'react'
import { TaskContainerSprint } from './task.jsx'

class SchedulerModal extends React.Component {
  static propTypes = {
    tasks: PropTypes.array.isRequired,
    schedule: PropTypes.array,
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
                // console.log('Unschedule Clicked')
                this.props.unschedule()
              }}
              data-close="">Unschedule Task</button>
      <button className="button" id="unplanned-task" title="Create or Add Task to Sprint" data-open="UnplannedTask">Add Unplanned Task</button>
      <ul className="tabs" data-tabs="" id="task-tabs">
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
      <button className="close-button" data-close="" aria-label="Close" onClick={() => this.props.close()} > <span aria-hidden="true">&times;</span></button>
      </div>
    </ReactModal>
    )
  }
}

class PlanTaskForm extends React.Component {
  static propTypes = {
    tasks: PropTypes.array.isRequired,
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
            click={() => this.props.update(t.id, () => { console.log('Scheduling ' + t.id) })}
           />
        )
      })
    if (tasksFiltered === []) {
      return (
        <div>
          <span>No {this.props.recurring ? 'Recurring' : ''} Tasks in sprint.</span>
        </div>
      )
    }

    return (
      <div>
        {tasksFiltered}
      </div>
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
    if (task === {} || task === undefined) {
      return
    }
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

export {
  SchedulerModal,
  SchedulerConfirm
}
