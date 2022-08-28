'use strict;'
import { PropTypes } from 'prop-types'
import React from 'react'
import app from './app.jsx'
import TaskContainerShowcase from './task.jsx'

const EditableHandleClick = app.EditableHandleClick
const DeadlineLabel = app.DeadlineLabel
const CreateElementClick = app.CreateElementClick

class StoryNameLabel extends React.Component {
  static propTypes = {
    update: PropTypes.func,
    story: PropTypes.string.isRequired
  }

  render () {
    return (
      <h5
        className={this.props.update ? 'editable' : ''}
        title={this.props.update ? 'Click to Edit Story' : 'Story Name'}
        onClick={
          this.props.update ? (t) => EditableHandleClick(t, this) : () => {}
        }
      >
        {this.props.story}
      </h5>
    )
  }
}

class StoryPriorityLabel extends React.Component {
  static propTypes = {
    update: PropTypes.func,
    prioritization: PropTypes.number
  }

  render () {
    return (
      <div className="float-left">
        <span
          className={'badge priority_' + this.props.prioritization}
          title={
            this.props.update ? 'Click to Edit Priority' : 'Prioritization'
          }
          onClick={() => {}} // TODO: Implement Priority Label Editing
        >
          {this.props.prioritization}
        </span>
      </div>
    )
  }
}

class StoryArchiveButton extends React.Component {
  static propTypes = {
    archive: PropTypes.bool,
    update: PropTypes.func
  }

  render () {
    return (
      <button
        className="button close-story"
        onClick={() => this.handleArchive()}
      >
        {this.props.archive ? 'Reopen' : 'Archive'} Story
      </button>
    )
  }

  handleArchive () {
    // TODO: Handle Archive
  }
}

class StoryEstimateLabel extends React.Component {
  static propTypes = {
    estimate: PropTypes.number
  }

  render () {
    return (
      <div>
        Hrs Estimated:
        <span className="story-metric estimate">{this.props.estimate}</span>
      </div>
    )
  }
}

function StoryIncompleteLabel (props) {
  return (
    <div>
      Tasks to Finish:
      <span className="story-metric estimate">{props.incomplete}</span>
    </div>
  )
}
StoryIncompleteLabel.propTypes = { incomplete: PropTypes.number }

class StorySummaryContainer extends React.Component {
  static propTypes = {
    estimate: PropTypes.number,
    incomplete: PropTypes.number,
    deadline: PropTypes.string,
    update: PropTypes.func,
    archive: PropTypes.bool
  }

  render () {
    return (
      <div className="small-2 columns story-label">
        <StoryEstimateLabel estimate={this.props.estimate} />
        <StoryIncompleteLabel incomplete={this.props.incomplete} />
        <DeadlineLabel
          deadline={this.props.deadline}
          update={(v, c) => this.props.update('deadline', v, c)}
        />
        <StoryArchiveButton update={this.props.update} />
      </div>
    )
  }
}
class StoryTasksContainer extends React.Component {
  static propTypes = {
    tasks: PropTypes.array,
    update: PropTypes.func
  }

  render () {
    const tasks = this.props.tasks
    const taskContainers = tasks.map((task) => (
      <TaskContainerShowcase
        key={task.id}
        id={task.id}
        status={task.status}
        task={task.task}
        estimate={task.estimate}
        deadline={task.deadline}
        recurring={task.recurring}
        sprint={task.sprint}
        update={(s, v, c) => this.props.update(task.id, s, v, c)}
      />
    ))
    return <div className="containers">{taskContainers}</div>
  }
}

class StoryCreateTaskButton extends React.Component {
  static propTypes = {
    new_task_url: PropTypes.string.isRequired
  }

  render () {
    return (
      <div>
      <button
        className="button create"
        onClick={(t) => CreateElementClick(t, this.props.new_task_url)}
      >
        Create Task
      </button>
      </div>
    )
  }
}
class StoryContainerTShowcase extends React.Component {
  static propTypes = {
    id: PropTypes.number.isRequired,
    story: PropTypes.string.isRequired,
    prioritization: PropTypes.number,
    deadline: PropTypes.string,
    tasks: PropTypes.array,
    update: PropTypes.func,
    updateTask: PropTypes.func
  }

  render () {
    const tasks = this.props.tasks
    const totalEstimate = tasks.reduce((acc, task) => {
      return acc + Number(task.estimate ? task.estimate : 0)
    }, 0)
    const incompleteTasks = tasks.reduce((acc, task) => {
      return acc + Number(task.satuts === 'Done' ? 0 : 1)
    }, 0)
    return (
      <div>
      <div className="row story">
          <StoryPriorityLabel
            prioritization={this.props.prioritization}
            update={(v, c) => this.props.update('prioritization', v, c)}
          />
          <StoryNameLabel
            story={this.props.story}
            update={(v, c) => this.props.update('story', v, c)}
          />
        </div>
        <div className="row summary-story">
          <StorySummaryContainer
            estimate={totalEstimate}
            incomplete={incompleteTasks}
            deadline={this.props.deadline}
            update={(v, c) => this.props.update('deadline', v, c)}
            archive={true}
          />

          <div className="columns large-10">
          <StoryTasksContainer tasks={tasks} update={(t, s, v, c) => this.props.updateTask(t, s, v, c)}/>
          <StoryCreateTaskButton new_task_url={'/tasks/create/' + this.props.id + '?is_asc=true'} />
          </div>
        </div>
      </div>
    )
  }
}

export default {
  StoryContainerTShowcase
}
